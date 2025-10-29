"""
市场热度计算器模块

该模块实现市场热度的量化评估，用于动态调整风险控制策略。
在市场热度高时，适当放宽风险控制；在市场冷淡时，收紧风险控制。

市场热度指标包括：
1. 成交量放大倍数（相对于20日均量）
2. 涨停/跌停家数比例
3. 换手率水平
4. 市场宽度（上涨股票占比）
5. 波动率水平
6. 资金流入强度
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MarketHeatCalculator:
    """
    市场热度计算器
    
    通过多维度指标量化市场热度，生成0-100的热度评分。
    热度评分用于动态调整风险控制参数。
    """
    
    # 热度组件权重配置
    HEAT_WEIGHTS = {
        'volume_ratio': 0.25,      # 成交量放大倍数权重
        'limit_up_ratio': 0.20,    # 涨停家数比例权重
        'turnover_rate': 0.20,     # 换手率权重
        'market_breadth': 0.15,    # 市场宽度权重
        'volatility': 0.10,        # 波动率权重
        'money_flow': 0.10         # 资金流向权重
    }
    
    # 热度等级阈值
    HEAT_LEVELS = {
        'ice_cold': (0, 20),       # 极冷：市场极度低迷
        'cold': (20, 40),          # 冷淡：市场交投清淡
        'normal': (40, 60),        # 正常：市场平稳运行
        'hot': (60, 80),           # 火热：市场活跃
        'boiling': (80, 100)       # 沸腾：市场极度狂热
    }
    
    # 风险控制调整系数（基于市场热度）
    RISK_ADJUSTMENT = {
        'ice_cold': {
            'position_multiplier': 0.5,      # 仓位降低50%
            'stop_loss_tightness': 1.5,      # 止损收紧50%
            'risk_rounds': 1                 # 风险辩论轮次：1轮（更保守）
        },
        'cold': {
            'position_multiplier': 0.7,
            'stop_loss_tightness': 1.2,
            'risk_rounds': 1
        },
        'normal': {
            'position_multiplier': 1.0,      # 标准仓位
            'stop_loss_tightness': 1.0,      # 标准止损
            'risk_rounds': 1                 # 标准1轮辩论
        },
        'hot': {
            'position_multiplier': 1.3,      # 仓位提高30%
            'stop_loss_tightness': 0.8,      # 止损放宽20%
            'risk_rounds': 2                 # 增加到2轮辩论（更充分讨论）
        },
        'boiling': {
            'position_multiplier': 1.5,      # 仓位提高50%
            'stop_loss_tightness': 0.7,      # 止损放宽30%
            'risk_rounds': 2                 # 2轮辩论
        }
    }
    
    @staticmethod
    def calculate_market_heat(
        volume_ratio: float = 1.0,
        limit_up_ratio: float = 0.0,
        turnover_rate: float = 0.0,
        market_breadth: float = 0.5,
        volatility: float = 0.0,
        money_flow: float = 0.0,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        计算市场热度评分
        
        Args:
            volume_ratio: 成交量放大倍数（相对于20日均量），范围 0.0-5.0+
                         1.0 = 正常水平，2.0 = 放大2倍，0.5 = 萎缩50%
            limit_up_ratio: 涨停家数占比，范围 0.0-1.0
                           0.1 = 10%股票涨停（极热），0.01 = 1%涨停（正常）
            turnover_rate: 换手率，范围 0.0-20.0+
                          5% = 正常，10% = 活跃，20%+ = 极度活跃
            market_breadth: 市场宽度（上涨股票占比），范围 0.0-1.0
                           0.7 = 70%股票上涨（强势），0.3 = 30%上涨（弱势）
            volatility: 波动率，范围 0.0-10.0+
                       2% = 正常，5% = 高波动，10%+ = 极端波动
            money_flow: 资金流向（净流入/总成交额），范围 -1.0 到 1.0
                       0.5 = 大量净流入，-0.5 = 大量净流出
            weights: 可选的自定义权重配置
        
        Returns:
            {
                'heat_score': float,              # 0-100的热度评分
                'heat_level': str,                # 热度等级
                'components': Dict[str, float],   # 各组件标准化评分
                'risk_adjustment': Dict,          # 风险控制调整参数
                'recommendation': str             # 策略建议
            }
        """
        # 使用默认权重或自定义权重
        weights_to_use = weights if weights is not None else MarketHeatCalculator.HEAT_WEIGHTS
        
        # 标准化各组件到0-1范围
        components = {
            'volume_ratio': MarketHeatCalculator._normalize_volume_ratio(volume_ratio),
            'limit_up_ratio': MarketHeatCalculator._normalize_limit_up_ratio(limit_up_ratio),
            'turnover_rate': MarketHeatCalculator._normalize_turnover_rate(turnover_rate),
            'market_breadth': market_breadth,  # 已经是0-1范围
            'volatility': MarketHeatCalculator._normalize_volatility(volatility),
            'money_flow': MarketHeatCalculator._normalize_money_flow(money_flow)
        }
        
        # 计算加权平均热度评分
        weighted_sum = 0.0
        total_weight = 0.0
        
        for component_name, score in components.items():
            weight = weights_to_use.get(component_name, 0.0)
            if weight > 0:
                weighted_sum += score * weight
                total_weight += weight
                
                logger.debug(
                    f"热度组件 '{component_name}': 评分={score:.3f}, "
                    f"权重={weight:.2f}, 贡献={score * weight:.3f}"
                )
        
        if total_weight == 0:
            raise ValueError("没有有效的热度组件权重")
        
        # 计算热度评分（0-1转换为0-100）
        raw_heat = weighted_sum / total_weight
        heat_score = raw_heat * 100
        
        # 获取热度等级
        heat_level = MarketHeatCalculator.get_heat_level(heat_score)
        
        # 获取风险控制调整参数
        risk_adjustment = MarketHeatCalculator.RISK_ADJUSTMENT[heat_level]
        
        # 生成策略建议
        recommendation = MarketHeatCalculator._generate_recommendation(
            heat_level, heat_score, components
        )
        
        logger.info(
            f"市场热度评估完成: 热度评分={heat_score:.1f}, "
            f"等级={heat_level}, 风险辩论轮次={risk_adjustment['risk_rounds']}"
        )
        
        return {
            'heat_score': round(heat_score, 2),
            'heat_level': heat_level,
            'heat_level_cn': MarketHeatCalculator._get_heat_level_cn(heat_level),
            'components': {k: round(v, 3) for k, v in components.items()},
            'risk_adjustment': risk_adjustment,
            'recommendation': recommendation,
            'raw_inputs': {
                'volume_ratio': volume_ratio,
                'limit_up_ratio': limit_up_ratio,
                'turnover_rate': turnover_rate,
                'market_breadth': market_breadth,
                'volatility': volatility,
                'money_flow': money_flow
            }
        }
    
    @staticmethod
    def _normalize_volume_ratio(ratio: float) -> float:
        """
        标准化成交量放大倍数到0-1范围
        
        0.5倍 -> 0.0（极度萎缩）
        1.0倍 -> 0.4（正常，提高基准）
        1.5倍 -> 0.6（偏活跃）
        2.0倍 -> 0.75（活跃）
        3.0倍+ -> 1.0（极度活跃）
        """
        if ratio <= 0.5:
            return 0.0
        elif ratio <= 1.0:
            # 0.5-1.0 映射到 0.0-0.4
            return (ratio - 0.5) * 0.8
        elif ratio >= 3.0:
            return 1.0
        else:
            # 1.0-3.0 映射到 0.4-1.0
            return 0.4 + (ratio - 1.0) * 0.3
    
    @staticmethod
    def _normalize_limit_up_ratio(ratio: float) -> float:
        """
        标准化涨停家数占比到0-1范围
        
        0% -> 0.0
        1% -> 0.2（正常偏低）
        2.5% -> 0.5（正常）
        5% -> 0.75（活跃）
        10%+ -> 1.0（极度狂热）
        """
        if ratio <= 0:
            return 0.0
        elif ratio >= 0.10:
            return 1.0
        elif ratio <= 0.025:
            # 0-2.5% 映射到 0.0-0.5
            return ratio / 0.05
        else:
            # 2.5%-10% 映射到 0.5-1.0
            return 0.5 + (ratio - 0.025) * (0.5 / 0.075)
    
    @staticmethod
    def _normalize_turnover_rate(rate: float) -> float:
        """
        标准化换手率到0-1范围
        
        0% -> 0.0
        5% -> 0.4（正常偏低）
        8% -> 0.55（正常）
        12% -> 0.75（活跃）
        20%+ -> 1.0（极度活跃）
        """
        if rate <= 0:
            return 0.0
        elif rate >= 20.0:
            return 1.0
        elif rate <= 8.0:
            # 0-8% 映射到 0.0-0.55
            return rate * 0.06875
        else:
            # 8%-20% 映射到 0.55-1.0
            return 0.55 + (rate - 8.0) * (0.45 / 12.0)
    
    @staticmethod
    def _normalize_volatility(volatility: float) -> float:
        """
        标准化波动率到0-1范围
        
        0% -> 0.0
        2% -> 0.3（正常偏低）
        3.5% -> 0.5（正常）
        5% -> 0.65（高波动）
        10%+ -> 1.0（极端波动）
        """
        if volatility <= 0:
            return 0.0
        elif volatility >= 10.0:
            return 1.0
        elif volatility <= 3.5:
            # 0-3.5% 映射到 0.0-0.5
            return volatility * (0.5 / 3.5)
        else:
            # 3.5%-10% 映射到 0.5-1.0
            return 0.5 + (volatility - 3.5) * (0.5 / 6.5)
    
    @staticmethod
    def _normalize_money_flow(flow: float) -> float:
        """
        标准化资金流向到0-1范围
        
        -1.0 -> 0.0（大量流出）
        0.0 -> 0.5（平衡）
        1.0 -> 1.0（大量流入）
        """
        return (flow + 1.0) / 2.0
    
    @staticmethod
    def get_heat_level(score: float) -> str:
        """
        根据评分返回热度等级
        
        Args:
            score: 热度评分，范围 0 到 100
        
        Returns:
            热度等级字符串
        """
        if score >= 80:
            return 'boiling'
        elif score >= 60:
            return 'hot'
        elif score >= 40:
            return 'normal'
        elif score >= 20:
            return 'cold'
        else:
            return 'ice_cold'
    
    @staticmethod
    def _get_heat_level_cn(level: str) -> str:
        """获取热度等级的中文名称"""
        level_map = {
            'ice_cold': '极冷',
            'cold': '冷淡',
            'normal': '正常',
            'hot': '火热',
            'boiling': '沸腾'
        }
        return level_map.get(level, '未知')
    
    @staticmethod
    def _generate_recommendation(
        heat_level: str,
        heat_score: float,
        components: Dict[str, float]
    ) -> str:
        """
        生成策略建议
        
        Args:
            heat_level: 热度等级
            heat_score: 热度评分
            components: 各组件评分
        
        Returns:
            策略建议文本
        """
        recommendations = {
            'ice_cold': (
                f"🥶 市场极度冷淡（热度：{heat_score:.1f}）\n"
                "建议：\n"
                "- 大幅降低仓位至50%以下\n"
                "- 收紧止损，快速止损\n"
                "- 避免追涨，等待市场转暖信号\n"
                "- 风险控制采用保守策略（1轮辩论）"
            ),
            'cold': (
                f"❄️ 市场交投清淡（热度：{heat_score:.1f}）\n"
                "建议：\n"
                "- 降低仓位至70%左右\n"
                "- 适当收紧止损\n"
                "- 谨慎操作，关注市场情绪变化\n"
                "- 风险控制采用保守策略（1轮辩论）"
            ),
            'normal': (
                f"😐 市场平稳运行（热度：{heat_score:.1f}）\n"
                "建议：\n"
                "- 保持标准仓位配置\n"
                "- 使用标准止损策略\n"
                "- 按常规策略操作\n"
                "- 风险控制采用标准策略（1轮辩论）"
            ),
            'hot': (
                f"🔥 市场活跃火热（热度：{heat_score:.1f}）\n"
                "建议：\n"
                "- 可适当提高仓位至130%（使用杠杆）\n"
                "- 适当放宽止损空间，给予更多波动容忍度\n"
                "- 积极把握热点机会\n"
                "- 风险控制采用积极策略（2轮辩论，充分讨论）"
            ),
            'boiling': (
                f"🌋 市场极度狂热（热度：{heat_score:.1f}）\n"
                "建议：\n"
                "- 可大幅提高仓位至150%（谨慎使用杠杆）\n"
                "- 放宽止损空间，但注意风险\n"
                "- 把握趋势机会，但警惕过热风险\n"
                "- 风险控制采用积极策略（2轮辩论，充分讨论）\n"
                "⚠️ 警告：市场可能过热，注意随时准备获利了结"
            )
        }
        
        base_recommendation = recommendations.get(heat_level, "")
        
        # 添加关键组件分析
        key_drivers = []
        if components['volume_ratio'] > 0.7:
            key_drivers.append("成交量大幅放大")
        if components['limit_up_ratio'] > 0.5:
            key_drivers.append("涨停家数众多")
        if components['market_breadth'] > 0.7:
            key_drivers.append("市场普涨")
        if components['money_flow'] > 0.7:
            key_drivers.append("资金大量流入")
        
        if key_drivers:
            base_recommendation += f"\n\n关键驱动因素：{', '.join(key_drivers)}"
        
        return base_recommendation
    
    @staticmethod
    def get_risk_rounds(heat_score: float) -> int:
        """
        根据市场热度获取建议的风险辩论轮次
        
        Args:
            heat_score: 市场热度评分 0-100
        
        Returns:
            建议的风险辩论轮次（1或2）
        """
        heat_level = MarketHeatCalculator.get_heat_level(heat_score)
        return MarketHeatCalculator.RISK_ADJUSTMENT[heat_level]['risk_rounds']
    
    @staticmethod
    def adjust_position_size(
        base_position: float,
        heat_score: float
    ) -> float:
        """
        根据市场热度调整仓位大小
        
        Args:
            base_position: 基础仓位（例如 0.3 表示30%）
            heat_score: 市场热度评分 0-100
        
        Returns:
            调整后的仓位
        """
        heat_level = MarketHeatCalculator.get_heat_level(heat_score)
        multiplier = MarketHeatCalculator.RISK_ADJUSTMENT[heat_level]['position_multiplier']
        adjusted_position = base_position * multiplier
        
        logger.info(
            f"仓位调整: 基础={base_position:.1%}, "
            f"热度={heat_score:.1f}, 倍数={multiplier:.2f}, "
            f"调整后={adjusted_position:.1%}"
        )
        
        return adjusted_position
    
    @staticmethod
    def adjust_stop_loss(
        base_stop_loss: float,
        heat_score: float
    ) -> float:
        """
        根据市场热度调整止损幅度
        
        Args:
            base_stop_loss: 基础止损幅度（例如 0.05 表示5%）
            heat_score: 市场热度评分 0-100
        
        Returns:
            调整后的止损幅度
        """
        heat_level = MarketHeatCalculator.get_heat_level(heat_score)
        tightness = MarketHeatCalculator.RISK_ADJUSTMENT[heat_level]['stop_loss_tightness']
        adjusted_stop_loss = base_stop_loss * tightness
        
        logger.info(
            f"止损调整: 基础={base_stop_loss:.1%}, "
            f"热度={heat_score:.1f}, 收紧系数={tightness:.2f}, "
            f"调整后={adjusted_stop_loss:.1%}"
        )
        
        return adjusted_stop_loss
