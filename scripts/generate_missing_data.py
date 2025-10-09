#!/usr/bin/env python3
"""
生成缺失的股票数据文件
用于解决 YFin-data CSV 文件缺失的问题
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    print("❌ yfinance 库未安装，请运行: pip install yfinance")
    YFINANCE_AVAILABLE = False
    sys.exit(1)

from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.config import get_data_dir

logger = get_logger('generate_missing_data')


def download_stock_data(symbol: str, start_date: str = "2015-01-01", end_date: str = "2025-03-25"):
    """
    下载股票数据并保存为CSV文件
    
    Args:
        symbol: 股票代码 (如 600580.SS)
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        logger.info(f"📈 开始下载股票数据: {symbol}")
        
        # 创建yfinance ticker对象
        ticker = yf.Ticker(symbol)
        
        # 下载历史数据
        data = ticker.history(start=start_date, end=end_date)
        
        if data.empty:
            logger.error(f"❌ 无法获取 {symbol} 的数据")
            return False
        
        # 获取数据目录
        data_dir = get_data_dir()
        price_data_dir = Path(data_dir) / "market_data" / "price_data"
        
        # 确保目录存在
        price_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        filename = f"{symbol}-YFin-data-{start_date}-{end_date}.csv"
        filepath = price_data_dir / filename
        
        # 重置索引，将Date作为列
        data.reset_index(inplace=True)
        
        # 保存为CSV
        data.to_csv(filepath, index=False)
        
        logger.info(f"✅ 数据已保存到: {filepath}")
        logger.info(f"📊 数据行数: {len(data)}")
        logger.info(f"📅 数据范围: {data['Date'].min()} 到 {data['Date'].max()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 下载 {symbol} 数据时出错: {e}")
        return False


def generate_common_stocks_data():
    """生成常用股票的数据文件"""
    
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
    
    logger.info(f"🚀 开始生成 {len(all_stocks)} 只股票的数据文件")
    
    success_count = 0
    failed_stocks = []
    
    for symbol in all_stocks:
        logger.info(f"📈 处理股票: {symbol}")
        
        if download_stock_data(symbol):
            success_count += 1
        else:
            failed_stocks.append(symbol)
        
        # 添加延迟避免API限制
        import time
        time.sleep(1)
    
    logger.info(f"✅ 成功生成 {success_count}/{len(all_stocks)} 只股票的数据")
    
    if failed_stocks:
        logger.warning(f"⚠️ 以下股票数据生成失败: {failed_stocks}")
    
    return success_count, failed_stocks


def main():
    """主函数"""
    if not YFINANCE_AVAILABLE:
        return
    
    logger.info("🔧 开始生成缺失的股票数据文件")
    
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
    
    # 生成数据
    success_count, failed_stocks = generate_common_stocks_data()
    
    logger.info("🎉 数据生成完成!")
    logger.info(f"✅ 成功: {success_count} 只股票")
    
    if failed_stocks:
        logger.info(f"❌ 失败: {len(failed_stocks)} 只股票")
        logger.info("💡 提示: 失败的股票可能是代码错误或网络问题")


if __name__ == "__main__":
    main()