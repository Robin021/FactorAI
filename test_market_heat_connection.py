#!/usr/bin/env python3
"""
测试市场热度数据连接问题
"""

import logging
import sys
from tradingagents.dataflows.market_heat_data import MarketHeatDataSource

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_market_data_connection():
    """测试市场数据连接"""
    print("=" * 80)
    print("🔍 测试市场热度数据获取")
    print("=" * 80)
    
    try:
        # 测试获取市场数据
        logger.info("开始测试市场数据获取...")
        data = MarketHeatDataSource.get_market_overview(max_retries=3)
        
        print("\n✅ 成功获取市场数据:")
        print(f"   日期: {data['date']}")
        print(f"   成交量放大倍数: {data['volume_ratio']:.2f}x")
        print(f"   涨停家数占比: {data['limit_up_ratio']:.2%}")
        print(f"   平均换手率: {data['turnover_rate']:.2f}%")
        print(f"   市场宽度: {data['market_breadth']:.2%}")
        print(f"   市场波动率: {data['volatility']:.2f}%")
        print(f"   资金流向: {data['money_flow']:.2f}")
        
        # 检查数据来源
        if data['stats']['total_stocks'] > 0:
            print(f"\n📊 统计信息 (实时市场数据):")
            print(f"   总股票数: {data['stats']['total_stocks']}")
            print(f"   涨停: {data['stats']['limit_up_count']}家")
            print(f"   上涨: {data['stats']['up_count']}家")
            print(f"   下跌: {data['stats']['down_count']}家")
            print(f"   平盘: {data['stats']['flat_count']}家")
        elif 'data_source' in data and data['data_source'] == 'index_estimation':
            print(f"\n📊 使用指数数据估算 (后备方案)")
            print(f"   数据来源: 上证指数、深证成指、创业板指")
        else:
            print(f"\n⚠️ 使用默认数据 (无法获取实时数据)")
        
        print("\n" + "=" * 80)
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_market_data_connection()
    sys.exit(0 if success else 1)
