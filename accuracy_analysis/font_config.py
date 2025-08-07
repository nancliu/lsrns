"""
字体配置模块
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import warnings
warnings.filterwarnings('ignore')

def setup_chinese_font():
    """
    设置中文字体支持
    
    Returns:
        FontProperties: 字体属性对象
    """
    # 常见中文字体列表（按优先级排序）
    chinese_fonts = [
        'SimHei',           # 黑体
        'Microsoft YaHei',  # 微软雅黑
        'KaiTi',            # 楷体
        'SimSun',           # 宋体
        'FangSong',         # 仿宋
        'NSimSun',          # 新宋体
        'STHeiti',          # 华文黑体
        'STZhongsong',      # 华文中宋
        'STFangsong',       # 华文仿宋
        'STKaiti',          # 华文楷体
        'STSong',           # 华文宋体
        'Arial Unicode MS', # Arial Unicode
        'WenQuanYi Micro Hei',  # 文泉驿微米黑
        'DejaVu Sans',      # DejaVu Sans
    ]
    
    # 尝试找到可用的中文字体
    available_font = None
    for font_name in chinese_fonts:
        try:
            # 检查字体是否可用
            font_path = fm.findfont(font_name)
            font = fm.FontProperties(fname=font_path)
            if font:
                available_font = font_name
                print(f"成功设置中文字体: {font_name}")
                break
        except:
            continue
    
    # 设置matplotlib字体
    if available_font:
        plt.rcParams['font.sans-serif'] = [available_font] + plt.rcParams['font.sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
    else:
        print("警告: 未找到合适的中文字体，中文显示可能异常")
        # 使用默认字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans'] + plt.rcParams['font.sans-serif']
    
    # 设置全局字体大小
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10
    
    # 返回字体属性对象
    return fm.FontProperties(family=available_font or 'DejaVu Sans')

def get_font_properties():
    """
    获取字体属性对象
    
    Returns:
        FontProperties: 字体属性对象
    """
    return fm.FontProperties(family=plt.rcParams['font.sans-serif'][0])

def force_chinese_font():
    """
    强制设置中文字体，用于解决中文显示问题
    
    Returns:
        FontProperties: 字体属性对象
    """
    # 常见中文字体列表（按优先级排序）
    chinese_fonts = [
        'SimHei',           # 黑体
        'Microsoft YaHei',  # 微软雅黑
        'KaiTi',            # 楷体
        'SimSun',           # 宋体
        'FangSong',         # 仿宋
        'NSimSun',          # 新宋体
        'STHeiti',          # 华文黑体
        'STZhongsong',      # 华文中宋
        'STFangsong',       # 华文仿宋
        'STKaiti',          # 华文楷体
        'STSong',           # 华文宋体
        'Arial Unicode MS', # Arial Unicode
        'WenQuanYi Micro Hei',  # 文泉驿微米黑
        'DejaVu Sans',      # DejaVu Sans
    ]
    
    # 尝试找到可用的中文字体
    available_font = None
    font_path = None
    
    for font_name in chinese_fonts:
        try:
            # 检查字体是否可用
            font_path = fm.findfont(font_name)
            if font_path and font_path != plt.rcParams['font.sans-serif'][0]:
                # 验证字体文件是否存在
                import os
                if os.path.exists(font_path):
                    available_font = font_name
                    print(f"✓ 找到中文字体: {font_name} (路径: {font_path})")
                    break
                else:
                    print(f"✗ 字体文件不存在: {font_path}")
            else:
                print(f"✗ 字体不可用: {font_name}")
        except Exception as e:
            print(f"✗ 尝试字体 {font_name} 失败: {e}")
            continue
    
    if not available_font:
        print("警告: 未找到合适的中文字体")
        return get_font_properties()
    
    # 强制设置matplotlib字体
    plt.rcParams['font.sans-serif'] = [available_font] + [f for f in plt.rcParams['font.sans-serif'] if f != available_font]
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.family'] = 'sans-serif'
    
    # 清除字体缓存
    try:
        fm._rebuild()
    except AttributeError:
        # 新版本的matplotlib可能没有_rebuild方法
        pass
    
    print(f"✓ 字体设置完成: {available_font}")
    
    # 返回字体属性对象
    return fm.FontProperties(fname=font_path)

def test_font_support():
    """
    测试字体支持情况
    
    Returns:
        bool: 是否支持中文字体
    """
    try:
        # 创建测试图
        fig, ax = plt.subplots(figsize=(6, 4))
        font_prop = get_font_properties()
        
        # 测试中文文本
        test_text = "中文测试：MAPE分布直方图"
        ax.text(0.5, 0.5, test_text, ha='center', va='center', 
                fontsize=16, fontproperties=font_prop)
        ax.set_title('测试标题', fontproperties=font_prop)
        ax.set_xlabel('测试X轴', fontproperties=font_prop)
        ax.set_ylabel('测试Y轴', fontproperties=font_prop)
        
        # 保存到临时文件
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_path = tmp.name
        
        plt.savefig(temp_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        # 检查文件是否成功生成
        success = os.path.exists(temp_path) and os.path.getsize(temp_path) > 0
        
        # 清理临时文件
        try:
            os.unlink(temp_path)
        except:
            pass
        
        return success
        
    except Exception as e:
        print(f"字体测试失败: {e}")
        return False

# 初始化字体设置
chinese_font_prop = setup_chinese_font()