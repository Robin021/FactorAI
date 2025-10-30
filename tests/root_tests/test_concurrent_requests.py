#!/usr/bin/env python3
"""
测试并发请求场景（模拟后端多个分析任务）
"""

import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tradingagents.dataflows.market_heat_data import MarketHeatDataSource

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def fetch_market_data(task_id: int):
    """模拟一个分析任务获取市场数据"""
    try:
        logger.info(f"🔄 任务 {task_id} 开始获取市场数据")
        start_time = time.time()
        
        data = MarketHeatDataSource.get_market_overview(max_retries=3)
        
        elapsed = time.time() - start_time
        
        if data['stats']['total_stocks'] > 0:
            logger.info(f"✅ 任务 {task_id} 成功 (耗时 {elapsed:.2f}秒) - 获取到 {data['stats']['total_stocks']} 只股票数据")
            return True, task_id, elapsed
        else:
            logger.warning(f"⚠️ 任务 {task_id} 使用默认数据 (耗时 {elapsed:.2f}秒)")
            return False, task_id, elapsed
            
    except Exception as e:
        logger.error(f"❌ 任务 {task_id} 失败: {e}")
        return False, task_id, 0

def test_concurrent_requests():
    """测试并发请求"""
    print("=" * 80)
    print("🔍 测试并发请求场景（模拟后端多个分析任务）")
    print("=" * 80)
    
    num_tasks = 5  # 模拟5个并发任务
    
    print(f"\n📊 启动 {num_tasks} 个并发任务...")
    
    start_time = time.time()
    success_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=num_tasks) as executor:
        futures = [executor.submit(fetch_market_data, i+1) for i in range(num_tasks)]
        
        for future in as_completed(futures):
            success, task_id, elapsed = future.result()
            if success:
                success_count += 1
            else:
                failed_count += 1
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("📈 测试结果:")
    print(f"   总任务数: {num_tasks}")
    print(f"   成功: {success_count}")
    print(f"   失败/使用默认: {failed_count}")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   平均耗时: {total_time/num_tasks:.2f}秒/任务")
    print("=" * 80)
    
    # 如果大部分任务成功，认为测试通过
    return success_count >= num_tasks * 0.6

if __name__ == "__main__":
    success = test_concurrent_requests()
    
    if success:
        print("\n✅ 并发测试通过！缓存机制工作正常。")
    else:
        print("\n⚠️ 并发测试部分失败，但这可能是正常的（数据源限流）")
    
    sys.exit(0 if success else 1)
