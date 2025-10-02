import traci
import time
from datetime import datetime
from prettytable import PrettyTable
import multiprocessing
import os
import psutil
import pandas as pd
import threading


class SimulationTimer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.interval_records = []

    def start(self):
        self.start_time = datetime.now()

    def record_interval(self, action_name=""):
        self.interval_records.append((action_name, datetime.now()))

    def stop(self):
        self.end_time = datetime.now()

    def get_duration(self):
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def print_statistics(self):
        print("\n=== 执行时长统计 ===")
        if len(self.interval_records) > 0:
            prev_time = self.start_time
            interval_table = PrettyTable()
            interval_table.field_names = ["操作", "开始时间", "耗时(秒)"]
            interval_table.align = "r"
            interval_table.align["操作"] = "l"

            for i, (action, current_time) in enumerate(self.interval_records, 1):
                duration = (current_time - prev_time).total_seconds()
                interval_table.add_row([
                    f"{i}. {action if action else '操作' + str(i)}",
                    prev_time.strftime("%H:%M:%S.%f")[:-3],
                    f"{duration:.4f}"
                ])
                prev_time = current_time

            print(interval_table)

        total_duration = self.get_duration()
        if total_duration:
            print(f"\n总执行时长: {total_duration:.4f} 秒")


class ResourceMonitor:
    """资源监控类，独立线程运行以减少对主程序的影响"""
    def __init__(self, pids, update_interval=5):
        self.pids = pids
        self.update_interval = update_interval
        self.monitoring = False
        self.resource_data = {}
        self.thread = None
        
    def start(self):
        self.monitoring = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.monitoring = False
        if self.thread:
            self.thread.join(timeout=2)
            
    def _monitor_loop(self):
        """监控循环，在独立线程中运行"""
        while self.monitoring:
            # 获取主程序资源
            main_usage = self._get_process_usage(os.getpid())
            if main_usage:
                self.resource_data["main"] = main_usage
            
            # 获取每个子进程资源
            for pid in self.pids:
                usage = self._get_process_usage(pid)
                if usage:
                    self.resource_data[f"process_{pid}"] = usage
            
            # 获取所有 sumo 资源
            sumo_list = self._get_sumo_usage(os.getpid())
            for i, usage in enumerate(sumo_list, 1):
                self.resource_data[f"sumo_{i}"] = usage
                
            time.sleep(self.update_interval)
    
    def _get_process_usage(self, pid):
        """获取指定PID进程的CPU和内存使用情况"""
        try:
            process = psutil.Process(pid)
            # 使用非常短的间隔来减少阻塞
            cpu_percent = process.cpu_percent(interval=0.01)
            memory_mb = process.memory_info().rss / (1024 * 1024)
            return {
                "pid": pid,
                "name": process.name(),
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
            
    def _get_sumo_usage(self, parent_pid):
        """获取指定父进程下所有的 sumo 子进程资源使用"""
        try:
            parent = psutil.Process(parent_pid)
            children = parent.children(recursive=True)
            sumo_usages = []

            for child in children:
                if "sumo" in child.name().lower():
                    # 使用非常短的间隔来减少阻塞
                    cpu_percent = child.cpu_percent(interval=0.01)
                    memory_mb = child.memory_info().rss / (1024 * 1024)
                    sumo_usages.append({
                        "pid": child.pid,
                        "cpu_percent": cpu_percent,
                        "memory_mb": memory_mb
                    })
            return sumo_usages
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []
            
    def get_resource_data(self):
        """获取当前资源数据"""
        return self.resource_data.copy()


def run_simulation_per_process(shared_dict, instance_id, config_path):
    """
    每个SUMO仿真实例运行的函数
    :param shared_dict: 多进程共享字典，用于存储车辆数量和仿真时间
    :param instance_id: 实例ID
    :param config_path: SUMO 配置文件路径
    """
    # 使用无界面版本的SUMO
    traci.start(["sumo", "-c", config_path], label=f"sim{instance_id}")
    conn = traci.getConnection(f"sim{instance_id}")

    try:
        while conn.simulation.getMinExpectedNumber() > 0:
            conn.simulationStep()
            vehicle_count = len(conn.vehicle.getIDList())
            sim_time = conn.simulation.getTime()
            shared_dict[f"instance_{instance_id}"] = {"count": vehicle_count, "time": sim_time}
            
            # 添加短暂延迟，但不要过长
            if sim_time % 50 == 0:  # 每50个仿真步暂停一下
                time.sleep(0.001)
                
    except Exception as e:
        print(f"仿真进程 {instance_id} 出错: {e}")
    finally:
        conn.close()


def run_parallel_simulations(num_simulations, config_path):
    manager = multiprocessing.Manager()
    shared_data = manager.dict()

    processes = []
    pids = []
    
    # 启动仿真进程
    for i in range(num_simulations):
        p = multiprocessing.Process(
            target=run_simulation_per_process, 
            args=(shared_data, i, config_path)
        )
        p.start()
        processes.append(p)
        pids.append(p.pid)

    # 启动资源监控
    resource_monitor = ResourceMonitor(pids, update_interval=5)  # 每5秒更新一次资源数据
    resource_monitor.start()

    # 日志记录列表
    log_data = []
    data_collection_interval = 10  # 每10个仿真步收集一次车辆数据
    resource_collection_interval = 30  # 每30个仿真步收集一次资源数据
    
    timer = SimulationTimer()
    timer.start()
    timer.record_interval("启动多进程仿真")

    # 用于跟踪仿真进度
    last_sim_time = 0
    sim_steps_without_progress = 0
    
    try:
        # 主循环 - 监控仿真进度
        while any(p.is_alive() for p in processes):
            # 检查共享数据是否有更新
            if shared_data:
                current_sim_time = list(shared_data.values())[0]["time"]
                
                # 检查仿真是否在前进
                if current_sim_time > last_sim_time:
                    last_sim_time = current_sim_time
                    sim_steps_without_progress = 0
                else:
                    sim_steps_without_progress += 1
                    # 如果仿真长时间没有进展，可能已经完成或卡住
                    if sim_steps_without_progress > 100:
                        print("仿真似乎已完成或卡住，准备退出监控循环")
                        break
                
                # 定期收集车辆数据
                if current_sim_time % data_collection_interval == 0:
                    row = {
                        "时间戳": datetime.now().strftime("%H:%M:%S"),
                        "仿真时间(s)": current_sim_time,
                        "总车辆数": sum(v["count"] for v in shared_data.values())
                    }
                    
                    # 定期收集资源数据（频率较低）
                    if current_sim_time % resource_collection_interval == 0:
                        resource_data = resource_monitor.get_resource_data()
                        
                        # 添加主程序资源
                        if "main" in resource_data:
                            row["主程序CPU%"] = f"{resource_data['main']['cpu_percent']:.2f}"
                            row["主程序内存(MB)"] = f"{resource_data['main']['memory_mb']:.2f}"
                        
                        # 添加子进程资源
                        process_count = 1
                        for key, data in resource_data.items():
                            if key.startswith("process_"):
                                row[f"子进程{process_count} CPU%"] = f"{data['cpu_percent']:.2f}"
                                row[f"子进程{process_count} 内存(MB)"] = f"{data['memory_mb']:.2f}"
                                process_count += 1
                        
                        # 添加SUMO进程资源
                        sumo_count = 1
                        for key, data in resource_data.items():
                            if key.startswith("sumo_"):
                                row[f"SUMO进程{sumo_count} CPU%"] = f"{data['cpu_percent']:.2f}"
                                row[f"SUMO进程{sumo_count} 内存(MB)"] = f"{data['memory_mb']:.2f}"
                                sumo_count += 1
                    
                    # 添加到日志
                    log_data.append(row)
                    
                    # 每收集100次数据保存一次临时文件
                    if len(log_data) % 100 == 0:
                        df = pd.DataFrame(log_data)
                        temp_file = f"temp_simulation_data_{len(log_data)//100}.xlsx"
                        df.to_excel(temp_file, index=False)
                        print(f"已保存临时数据到 {temp_file}")
                    
                    # 打印进度
                    if current_sim_time % 100 == 0:
                        print(f"仿真时间: {current_sim_time}s, 车辆数: {row['总车辆数']}")
            
            # 短暂睡眠以减少CPU占用
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("正在终止仿真...")
    except Exception as e:
        print(f"监控循环出错: {e}")
    finally:
        # 停止资源监控
        resource_monitor.stop()
        
        timer.stop()
        timer.print_statistics()
        
        # 保存所有数据到最终Excel文件
        if log_data:
            df = pd.DataFrame(log_data)
            excel_path = "simulation_vehicle_stats_with_resources.xlsx"
            df.to_excel(excel_path, index=False)
            print(f"\n所有车辆统计和资源数据已保存至 {excel_path}")
            
            # 删除临时文件
            for i in range(1, 1000000):
                temp_file = f"temp_simulation_data_{i}.xlsx"
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"已删除临时文件: {temp_file}")
        
        # 终止所有仿真进程
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join()


if __name__ == "__main__":
    num_simulations = 65  # 启动的仿真数量
    config_path = r"D:/sumo大规模路网/新建文件夹/run_20250731_195139/simulation.sumocfg"  # 替换为你的配置文件路径
    
    print("开始运行SUMO仿真...")
    print(f"配置文件: {config_path}")
    print("正在实时统计车辆数量和系统资源...")
    
    run_parallel_simulations(num_simulations, config_path)
