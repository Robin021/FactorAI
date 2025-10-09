#!/usr/bin/env python3
"""
创建示例股票数据文件
用于解决 YFin-data CSV 文件缺失的问题
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.config import get_data_dir

logger = get_logger('create_sample_data')


def create_sample_stock_data(symbol: str, start_date: str = "2015-01-01", end_date: str = "2025-03-25"):
    """
    创建示例股票数据
    
    Args:
        symbol: 股票代码 (如 600580.SS)
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        logger.info(f"📈 创建示例数据: {symbol}")
        
        # 生成日期范围
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # 生成交易日（排除周末）
        date_range = pd.bdate_range(start=start, end=end)
        
        # 生成示例价格数据
        np.random.seed(42)  # 固定随机种子，确保数据一致性
        
        # 基础价格（根据股票类型设置）
        if symbol.startswith('6') or symbol.endswith('.SS') or symbol.endswith('.SZ'):
            # A股，价格范围 10-100
            base_price = 30.0
        else:
            # 美股，价格范围 100-300
            base_price = 150.0
        
        # 生成价格走势（随机游走）
        returns = np.random.normal(0.0005, 0.02, len(date_range))  # 日收益率
        prices = [base_price]
        
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 1.0))  # 确保价格不为负
        
        # 生成其他数据
        data = []
        for i, date in enumerate(date_range):
            price = prices[i]
            
            # 生成OHLC数据
            high = price * (1 + np.random.uniform(0, 0.05))
            low = price * (1 - np.random.uniform(0, 0.05))
            open_price = price * (1 + np.random.uniform(-0.02, 0.02))
            close_price = price
            
            # 生成成交量
            volume = int(np.random.uniform(1000000, 10000000))
            
            data.append({
                'Date': date,
                'Open': round(open_price, 2),
                'High': round(high, 2),
                'Low': round(low, 2),
                'Close': round(close_price, 2),
                'Volume': volume,
                'Dividends': 0.0,
                'Stock Splits': 0.0
            })
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 获取数据目录
        data_dir = get_data_dir()
        price_data_dir = Path(data_dir) / "market_data" / "price_data"
        
        # 确保目录存在
        price_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        filename = f"{symbol}-YFin-data-{start_date}-{end_date}.csv"
        filepath = price_data_dir / filename
        
        # 保存为CSV
        df.to_csv(filepath, index=False)
        
        logger.info(f"✅ 示例数据已保存到: {filepath}")
        logger.info(f"📊 数据行数: {len(df)}")
        logger.info(f"📅 数据范围: {df['Date'].min()} 到 {df['Date'].max()}")
        logger.info(f"💰 价格范围: {df['Close'].min():.2f} - {df['Close'].max():.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建 {symbol} 示例数据时出错: {e}")
        return False


def create_common_stocks_sample_data():
    """创建常用股票的示例数据文件"""
    
    # 常用的股票代码列表
    common_stocks = [
        "600580.SS",  # 卧龙电驱
        "000001.SZ",  # 平安银行
        "600036.SS",  # 招商银行
        "000002.SZ",  # 万科A
        "600519.SS",  # 贵州茅台
        "000858.SZ",  # 五粮液
        "600276.SS",  # 恒瑞医药
        "000063.SZ",  # 中兴通讯
        "002415.SZ",  # 海康威视
        "600887.SS",  # 伊利股份
    ]
    
    # 美股代码
    us_stocks = [
        "AAPL",       # 苹果
        "MSFT",       # 微软
        "GOOGL",      # 谷歌
        "TSLA",       # 特斯拉
        "NVDA",       # 英伟达
    ]
    
    all_stocks = common_stocks + us_stocks
    
    logger.info(f"🚀 开始创建 {len(all_stocks)} 只股票的示例数据文件")
    
    success_count = 0
    failed_stocks = []
    
    for symbol in all_stocks:
        logger.info(f"📈 处理股票: {symbol}")
        
        if create_sample_stock_data(symbol):
            success_count += 1
        else:
            failed_stocks.append(symbol)
    
    logger.info(f"✅ 成功创建 {success_count}/{len(all_stocks)} 只股票的示例数据")
    
    if failed_stocks:
        logger.warning(f"⚠️ 以下股票示例数据创建失败: {failed_stocks}")
    
    return success_count, failed_stocks


def main():
    """主函数"""
    logger.info("🔧 开始创建示例股票数据文件")
    
    # 检查数据目录
    data_dir = get_data_dir()
    logger.info(f"📁 数据目录: {data_dir}")
    
    price_data_dir = Path(data_dir) / "market_data" / "price_data"
    logger.info(f"📁 价格数据目录: {price_data_dir}")
    
    # 检查目录是否存在
    if not price_data_dir.exists():
        logger.info(f"📁 创建价格数据目录: {price_data_dir}")
        price_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查现有文件
    existing_files = list(price_data_dir.glob("*.csv"))
    logger.info(f"📊 现有数据文件数量: {len(existing_files)}")
    
    if existing_files:
        logger.info("📋 现有文件:")
        for file in existing_files[:5]:  # 只显示前5个
            logger.info(f"  - {file.name}")
        if len(existing_files) > 5:
            logger.info(f"  ... 还有 {len(existing_files) - 5} 个文件")
    
    # 创建示例数据
    success_count, failed_stocks = create_common_stocks_sample_data()
    
    logger.info("🎉 示例数据创建完成!")
    logger.info(f"✅ 成功: {success_count} 只股票")
    
    if failed_stocks:
        logger.info(f"❌ 失败: {len(failed_stocks)} 只股票")
    
    logger.info("💡 提示: 这些是示例数据，用于测试。生产环境请使用真实数据。")


if __name__ == "__main__":
    main()