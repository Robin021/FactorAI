"""
情绪评分计算器模块

该模块实现市场情绪分析的核心计算逻辑，包括：
- 综合情绪评分计算（加权平均）
- 评分归一化（-1到1转换为0-100）
- 情绪等级分类（极度恐慌/悲观/中性/乐观/极度乐观）
- 组件贡献度分析

需求: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SentimentCalculator:
    """
    情绪评分计算器
    
    实现市场情绪的量化评估，通过加权平均多个情绪组件，
    生成0-100的综合情绪评分和对应的情绪等级。
    
    权重配置（需求 6.2）:
    - 新闻情绪: 25%
    - 资金流向: 25%
    - 波动率: 20%
    - 技术动量: 20%
    - 社交媒体: 10%
    """
    
    # 组件权重配置（需求 6.2）
    # 更新: 添加volume和margin组件，重新平衡权重以防止新闻过度影响
    WEIGHTS = {
        'news': 0.20,           # 新闻情绪权重 (降低从25%到20%)
        'money_flow': 0.20,     # 资金流向权重 (降低从25%到20%)
        'volatility': 0.15,     # 波动率权重 (降低从20%到15%)
        'technical': 0.20,      # 技术动量权重 (保持20%)
        'volume': 0.15,         # 成交量情绪权重 (新增15%)
        'social': 0.05,         # 社交媒体权重 (降低从10%到5%)
        'margin': 0.05          # 融资融券权重 (新增5%)
    }
    
    # 情绪等级阈值（需求 6.3-6.7）
    SENTIMENT_LEVELS = {
        'extreme_fear': (0, 20),      # 极度恐慌
        'fear': (20, 40),             # 悲观
        'neutral': (40, 60),          # 中性
        'greed': (60, 80),            # 乐观
        'extreme_greed': (80, 100)    # 极度乐观
    }
    
    @staticmethod
    def calculate_composite_score(
        components: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        计算综合情绪评分（需求 6.1, 6.2, 6.9）
        
        使用加权平均算法计算综合情绪评分。每个组件的评分范围为-1到1，
        通过归一化转换为0-100的最终评分。
        
        Args:
            components: 各组件评分字典 {component_name: score}
                       score范围: -1.0 到 1.0
                       支持的组件: news, money_flow, volatility, technical, social
            weights: 可选的自定义权重配置，如果不提供则使用默认权重
        
        Returns:
            {
                'score': float,              # 0-100的综合评分
                'level': str,                # 情绪等级
                'breakdown': Dict[str, float] # 各组件贡献度
            }
        
        Raises:
            ValueError: 当组件评分超出范围或没有有效组件时
        
        Example:
            >>> calculator = SentimentCalculator()
            >>> components = {
            ...     'news': 0.5,
            ...     'money_flow': 0.3,
            ...     'volatility': -0.2,
            ...     'technical': 0.4,
            ...     'social': 0.1
            ... }
            >>> result = calculator.calculate_composite_score(components)
            >>> print(result['score'])  # 输出: 62.5
            >>> print(result['level'])  # 输出: 乐观
        """
        if not components:
            raise ValueError("组件字典不能为空")
        
        # 使用默认权重或自定义权重
        weights_to_use = weights if weights is not None else SentimentCalculator.WEIGHTS
        
        # 验证组件评分范围（需求 6.9）
        for component_name, score in components.items():
            if not isinstance(score, (int, float)):
                raise ValueError(f"组件 '{component_name}' 的评分必须是数值类型")
            if not -1.0 <= score <= 1.0:
                raise ValueError(
                    f"组件 '{component_name}' 的评分 {score} 超出范围 [-1.0, 1.0]"
                )
        
        # 计算加权平均（需求 6.2）
        weighted_sum = 0.0
        total_weight = 0.0
        breakdown = {}
        
        for component_name, score in components.items():
            weight = weights_to_use.get(component_name, 0.0)
            if weight > 0:
                contribution = score * weight
                weighted_sum += contribution
                total_weight += weight
                breakdown[component_name] = contribution
                
                logger.debug(
                    f"组件 '{component_name}': 评分={score:.3f}, "
                    f"权重={weight:.2f}, 贡献={contribution:.3f}"
                )
        
        if total_weight == 0:
            raise ValueError("没有有效的组件权重")
        
        # 计算加权平均评分（-1 到 1）
        raw_score = weighted_sum / total_weight
        
        # 归一化到 0-100（需求 6.1）
        normalized_score = SentimentCalculator.normalize_score(raw_score)
        
        # 获取情绪等级
        sentiment_level = SentimentCalculator.get_sentiment_level(normalized_score)
        
        logger.info(
            f"综合情绪评分计算完成: 原始评分={raw_score:.3f}, "
            f"归一化评分={normalized_score:.1f}, 等级={sentiment_level}"
        )
        
        return {
            'score': round(normalized_score, 2),
            'level': sentiment_level,
            'breakdown': {k: round(v, 3) for k, v in breakdown.items()},
            'raw_score': round(raw_score, 3),
            'total_weight': round(total_weight, 2)
        }
    
    @staticmethod
    def normalize_score(raw_score: float) -> float:
        """
        将评分归一化到0-100范围（需求 6.1）
        
        将-1到1的原始评分线性转换为0-100的标准化评分。
        
        Args:
            raw_score: 原始评分，范围 -1.0 到 1.0
        
        Returns:
            归一化后的评分，范围 0 到 100
        
        Example:
            >>> SentimentCalculator.normalize_score(-1.0)
            0.0
            >>> SentimentCalculator.normalize_score(0.0)
            50.0
            >>> SentimentCalculator.normalize_score(1.0)
            100.0
        """
        # 线性转换: score = (raw_score + 1) * 50
        # -1 -> 0, 0 -> 50, 1 -> 100
        normalized = (raw_score + 1) * 50
        
        # 确保结果在有效范围内（处理浮点数精度问题）
        return max(0.0, min(100.0, normalized))
    
    @staticmethod
    def get_sentiment_level(score: float) -> str:
        """
        根据评分返回情绪等级（需求 6.3, 6.4, 6.5, 6.6, 6.7）
        
        将0-100的评分映射到五个情绪等级：
        - [80, 100]: 极度乐观
        - [60, 80): 乐观
        - [40, 60): 中性
        - [20, 40): 悲观
        - [0, 20): 极度恐慌
        
        Args:
            score: 情绪评分，范围 0 到 100
        
        Returns:
            情绪等级字符串
        
        Example:
            >>> SentimentCalculator.get_sentiment_level(85)
            '极度乐观'
            >>> SentimentCalculator.get_sentiment_level(50)
            '中性'
            >>> SentimentCalculator.get_sentiment_level(15)
            '极度恐慌'
        """
        if score >= 80:
            return '极度乐观'  # 需求 6.3
        elif score >= 60:
            return '乐观'      # 需求 6.4
        elif score >= 40:
            return '中性'      # 需求 6.5
        elif score >= 20:
            return '悲观'      # 需求 6.6
        else:
            return '极度恐慌'  # 需求 6.7
    
    @staticmethod
    def calculate_breakdown(
        components: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        计算各组件对最终评分的贡献度（需求 6.8）
        
        分析每个情绪组件对综合评分的具体贡献，包括：
        - 绝对贡献值（考虑权重后的评分）
        - 相对贡献百分比
        - 组件重要性排序
        
        Args:
            components: 各组件评分字典 {component_name: score}
            weights: 可选的自定义权重配置
        
        Returns:
            {
                'contributions': Dict[str, float],      # 绝对贡献值
                'percentages': Dict[str, float],        # 相对贡献百分比
                'ranked_components': List[Tuple],       # 按贡献度排序的组件
                'dominant_component': str,              # 主导组件
                'visualization_data': Dict              # 可视化数据
            }
        
        Example:
            >>> calculator = SentimentCalculator()
            >>> components = {'news': 0.5, 'money_flow': 0.3}
            >>> breakdown = calculator.calculate_breakdown(components)
            >>> print(breakdown['dominant_component'])  # 输出: news
        """
        if not components:
            raise ValueError("组件字典不能为空")
        
        weights_to_use = weights if weights is not None else SentimentCalculator.WEIGHTS
        
        # 计算每个组件的绝对贡献
        contributions = {}
        total_contribution = 0.0
        
        for component_name, score in components.items():
            weight = weights_to_use.get(component_name, 0.0)
            if weight > 0:
                # 贡献 = 评分 * 权重
                contribution = score * weight
                contributions[component_name] = contribution
                total_contribution += abs(contribution)
        
        if total_contribution == 0:
            # 所有组件评分都为0的情况
            percentages = {k: 0.0 for k in contributions.keys()}
        else:
            # 计算相对贡献百分比
            percentages = {
                k: (abs(v) / total_contribution) * 100
                for k, v in contributions.items()
            }
        
        # 按贡献度排序（按绝对值）
        ranked_components = sorted(
            contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        # 确定主导组件
        dominant_component = ranked_components[0][0] if ranked_components else None
        
        # 生成可视化数据
        visualization_data = {
            'labels': list(contributions.keys()),
            'values': [contributions[k] for k in contributions.keys()],
            'percentages': [percentages[k] for k in contributions.keys()],
            'colors': SentimentCalculator._get_component_colors(contributions)
        }
        
        logger.info(
            f"组件贡献度分析完成: 主导组件={dominant_component}, "
            f"贡献度={percentages.get(dominant_component, 0):.1f}%"
        )
        
        return {
            'contributions': {k: round(v, 3) for k, v in contributions.items()},
            'percentages': {k: round(v, 2) for k, v in percentages.items()},
            'ranked_components': [(k, round(v, 3)) for k, v in ranked_components],
            'dominant_component': dominant_component,
            'visualization_data': visualization_data
        }
    
    @staticmethod
    def _get_component_colors(contributions: Dict[str, float]) -> Dict[str, str]:
        """
        为组件分配颜色（用于可视化）
        
        根据组件的贡献值（正负）分配颜色：
        - 正贡献: 绿色系（乐观）
        - 负贡献: 红色系（悲观）
        - 零贡献: 灰色（中性）
        """
        colors = {}
        for component_name, contribution in contributions.items():
            if contribution > 0.1:
                colors[component_name] = '#10b981'  # 绿色（乐观）
            elif contribution < -0.1:
                colors[component_name] = '#ef4444'  # 红色（悲观）
            else:
                colors[component_name] = '#6b7280'  # 灰色（中性）
        return colors
    
    @staticmethod
    def detect_divergence(components: Dict[str, float]) -> Dict[str, Any]:
        """
        检测新闻与价格/成交量的背离
        
        当新闻情绪与市场行为（价格、成交量）出现显著背离时，
        这通常是一个警告信号，表明市场可能不认同新闻的乐观/悲观情绪。
        
        Args:
            components: 组件评分字典
        
        Returns:
            {
                'has_divergence': bool,           # 是否存在背离
                'divergence_type': str,           # 背离类型
                'divergence_strength': float,     # 背离强度 (0-1)
                'warning_message': str,           # 警告信息
                'adjustment_factor': float        # 建议调整系数 (0.7-1.0)
            }
        
        Example:
            >>> components = {'news': 1.0, 'technical': -0.3, 'volume': -0.1}
            >>> result = SentimentCalculator.detect_divergence(components)
            >>> print(result['divergence_type'])  # 输出: 'sell_the_news'
        """
        news = components.get('news', 0.0)
        technical = components.get('technical', 0.0)
        volume = components.get('volume', 0.0)
        
        # 初始化结果
        result = {
            'has_divergence': False,
            'divergence_type': 'none',
            'divergence_strength': 0.0,
            'warning_message': '',
            'adjustment_factor': 1.0
        }
        
        # 检测"卖出新闻"模式：新闻乐观但价格/成交量悲观
        if news > 0.5 and technical < -0.1:
            divergence_strength = min(1.0, abs(news - technical))
            
            # 如果成交量也是负面的，背离更强
            if volume < 0:
                divergence_strength = min(1.0, divergence_strength * 1.2)
            
            result['has_divergence'] = True
            result['divergence_type'] = 'sell_the_news'
            result['divergence_strength'] = divergence_strength
            result['warning_message'] = (
                f"⚠️ 背离警告：新闻情绪极度乐观({news:.2f})，但价格走势疲软({technical:.2f})，"
                f"成交量不足({volume:.2f})。这可能是\"卖出新闻\"模式，市场可能不认同乐观预期。"
            )
            # 根据背离强度调整评分（降低10-30%）
            result['adjustment_factor'] = max(0.7, 1.0 - (divergence_strength * 0.3))
            
            logger.warning(
                f"检测到新闻-价格背离: 新闻={news:.2f}, 技术={technical:.2f}, "
                f"成交量={volume:.2f}, 背离强度={divergence_strength:.2f}"
            )
        
        # 检测"买入新闻"模式：新闻悲观但价格/成交量乐观
        elif news < -0.5 and technical > 0.1:
            divergence_strength = min(1.0, abs(news - technical))
            
            # 如果成交量也是正面的，背离更强
            if volume > 0:
                divergence_strength = min(1.0, divergence_strength * 1.2)
            
            result['has_divergence'] = True
            result['divergence_type'] = 'buy_the_dip'
            result['divergence_strength'] = divergence_strength
            result['warning_message'] = (
                f"⚠️ 背离警告：新闻情绪极度悲观({news:.2f})，但价格走势强劲({technical:.2f})，"
                f"成交量充足({volume:.2f})。市场可能正在\"逢低买入\"，不认同悲观预期。"
            )
            # 根据背离强度调整评分（提高10-30%）
            result['adjustment_factor'] = min(1.3, 1.0 + (divergence_strength * 0.3))
            
            logger.warning(
                f"检测到新闻-价格背离: 新闻={news:.2f}, 技术={technical:.2f}, "
                f"成交量={volume:.2f}, 背离强度={divergence_strength:.2f}"
            )
        
        return result
    
    @staticmethod
    def validate_components(components: Dict[str, float]) -> bool:
        """
        验证组件数据的有效性
        
        检查：
        1. 组件评分是否在有效范围内 [-1, 1]
        2. 组件名称是否有效
        3. 是否至少有一个有效组件
        
        Args:
            components: 组件评分字典
        
        Returns:
            True if valid, False otherwise
        """
        if not components:
            logger.warning("组件字典为空")
            return False
        
        valid_components = set(SentimentCalculator.WEIGHTS.keys())
        
        for component_name, score in components.items():
            # 检查组件名称
            if component_name not in valid_components:
                logger.warning(f"未知的组件名称: {component_name}")
                # 不返回False，允许自定义组件
            
            # 检查评分范围
            if not isinstance(score, (int, float)):
                logger.error(f"组件 '{component_name}' 的评分不是数值类型")
                return False
            
            if not -1.0 <= score <= 1.0:
                logger.error(
                    f"组件 '{component_name}' 的评分 {score} 超出范围 [-1.0, 1.0]"
                )
                return False
        
        return True
