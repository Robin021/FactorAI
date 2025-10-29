"""
情绪分析工具模块
为市场情绪分析师提供LLM可调用的工具函数

需求: 11.3, 11.4
"""

from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field as PydanticField
from typing import Dict, Any
from datetime import datetime

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
# 导入数据源管理器
from tradingagents.dataflows.sentiment_data_sources import (
    CoreSentimentDataSource,
    USEnhancedDataSource,
    CNEnhancedDataSource,
    HKEnhancedDataSource
)
# 导入情绪计算器
from tradingagents.agents.utils.sentiment_calculator import SentimentCalculator
# 导入缓存管理器
from tradingagents.dataflows.sentiment_cache import get_sentiment_cache
# 导入降级策略
from tradingagents.agents.utils.fallback_strategy import FallbackStrategy

logger = get_logger("sentiment_tools")


def create_sentiment_analysis_tool(toolkit, market_info: Dict[str, Any]) -> StructuredTool:
    """
    创建情绪分析工具
    
    Args:
        toolkit: 工具集
        market_info: 市场信息字典
    
    Returns:
        情绪分析工具
    
    需求: 11.3
    """
    
    # 定义输入模型
    class SentimentAnalysisInput(BaseModel):
        ticker: str = PydanticField(description="股票代码")
        date: str = PydanticField(description="分析日期 (YYYY-MM-DD)")
        market_type: str = PydanticField(description="市场类型")
    
    def get_market_sentiment_data(ticker: str, date: str, market_type: str) -> str:
        """
        获取市场情绪数据
        
        Args:
            ticker: 股票代码
            date: 日期 (YYYY-MM-DD)
            market_type: 市场类型
        
        Returns:
            情绪数据的文本描述
        
        需求: 1.5, 2.4, 2.5
        """
        logger.info(f"[情绪工具] 获取市场情绪数据: {ticker}, {date}, {market_type}")
        
        try:
            # 初始化缓存和降级策略
            cache_manager = get_sentiment_cache()
            fallback_strategy = FallbackStrategy()
            
            # 初始化核心数据源 - 需求 2.1, 2.2, 2.3
            core_source = CoreSentimentDataSource(
                cache_manager=cache_manager,
                toolkit=toolkit,
                fallback_strategy=fallback_strategy
            )
            
            # 获取核心情绪数据
            logger.info(f"[情绪工具] 获取核心情绪数据...")
            core_data = core_source.get_data(ticker, date)
            
            # 提取核心组件评分
            components = {
                'news': core_data.get('news_sentiment', 0.0),
                'technical': core_data.get('price_momentum', 0.0),
                'volume': core_data.get('volume_sentiment', 0.0)
            }
            
            logger.info(f"[情绪工具] 核心组件评分: {components}")
            
            # 根据市场类型获取增强数据 - 需求 3.1-3.6, 4.1-4.10, 5.1-5.5
            enhanced_data = {}
            
            if market_info['is_us']:
                # 美股增强数据 - 需求 3.1-3.6
                logger.info(f"[情绪工具] 获取美股增强数据...")
                us_source = USEnhancedDataSource(
                    cache_manager=cache_manager,
                    toolkit=toolkit,
                    fallback_strategy=fallback_strategy
                )
                enhanced_data = us_source.get_data(ticker, date)
                
                components['volatility'] = enhanced_data.get('vix_sentiment', 0.0)
                components['social'] = enhanced_data.get('reddit_sentiment', 0.0)
                
            elif market_info['is_china']:
                # A股增强数据 - 需求 4.1-4.10
                logger.info(f"[情绪工具] 获取A股增强数据...")
                cn_source = CNEnhancedDataSource(
                    cache_manager=cache_manager,
                    toolkit=toolkit,
                    fallback_strategy=fallback_strategy
                )
                enhanced_data = cn_source.get_data(ticker, date)
                
                components['money_flow'] = enhanced_data.get('northbound_flow', 0.0)
                components['volatility'] = enhanced_data.get('volatility_sentiment', 0.0)
                # 融资融券数据可选
                margin_sentiment = enhanced_data.get('margin_trading', None)
                if margin_sentiment is not None:
                    components['margin'] = margin_sentiment
                
            elif market_info['is_hk']:
                # 港股增强数据 - 需求 5.1-5.5
                logger.info(f"[情绪工具] 获取港股增强数据...")
                hk_source = HKEnhancedDataSource(
                    cache_manager=cache_manager,
                    toolkit=toolkit,
                    fallback_strategy=fallback_strategy
                )
                enhanced_data = hk_source.get_data(ticker, date)
                
                components['money_flow'] = enhanced_data.get('southbound_flow', 0.0)
            
            logger.info(f"[情绪工具] 所有组件评分: {components}")
            
            # 检测背离 - 新增功能
            calculator = SentimentCalculator()
            divergence_result = calculator.detect_divergence(components)
            
            # 计算综合情绪评分 - 需求 6.1, 6.2, 6.9
            sentiment_result = calculator.calculate_composite_score(components)
            
            composite_score = sentiment_result['score']
            sentiment_level = sentiment_result['level']
            breakdown = sentiment_result['breakdown']
            
            # 如果存在背离，记录警告
            if divergence_result['has_divergence']:
                logger.warning(
                    f"[情绪工具] 检测到背离: {divergence_result['divergence_type']}, "
                    f"强度: {divergence_result['divergence_strength']:.2f}"
                )
            
            logger.info(f"[情绪工具] 综合情绪评分: {composite_score}, 等级: {sentiment_level}")
            
            # 生成文本描述 - 需求 7.1, 7.2, 7.3, 7.4
            report_lines = []
            report_lines.append(f"# 市场情绪数据")
            report_lines.append(f"")
            report_lines.append(f"**股票代码**: {ticker}")
            report_lines.append(f"**分析日期**: {date}")
            report_lines.append(f"**市场类型**: {market_type}")
            report_lines.append(f"")
            report_lines.append(f"## 综合情绪评估")
            report_lines.append(f"")
            report_lines.append(f"- **综合情绪评分**: {composite_score:.2f} / 100")
            report_lines.append(f"- **情绪等级**: {sentiment_level}")
            report_lines.append(f"")
            
            # 背离警告 - 新增功能
            if divergence_result['has_divergence']:
                report_lines.append(f"{divergence_result['warning_message']}")
                report_lines.append(f"")
                report_lines.append(f"**背离详情**:")
                report_lines.append(f"- 背离类型: {divergence_result['divergence_type']}")
                report_lines.append(f"- 背离强度: {divergence_result['divergence_strength']:.2f}")
                report_lines.append(f"")
            
            # 极端情绪警告 - 需求 7.6
            if composite_score >= 80:
                report_lines.append(f"⚠️ **极端乐观警告**: 市场情绪过于乐观，可能存在回调风险，建议关注反向指标。")
                report_lines.append(f"")
            elif composite_score <= 20:
                report_lines.append(f"⚠️ **极端恐慌警告**: 市场情绪过于悲观，可能存在超跌反弹机会，建议关注反向指标。")
                report_lines.append(f"")
            
            # 组件贡献度分析 - 需求 6.8
            report_lines.append(f"## 情绪组件分析")
            report_lines.append(f"")
            report_lines.append(f"| 组件 | 评分 | 贡献度 |")
            report_lines.append(f"|------|------|--------|")
            
            component_names = {
                'news': '新闻情绪',
                'technical': '技术动量',
                'volume': '成交量',
                'money_flow': '资金流向',
                'volatility': '波动率',
                'social': '社交媒体',
                'margin': '融资融券'
            }
            
            for comp_key, comp_score in components.items():
                comp_name = component_names.get(comp_key, comp_key)
                contribution = breakdown.get(comp_key, 0.0)
                report_lines.append(f"| {comp_name} | {comp_score:.3f} | {contribution:.3f} |")
            
            report_lines.append(f"")
            
            # 核心数据详情
            report_lines.append(f"## 核心情绪数据")
            report_lines.append(f"")
            report_lines.append(f"- **新闻情绪**: {core_data.get('news_sentiment', 0.0):.3f}")
            report_lines.append(f"- **价格动量**: {core_data.get('price_momentum', 0.0):.3f}")
            report_lines.append(f"- **成交量情绪**: {core_data.get('volume_sentiment', 0.0):.3f}")
            report_lines.append(f"")
            
            # 增强数据详情
            if enhanced_data:
                report_lines.append(f"## 增强情绪数据")
                report_lines.append(f"")
                
                if market_info['is_us']:
                    report_lines.append(f"- **VIX恐慌指数**: {enhanced_data.get('vix_sentiment', 0.0):.3f}")
                    report_lines.append(f"- **Reddit情绪**: {enhanced_data.get('reddit_sentiment', 0.0):.3f}")
                elif market_info['is_china']:
                    report_lines.append(f"- **北向资金**: {enhanced_data.get('northbound_flow', 0.0):.3f}")
                    report_lines.append(f"- **波动率情绪**: {enhanced_data.get('volatility_sentiment', 0.0):.3f}")
                    if 'margin_trading' in enhanced_data:
                        report_lines.append(f"- **融资融券**: {enhanced_data.get('margin_trading', 0.0):.3f}")
                elif market_info['is_hk']:
                    report_lines.append(f"- **南向资金**: {enhanced_data.get('southbound_flow', 0.0):.3f}")
                
                report_lines.append(f"")
            
            # 数据源信息 - 需求 7.7
            report_lines.append(f"## 数据源信息")
            report_lines.append(f"")
            report_lines.append(f"- **数据时间戳**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"- **核心数据源**: 新闻API, 价格数据, 成交量数据")
            
            if market_info['is_us']:
                report_lines.append(f"- **增强数据源**: VIX指数, Reddit社交媒体")
            elif market_info['is_china']:
                report_lines.append(f"- **增强数据源**: 北向资金, 波动率, 融资融券")
            elif market_info['is_hk']:
                report_lines.append(f"- **增强数据源**: 南向资金")
            
            # 降级策略使用情况 - 需求 8.3, 8.4
            if fallback_strategy.has_failures():
                report_lines.append(f"")
                report_lines.append(f"⚠️ **数据可用性说明**: 部分数据源不可用，已使用降级策略")
                failures = fallback_strategy.get_failures()
                for failure in failures:
                    # 使用 to_dict() 方法获取字典格式
                    failure_dict = failure.to_dict()
                    report_lines.append(f"  - {failure_dict['component']}: {failure_dict['error']}")
            
            report = "\n".join(report_lines)
            
            logger.info(f"[情绪工具] 情绪数据报告生成完成，长度: {len(report)} 字符")
            
            return report
            
        except Exception as e:
            logger.error(f"[情绪工具] 获取市场情绪数据失败: {e}")
            
            # 降级处理 - 需求 8.5, 8.6
            return f"""# 市场情绪数据获取失败

**股票代码**: {ticker}
**分析日期**: {date}
**市场类型**: {market_type}

## 错误信息

获取市场情绪数据时发生错误: {str(e)}

## 降级评估

- **综合情绪评分**: 50.0 / 100 (中性)
- **情绪等级**: 中性

由于数据源不可用，返回中性评分。建议稍后重试或使用其他分析方法。
"""
    
    # 创建结构化工具
    tool = StructuredTool.from_function(
        func=get_market_sentiment_data,
        name="get_market_sentiment_data",
        description=f"获取{market_info['market_name']}股票的市场情绪数据，包括综合情绪评分、情绪等级和各组件分析。需要提供ticker(股票代码)、date(日期)、market_type(市场类型)三个参数。",
        args_schema=SentimentAnalysisInput
    )
    
    return tool


def create_vix_tool() -> Tool:
    """
    创建VIX恐慌指数工具
    
    Returns:
        VIX工具
    
    需求: 3.1, 3.2, 3.3, 3.4
    """
    
    def get_vix_index(date: str = None) -> str:
        """
        获取VIX恐慌指数
        
        Args:
            date: 日期 (YYYY-MM-DD)，可选，默认为当前日期
        
        Returns:
            VIX指数数据的文本描述
        """
    logger.info(f"[VIX工具] 获取VIX恐慌指数: {date}")
    
    try:
        # 初始化缓存
        cache_manager = get_sentiment_cache()
        
        # 初始化美股增强数据源
        us_source = USEnhancedDataSource(
            cache_manager=cache_manager,
            toolkit=None,
            fallback_strategy=FallbackStrategy()
        )
        
        # 获取VIX数据
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        vix_data = us_source.get_data('VIX', date)
        vix_sentiment = vix_data.get('vix_sentiment', 0.0)
        vix_value = vix_data.get('vix_value', None)
        
        # 生成文本描述
        report_lines = []
        report_lines.append(f"# VIX恐慌指数")
        report_lines.append(f"")
        report_lines.append(f"**查询日期**: {date}")
        report_lines.append(f"")
        
        if vix_value is not None:
            report_lines.append(f"## 当前VIX指数")
            report_lines.append(f"")
            report_lines.append(f"- **VIX值**: {vix_value:.2f}")
            report_lines.append(f"- **情绪评分**: {vix_sentiment:.3f} (-1到1)")
            report_lines.append(f"")
            
            # 解读VIX水平 - 需求 3.2, 3.3, 3.4
            report_lines.append(f"## VIX水平解读")
            report_lines.append(f"")
            
            if vix_value < 15:
                fear_level = "低恐慌"
                interpretation = "市场情绪乐观，投资者信心较强"
            elif vix_value < 25:
                fear_level = "正常波动"
                interpretation = "市场处于正常波动范围"
            elif vix_value < 40:
                fear_level = "高恐慌"
                interpretation = "市场情绪悲观，投资者担忧增加"
            else:
                fear_level = "极度恐慌"
                interpretation = "市场极度恐慌，可能存在系统性风险"
            
            report_lines.append(f"- **恐慌等级**: {fear_level}")
            report_lines.append(f"- **市场解读**: {interpretation}")
            report_lines.append(f"")
            
            # VIX参考标准
            report_lines.append(f"## VIX参考标准")
            report_lines.append(f"")
            report_lines.append(f"| VIX范围 | 恐慌等级 | 市场状态 |")
            report_lines.append(f"|---------|----------|----------|")
            report_lines.append(f"| < 15 | 低恐慌 | 市场乐观 |")
            report_lines.append(f"| 15-25 | 正常 | 正常波动 |")
            report_lines.append(f"| 25-40 | 高恐慌 | 市场悲观 |")
            report_lines.append(f"| > 40 | 极度恐慌 | 系统性风险 |")
            report_lines.append(f"")
        else:
            report_lines.append(f"⚠️ **数据不可用**: 无法获取VIX指数数据")
            report_lines.append(f"")
        
        # 数据源信息
        report_lines.append(f"## 数据源")
        report_lines.append(f"")
        report_lines.append(f"- **数据来源**: Yahoo Finance (^VIX)")
        report_lines.append(f"- **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"")
        
        report = "\n".join(report_lines)
        
        logger.info(f"[VIX工具] VIX数据报告生成完成，长度: {len(report)} 字符")
        
        return report
        
    except Exception as e:
        logger.error(f"[VIX工具] 获取VIX指数失败: {e}")
        
        return f"""# VIX恐慌指数获取失败

**查询日期**: {date}

## 错误信息

获取VIX恐慌指数时发生错误: {str(e)}

VIX指数暂时不可用，建议使用其他波动率指标。
"""
    
    # 创建工具
    tool = Tool(
        name="get_vix_index",
        description="获取VIX恐慌指数，用于评估美股市场的波动率和投资者恐慌程度",
        func=get_vix_index
    )
    
    return tool


def create_capital_flow_tool(market_info: Dict[str, Any]) -> Tool:
    """
    创建资金流向工具
    
    Args:
        market_info: 市场信息字典
    
    Returns:
        资金流向工具
    
    需求: 4.1, 4.2, 4.3, 5.1, 5.2, 5.3
    """
    
    def get_capital_flow(ticker: str, date: str, market_type: str) -> str:
        """
        获取资金流向数据
        
        Args:
            ticker: 股票代码
            date: 日期 (YYYY-MM-DD)
            market_type: 市场类型 (US/CN/HK)
        
        Returns:
            资金流向数据的文本描述
        """
    logger.info(f"[资金流向工具] 获取资金流向: {ticker}, {date}, {market_type}")
    
    try:
        # 初始化缓存和降级策略
        cache_manager = get_sentiment_cache()
        fallback_strategy = FallbackStrategy()
        
        # 根据市场类型选择数据源
        if market_type in ['CN', '中国A股', 'A股']:
            # A股：北向资金 - 需求 4.1, 4.2, 4.3
            logger.info(f"[资金流向工具] 获取A股北向资金数据...")
            
            cn_source = CNEnhancedDataSource(
                cache_manager=cache_manager,
                toolkit=None,
                fallback_strategy=fallback_strategy
            )
            
            capital_data = cn_source.get_data(ticker, date)
            flow_sentiment = capital_data.get('northbound_flow', 0.0)
            flow_value = capital_data.get('northbound_value', None)
            
            # 生成报告
            report_lines = []
            report_lines.append(f"# 北向资金流向")
            report_lines.append(f"")
            report_lines.append(f"**股票代码**: {ticker}")
            report_lines.append(f"**查询日期**: {date}")
            report_lines.append(f"")
            
            if flow_value is not None:
                report_lines.append(f"## 资金流向数据")
                report_lines.append(f"")
                report_lines.append(f"- **净流入金额**: {flow_value:.2f} 亿元")
                report_lines.append(f"- **情绪评分**: {flow_sentiment:.3f} (-1到1)")
                report_lines.append(f"")
                
                # 解读资金流向 - 需求 4.2, 4.3
                report_lines.append(f"## 资金流向解读")
                report_lines.append(f"")
                
                if flow_value > 10:
                    sentiment = "强烈看多"
                    interpretation = "机构资金大量流入，看好后市"
                elif flow_value > 0:
                    sentiment = "温和看多"
                    interpretation = "机构资金小幅流入，谨慎乐观"
                elif flow_value > -10:
                    sentiment = "温和看空"
                    interpretation = "机构资金小幅流出，谨慎悲观"
                else:
                    sentiment = "强烈看空"
                    interpretation = "机构资金大量流出，看空后市"
                
                report_lines.append(f"- **机构情绪**: {sentiment}")
                report_lines.append(f"- **市场解读**: {interpretation}")
                report_lines.append(f"")
                
                # 参考标准
                report_lines.append(f"## 北向资金参考标准")
                report_lines.append(f"")
                report_lines.append(f"| 净流入金额 | 机构情绪 | 市场含义 |")
                report_lines.append(f"|-----------|----------|----------|")
                report_lines.append(f"| > 10亿 | 强烈看多 | 大量流入 |")
                report_lines.append(f"| 0-10亿 | 温和看多 | 小幅流入 |")
                report_lines.append(f"| -10-0亿 | 温和看空 | 小幅流出 |")
                report_lines.append(f"| < -10亿 | 强烈看空 | 大量流出 |")
                report_lines.append(f"")
            else:
                report_lines.append(f"⚠️ **数据不可用**: 无法获取北向资金数据")
                report_lines.append(f"")
            
            # 数据源信息
            report_lines.append(f"## 数据源")
            report_lines.append(f"")
            report_lines.append(f"- **数据来源**: AKShare (沪股通 + 深股通)")
            report_lines.append(f"- **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"")
            
        elif market_type in ['HK', '港股', '香港']:
            # 港股：南向资金 - 需求 5.1, 5.2, 5.3
            logger.info(f"[资金流向工具] 获取港股南向资金数据...")
            
            hk_source = HKEnhancedDataSource(
                cache_manager=cache_manager,
                toolkit=None,
                fallback_strategy=fallback_strategy
            )
            
            capital_data = hk_source.get_data(ticker, date)
            flow_sentiment = capital_data.get('southbound_flow', 0.0)
            flow_value = capital_data.get('southbound_value', None)
            
            # 生成报告
            report_lines = []
            report_lines.append(f"# 南向资金流向")
            report_lines.append(f"")
            report_lines.append(f"**股票代码**: {ticker}")
            report_lines.append(f"**查询日期**: {date}")
            report_lines.append(f"")
            
            if flow_value is not None:
                report_lines.append(f"## 资金流向数据")
                report_lines.append(f"")
                report_lines.append(f"- **净流入金额**: {flow_value:.2f} 亿港元")
                report_lines.append(f"- **情绪评分**: {flow_sentiment:.3f} (-1到1)")
                report_lines.append(f"")
                
                # 解读资金流向 - 需求 5.2, 5.3
                report_lines.append(f"## 资金流向解读")
                report_lines.append(f"")
                
                if flow_value > 5:
                    sentiment = "内地资金看多"
                    interpretation = "内地资金大量流入，看好港股"
                elif flow_value > 0:
                    sentiment = "温和流入"
                    interpretation = "内地资金小幅流入"
                elif flow_value > -5:
                    sentiment = "温和流出"
                    interpretation = "内地资金小幅流出"
                else:
                    sentiment = "内地资金看空"
                    interpretation = "内地资金大量流出，看空港股"
                
                report_lines.append(f"- **内地投资者情绪**: {sentiment}")
                report_lines.append(f"- **市场解读**: {interpretation}")
                report_lines.append(f"")
                
                # 参考标准
                report_lines.append(f"## 南向资金参考标准")
                report_lines.append(f"")
                report_lines.append(f"| 净流入金额 | 投资者情绪 | 市场含义 |")
                report_lines.append(f"|-----------|------------|----------|")
                report_lines.append(f"| > 5亿港元 | 看多 | 大量流入 |")
                report_lines.append(f"| 0-5亿 | 温和流入 | 小幅流入 |")
                report_lines.append(f"| -5-0亿 | 温和流出 | 小幅流出 |")
                report_lines.append(f"| < -5亿 | 看空 | 大量流出 |")
                report_lines.append(f"")
            else:
                report_lines.append(f"⚠️ **数据不可用**: 无法获取南向资金数据")
                report_lines.append(f"")
            
            # 数据源信息
            report_lines.append(f"## 数据源")
            report_lines.append(f"")
            report_lines.append(f"- **数据来源**: AKShare (港股通沪 + 港股通深)")
            report_lines.append(f"- **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"")
            
        else:
            # 美股：暂不支持资金流向
            report_lines = []
            report_lines.append(f"# 资金流向数据")
            report_lines.append(f"")
            report_lines.append(f"**股票代码**: {ticker}")
            report_lines.append(f"**市场类型**: {market_type}")
            report_lines.append(f"")
            report_lines.append(f"⚠️ **暂不支持**: 美股市场暂不支持资金流向分析")
            report_lines.append(f"")
            report_lines.append(f"建议使用VIX指数和社交媒体情绪作为替代指标。")
            report_lines.append(f"")
        
        report = "\n".join(report_lines)
        
        logger.info(f"[资金流向工具] 资金流向报告生成完成，长度: {len(report)} 字符")
        
        return report
        
    except Exception as e:
        logger.error(f"[资金流向工具] 获取资金流向失败: {e}")
        
        return f"""# 资金流向数据获取失败

**股票代码**: {ticker}
**查询日期**: {date}
**市场类型**: {market_type}

## 错误信息

获取资金流向数据时发生错误: {str(e)}

资金流向数据暂时不可用。
"""
    
    # 创建工具
    tool = Tool(
        name="get_capital_flow",
        description=f"获取{market_info['market_name']}股票的资金流向数据，包括北向资金（A股）或南向资金（港股）的净流入情况",
        func=get_capital_flow
    )
    
    return tool
