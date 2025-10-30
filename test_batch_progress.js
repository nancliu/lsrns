// 测试脚本：验证live_time_series数据的返回和处理

const API_BASE = '/api/v1';
const BATCH_ID = 'batch_20251029_155729';

async function testBatchProgress() {
    try {
        const response = await fetch(`${API_BASE}/control/optimization/batch/${BATCH_ID}/progress`);
        const data = await response.json();
        
        console.log('=== Batch Progress Response ===');
        console.log('Status:', data.status);
        console.log('Progress:', data.progress);
        console.log('Running tasks:', data.running_tasks);
        console.log('Has live_time_series:', !!data.live_time_series);
        
        if (data.live_time_series) {
            console.log('live_time_series details:');
            console.log('  - time_points length:', data.live_time_series.time_points?.length);
            console.log('  - total_running length:', data.live_time_series.total_running?.length);
            console.log('  - task_count:', data.live_time_series.task_count);
            console.log('  - First 5 time points:', data.live_time_series.time_points?.slice(0, 5));
            console.log('  - First 5 running values:', data.live_time_series.total_running?.slice(0, 5));
        }
        
        // 检查是否有live_status
        data.tasks.forEach(task => {
            if (task.status === 'running' && task.live_status) {
                console.log(`Task ${task.task_id} live_status:`, task.live_status);
            }
        });
        
    } catch (error) {
        console.error('Test error:', error);
    }
}

// 如果在Node.js中运行
if (typeof module !== 'undefined' && module.exports) {
    testBatchProgress();
}
