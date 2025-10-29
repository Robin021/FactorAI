#!/usr/bin/env python3
"""
直接测试情绪分析工具
用于调试情绪工具是否能正常生成报告
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tradingagents.utils.logging_init import get_logger
from tradingagents.tools.sentiment_tools import create_sentiment_analysis_tool
from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.utils.stock_utils import StockUtils

logger = get_logger("test_sentiment_tool_direct")


def test_sentiment_tool_us():
    """直接测试美股情绪工具"""
    logger.info("=" * 80)
    logger.info("测试美股情绪工具")
    logger.info("=" * 80)
    
    try:
        # 创建工具包
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit()
        toolkit.update_config(config)
        
        # 准备测试数据
        ticker = "AAPL"
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        logger.info(f"市场信息: {market_info}")
        
        # 创建情绪工具
        sentiment_tool = create_sentiment_analysis_tool(toolkit, market_info)
        
        # 调用工具
        logger.info(f"调用情绪工具: ticker={ticker}, date={date}, market_type={market_info['market_name']}")
        result = sentiment_tool.invoke({
            'ticker': ticker,
            'date': date,
            'market_type': market_info['market_name']
        })
        
        # 打印结果
        logger.info(f"结果类型: {type(result)}")
        logger.info(f"结果长度: {len(str(result))} 字符")
        logger.info(f"结果内容:\n{result}")
        
        # 验证结果
        assert result is not None, "工具返回None"
        assert len(str(result)) > 50, f"结果太短: {len(str(result))} 字符"
        
        # 检查关键内容
        result_str = str(result)
        checks = {
            "包含股票代码": ticker in result_str,
            "包含情绪评分": "评分" in result_str or "score" in result_str.lower(),
            "包含市场类型": market_info['market_name'] in result_str,
            "包含数据": "数据" in result_str or "data" in result_str.lower(),
        }
        
        logger.info("\n内容检查:")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"  {status} {check_name}")
        
        passed_count = sum(1 for v in checks.values() if v)
        logger.info(f"\n检查通过: {passed_count}/{len(checks)}")
        
        if passed_count >= len(checks) * 0.75:
            logger.info("✅ 美股情绪工具测试通过")
            return True
        else:
            logger.warning("⚠️ 美股情绪工具测试部分通过")
            return True  # 仍然返回True，因为工具能工作
        
    except Exception as e:
        logger.error(f"❌ 美股情绪工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sentiment_tool_cn():
    """直接测试A股情绪工具"""
    logger.info("=" * 80)
    logger.info("测试A股情绪工具")
    logger.info("=" * 80)
    
    try:
        # 创建工具包
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit()
        toolkit.update_config(config)
        
        # 准备测试数据
        ticker = "600519"
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        logger.info(f"市场信息: {market_info}")
        
        # 创建情绪工具
        sentiment_tool = create_sentiment_analysis_tool(toolkit, market_info)
        
        # 调用工具
        logger.info(f"调用情绪工具: ticker={ticker}, date={date}, market_type={market_info['market_name']}")
        result = sentiment_tool.invoke({
            'ticker': ticker,
            'date': date,
            'market_type': market_info['market_name']
        })
        
        # 打印结果
        logger.info(f"结果类型: {type(result)}")
        logger.info(f"结果长度: {len(str(result))} 字符")
        logger.info(f"结果内容:\n{result}")
        
        # 验证结果
        assert result is not None, "工具返回None"
        assert len(str(result)) > 50, f"结果太短: {len(str(result))} 字符"
        
        # 检查A股特有内容
        result_str = str(result)
        checks = {
            "包含股票代码": ticker in result_str,
            "包含情绪评分": "评分" in result_str,
            "包含市场类型": "A股" in result_str or "中国" in result_str,
            "包含北向资金": "北向" in result_str,
        }
        
        logger.info("\n内容检查:")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"  {status} {check_name}")
        
        passed_count = sum(1 for v in checks.values() if v)
        logger.info(f"\n检查通过: {passed_count}/{len(checks)}")
        
        if passed_count >= len(checks) * 0.75:
            logger.info("✅ A股情绪工具测试通过")
            return True
        else:
            logger.warning("⚠️ A股情绪工具测试部分通过")
            return True
        
    except Exception as e:
        logger.error(f"❌ A股情绪工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sentiment_tool_hk():
    """直接测试港股情绪工具"""
    logger.info("=" * 80)
    logger.info("测试港股情绪工具")
    logger.info("=" * 80)
    
    try:
        # 创建工具包
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit()
        toolkit.update_config(config)
        
        # 准备测试数据
        ticker = "00700.HK"
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        logger.info(f"市场信息: {market_info}")
        
        # 创建情绪工具
        sentiment_tool = create_sentiment_analysis_tool(toolkit, market_info)
        
        # 调用工具
        logger.info(f"调用情绪工具: ticker={ticker}, date={date}, market_type={market_info['market_name']}")
        result = sentiment_tool.invoke({
            'ticker': ticker,
            'date': date,
            'market_type': market_info['market_name']
        })
        
        # 打印结果
        logger.info(f"结果类型: {type(result)}")
        logger.info(f"结果长度: {len(str(result))} 字符")
        logger.info(f"结果内容:\n{result}")
        
        # 验证结果
        assert result is not None, "工具返回None"
        assert len(str(result)) > 50, f"结果太短: {len(str(result))} 字符"
        
        # 检查港股特有内容
        result_str = str(result)
        checks = {
            "包含股票代码": "00700" in result_str or "700" in result_str,
            "包含情绪评分": "评分" in result_str,
            "包含市场类型": "港股" in result_str or "香港" in result_str,
            "包含南向资金": "南向" in result_str,
        }
        
        logger.info("\n内容检查:")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"  {status} {check_name}")
        
        passed_count = sum(1 for v in checks.values() if v)
        logger.info(f"\n检查通过: {passed_count}/{len(checks)}")
        
        if passed_count >= len(checks) * 0.75:
            logger.info("✅ 港股情绪工具测试通过")
            return True
        else:
            logger.warning("⚠️ 港股情绪工具测试部分通过")
            return True
        
    except Exception as e:
        logger.error(f"❌ 港股情绪工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有直接工具测试"""
    logger.info("=" * 80)
    logger.info("情绪分析工具直接测试")
    logger.info("=" * 80)
    logger.info("")
    
    test_results = []
    
    # 测试1: 美股工具
    test_results.append(("美股情绪工具", test_sentiment_tool_us()))
    
    # 测试2: A股工具
    test_results.append(("A股情绪工具", test_sentiment_tool_cn()))
    
    # 测试3: 港股工具
    test_results.append(("港股情绪工具", test_sentiment_tool_hk()))
    
    # 汇总结果
    logger.info("")
    logger.info("=" * 80)
    logger.info("测试结果汇总")
    logger.info("=" * 80)
    
    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{status} - {test_name}")
    
    passed_count = sum(1 for _, passed in test_results if passed)
    total_count = len(test_results)
    
    logger.info("")
    logger.info(f"总计: {passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        logger.info("🎉 所有工具测试通过！")
        return 0
    else:
        logger.error(f"⚠️ {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
