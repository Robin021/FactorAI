"""
市场热度评估节点

该节点在分析流程开始时评估市场热度，并将结果存入state中，
供后续的风险控制逻辑使用。
"""

from typing import Dict, Any
from tradingagents.dataflows.market_heat_data import MarketHeatDataSource
from tradingagents.agents.utils.market_heat_calculator import MarketHeatCalculator

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def create_market_heat_evaluator():
    """
    创建市场热度评估节点
    
    该节点会：
    1. 获取实时市场数据
    2. 计算市场热度评分
    3. 将结果存入state供后续使用
    """
    
    def market_heat_node(state) -> Dict[str, Any]:
        """
        市场热度评估节点
        
        Args:
            state: 当前状态
        
        Returns:
            更新后的状态，包含市场热度信息
        """
        # 进度回调：市场热度评估开始
        try:
            callback = state.get("progress_callback")
            if callable(callback):
                callback("🌡️ 市场热度评估：开始获取市场数据", 0)
        except Exception:
            pass
        
        try:
            # 获取交易日期（如果有的话）
            trade_date = state.get("trade_date")
            if trade_date:
                # 转换日期格式 YYYY-MM-DD
                logger.info(f"📅 使用指定交易日期: {trade_date}")
            else:
                trade_date = None
                logger.info(f"📅 使用当前日期")
            
            # 步骤1：获取市场数据
            logger.info("🔍 开始获取市场整体数据...")
            market_data = MarketHeatDataSource.get_market_overview(trade_date)
            
            logger.info(
                f"✅ 市场数据获取成功: "
                f"涨停={market_data['stats']['limit_up_count']}家, "
                f"上涨={market_data['stats']['up_count']}家, "
                f"换手率={market_data['turnover_rate']:.2f}%"
            )
            
            # 进度回调：计算市场热度
            try:
                if callable(callback):
                    callback("🌡️ 市场热度评估：计算热度评分", 0)
            except Exception:
                pass
            
            # 步骤2：计算市场热度
            logger.info("🌡️ 开始计算市场热度...")
            heat_result = MarketHeatCalculator.calculate_market_heat(
                volume_ratio=market_data['volume_ratio'],
                limit_up_ratio=market_data['limit_up_ratio'],
                turnover_rate=market_data['turnover_rate'],
                market_breadth=market_data['market_breadth'],
                volatility=market_data['volatility'],
                money_flow=market_data['money_flow']
            )
            
            logger.info(
                f"✅ 市场热度评估完成: "
                f"评分={heat_result['heat_score']:.1f}, "
                f"等级={heat_result['heat_level_cn']}, "
                f"风险辩论轮次={heat_result['risk_adjustment']['risk_rounds']}轮"
            )
            
            # 进度回调：市场热度评估完成
            try:
                if callable(callback):
                    callback(
                        f"🌡️ 市场热度评估：{heat_result['heat_level_cn']}（{heat_result['heat_score']:.1f}分）",
                        0
                    )
            except Exception:
                pass
            
            # 返回更新后的状态
            return {
                "market_heat_score": heat_result['heat_score'],
                "market_heat_level": heat_result['heat_level_cn'],
                "market_heat_data": {
                    'raw_data': market_data,
                    'heat_result': heat_result,
                    'recommendation': heat_result['recommendation'],
                    'risk_adjustment': heat_result['risk_adjustment']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 市场热度评估失败: {e}")
            logger.warning("⚠️ 使用默认市场热度（正常市场）")
            
            # 进度回调：使用默认值
            try:
                if callable(callback):
                    callback("🌡️ 市场热度评估：使用默认值（正常市场）", 0)
            except Exception:
                pass
            
            # 返回默认值（正常市场）
            return {
                "market_heat_score": 50.0,
                "market_heat_level": "正常",
                "market_heat_data": {
                    'raw_data': {},
                    'heat_result': {
                        'heat_score': 50.0,
                        'heat_level': 'normal',
                        'heat_level_cn': '正常',
                        'risk_adjustment': {
                            'position_multiplier': 1.0,
                            'stop_loss_tightness': 1.0,
                            'risk_rounds': 1
                        }
                    },
                    'recommendation': '市场数据获取失败，使用标准风险控制策略',
                    'risk_adjustment': {
                        'position_multiplier': 1.0,
                        'stop_loss_tightness': 1.0,
                        'risk_rounds': 1
                    }
                }
            }
    
    return market_heat_node


def get_market_heat_summary(state) -> str:
    """
    从state中获取市场热度摘要（用于报告生成）
    
    Args:
        state: 当前状态
    
    Returns:
        市场热度摘要文本
    """
    if "market_heat_data" not in state:
        return "市场热度数据不可用"
    
    heat_data = state["market_heat_data"]
    heat_result = heat_data.get("heat_result", {})
    raw_data = heat_data.get("raw_data", {})
    
    if not heat_result:
        return "市场热度数据不可用"
    
    summary = f"""
## 🌡️ 市场热度分析

### 热度评分
- **评分**: {heat_result.get('heat_score', 0):.1f} / 100
- **等级**: {heat_result.get('heat_level_cn', '未知')}

### 市场数据
"""
    
    if raw_data and 'stats' in raw_data:
        stats = raw_data['stats']
        summary += f"""
- 涨停家数: {stats.get('limit_up_count', 0)}家 ({raw_data.get('limit_up_ratio', 0):.2%})
- 上涨家数: {stats.get('up_count', 0)}家 ({raw_data.get('market_breadth', 0):.2%})
- 下跌家数: {stats.get('down_count', 0)}家
- 平均换手率: {raw_data.get('turnover_rate', 0):.2f}%
- 成交量放大: {raw_data.get('volume_ratio', 1.0):.2f}倍
- 市场波动率: {raw_data.get('volatility', 0):.2f}%
"""
    
    # 添加风险控制建议
    risk_adj = heat_result.get('risk_adjustment', {})
    summary += f"""
### 风险控制调整
- 仓位倍数: {risk_adj.get('position_multiplier', 1.0):.2f}x
- 止损收紧系数: {risk_adj.get('stop_loss_tightness', 1.0):.2f}x
- 风险辩论轮次: {risk_adj.get('risk_rounds', 1)}轮

### 策略建议
{heat_data.get('recommendation', '无建议')}
"""
    
    return summary.strip()
