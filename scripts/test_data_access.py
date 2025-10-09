#!/usr/bin/env python3
"""
测试数据访问是否正常
验证 YFin-data CSV 文件是否可以正常读取
"""

import os
import sys
import pandas as pd
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.config import get_data_dir, DATA_DIR

logger = get_logger('test_data_access')


def test_data_file_access(symbol: str = "600580.SS"):
    """
    测试数据文件访问
    
    Args:
        symbol: 股票代码
    """
    try:
        logger.info(f"🧪 测试数据文件访问: {symbol}")
        
        # 获取数据目录
        data_dir = get_data_dir()
        logger.info(f"📁 配置的数据目录: {data_dir}")
        logger.info(f"📁 DATA_DIR 变量: {DATA_DIR}")
        
        # 构建文件路径（模拟 interface.py 中的逻辑）
        file_path = os.path.join(
            DATA_DIR,
            f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv"
        )
        
        logger.info(f"📄 尝试读取文件: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"❌ 文件不存在: {file_path}")
            return False
        
        # 尝试读取文件
        data = pd.read_csv(file_path)
        logger.info(f"✅ 文件读取成功!")
        logger.info(f"📊 数据行数: {len(data)}")
        logger.info(f"📋 列名: {list(data.columns)}")
        
        # 检查Date列
        if 'Date' in data.columns:
            data["Date"] = pd.to_datetime(data["Date"], utc=True)
            logger.info(f"📅 日期范围: {data['Date'].min()} 到 {data['Date'].max()}")
        
        # 显示前几行数据
        logger.info("📋 前5行数据:")
        logger.info(f"\n{data.head().to_string()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return False


def test_multiple_symbols():
    """测试多个股票代码"""
    test_symbols = [
        "600580.SS",  # 卧龙电驱
        "000001.SZ",  # 平安银行
        "AAPL",       # 苹果
    ]
    
    logger.info(f"🧪 测试多个股票代码: {test_symbols}")
    
    success_count = 0
    for symbol in test_symbols:
        if test_data_file_access(symbol):
            success_count += 1
        logger.info("-" * 50)
    
    logger.info(f"✅ 测试结果: {success_count}/{len(test_symbols)} 成功")
    return success_count == len(test_symbols)


def main():
    """主函数"""
    logger.info("🔧 开始测试数据文件访问")
    
    # 显示当前工作目录
    logger.info(f"📁 当前工作目录: {os.getcwd()}")
    
    # 测试单个文件
    logger.info("=" * 60)
    logger.info("测试单个文件 (600580.SS)")
    logger.info("=" * 60)
    
    success = test_data_file_access("600580.SS")
    
    if success:
        logger.info("🎉 单个文件测试通过!")
    else:
        logger.error("❌ 单个文件测试失败!")
        return
    
    # 测试多个文件
    logger.info("=" * 60)
    logger.info("测试多个文件")
    logger.info("=" * 60)
    
    all_success = test_multiple_symbols()
    
    if all_success:
        logger.info("🎉 所有测试通过! 数据文件访问正常!")
        logger.info("💡 原来的 '[Errno 2] No such file or directory' 问题应该已经解决")
    else:
        logger.error("❌ 部分测试失败!")


if __name__ == "__main__":
    main()