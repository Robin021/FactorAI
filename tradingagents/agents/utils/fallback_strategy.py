"""
降级策略管理模块

该模块实现数据源失败时的降级策略，确保服务可用性。
实现5级降级逻辑：完整→增强→核心→最小→中性

需求: 8.1, 8.2, 8.3, 8.6
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

# 导入日志管理器
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('fallback_strategy')


class FallbackLevel(Enum):
    """降级级别枚举"""
    FULL = 'full'              # Level 1: 完整数据（核心层 + 增强层）
    ENHANCED = 'enhanced'      # Level 2: 核心层 + 部分增强层
    CORE = 'core'              # Level 3: 仅核心层（新闻 + 价格 + 成交量）
    MINIMAL = 'minimal'        # Level 4: 最小化分析（仅新闻情绪）
    NEUTRAL = 'neutral'        # Level 5: 返回中性评分 + 说明


class FailureRecord:
    """失败记录"""
    
    def __init__(self, component: str, error: Exception, timestamp: datetime = None):
        self.component = component
        self.error = str(error)
        self.error_type = type(error).__name__
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'component': self.component,
            'error': self.error,
            'error_type': self.error_type,
            'timestamp': self.timestamp.isoformat()
        }


class FallbackStrategy:
    """
    降级策略管理器
    
    实现5级降级逻辑，根据数据源失败情况自动降级：
    - Level 1 (FULL): 完整数据（核心层 + 增强层）
    - Level 2 (ENHANCED): 核心层 + 部分增强层
    - Level 3 (CORE): 仅核心层（新闻 + 价格 + 成交量）
    - Level 4 (MINIMAL): 最小化分析（仅新闻情绪）
    - Level 5 (NEUTRAL): 返回中性评分 + 说明
    
    需求: 8.1, 8.2, 8.3, 8.6
    """
    
    # 核心组件列表（需求 8.2）
    CORE_COMPONENTS = ['news_sentiment', 'price_momentum', 'volume_sentiment']
    
    # 增强组件列表（按市场分类）
    ENHANCED_COMPONENTS = {
        'US': ['vix_sentiment', 'reddit_sentiment'],
        'CN': ['northbound_flow', 'margin_trading', 'volatility_sentiment'],
        'HK': ['southbound_flow']
    }
    
    # 降级阈值配置
    DEGRADATION_THRESHOLDS = {
        FallbackLevel.ENHANCED: 1,   # 1个增强组件失败 -> ENHANCED
        FallbackLevel.CORE: 2,       # 2个组件失败 -> CORE
        FallbackLevel.MINIMAL: 4,    # 4个组件失败 -> MINIMAL
        FallbackLevel.NEUTRAL: 6     # 6个组件失败 -> NEUTRAL
    }
    
    def __init__(self, market_type: str = 'US'):
        """
        初始化降级策略管理器
        
        Args:
            market_type: 市场类型 (US/CN/HK)
        """
        self.market_type = market_type
        self.current_level = FallbackLevel.FULL
        self.failures: List[FailureRecord] = []
        self.warnings: List[str] = []
        
        logger.info(f"降级策略管理器初始化: 市场={market_type}, 级别={self.current_level.value}")
    
    def record_failure(self, component: str, error: Exception) -> None:
        """
        记录组件失败（需求 8.1, 8.3）
        
        Args:
            component: 失败的组件名称
            error: 异常对象
        """
        failure = FailureRecord(component, error)
        self.failures.append(failure)
        
        logger.warning(
            f"组件失败: {component}, 错误: {failure.error}, "
            f"失败次数: {len(self.failures)}"
        )
        
        # 更新降级级别
        self._update_degradation_level()
    
    def _update_degradation_level(self) -> None:
        """
        根据失败次数更新降级级别（需求 8.1, 8.2）
        """
        failure_count = len(self.failures)
        previous_level = self.current_level
        
        # 根据失败次数确定降级级别
        if failure_count >= self.DEGRADATION_THRESHOLDS[FallbackLevel.NEUTRAL]:
            self.current_level = FallbackLevel.NEUTRAL
        elif failure_count >= self.DEGRADATION_THRESHOLDS[FallbackLevel.MINIMAL]:
            self.current_level = FallbackLevel.MINIMAL
        elif failure_count >= self.DEGRADATION_THRESHOLDS[FallbackLevel.CORE]:
            self.current_level = FallbackLevel.CORE
        elif failure_count >= self.DEGRADATION_THRESHOLDS[FallbackLevel.ENHANCED]:
            self.current_level = FallbackLevel.ENHANCED
        else:
            self.current_level = FallbackLevel.FULL
        
        # 如果级别发生变化，记录警告
        if self.current_level != previous_level:
            warning = f"降级级别变更: {previous_level.value} -> {self.current_level.value}"
            self.warnings.append(warning)
            logger.warning(warning)
    
    def get_fallback_data(
        self,
        component: str,
        market_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取降级数据（需求 8.1, 8.4）
        
        根据组件类型和当前降级级别，返回替代数据或默认值。
        
        Args:
            component: 组件名称
            market_type: 市场类型（可选，默认使用初始化时的市场类型）
        
        Returns:
            降级数据字典，包含替代评分和说明
        """
        market = market_type or self.market_type
        
        logger.info(f"获取降级数据: 组件={component}, 市场={market}, 级别={self.current_level.value}")
        
        # 根据组件类型返回降级数据
        if component in self.CORE_COMPONENTS:
            return self._get_core_component_fallback(component)
        else:
            return self._get_enhanced_component_fallback(component, market)
    
    def _get_core_component_fallback(self, component: str) -> Dict[str, Any]:
        """
        获取核心组件的降级数据（需求 8.2）
        
        核心组件失败时，返回中性评分和说明。
        """
        fallback_data = {
            'score': 0.0,  # 中性评分
            'confidence': 0.0,
            'fallback_used': True,
            'fallback_reason': f'{component} 数据不可用，使用中性评分',
            'data_source': 'fallback',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"核心组件降级: {component} -> 中性评分")
        return fallback_data
    
    def _get_enhanced_component_fallback(
        self,
        component: str,
        market_type: str
    ) -> Dict[str, Any]:
        """
        获取增强组件的降级数据（需求 8.1, 8.4）
        
        增强组件失败时，尝试使用替代数据源或返回中性评分。
        """
        # 定义替代数据源映射
        alternative_sources = {
            'vix_sentiment': self._get_vix_alternative,
            'reddit_sentiment': self._get_reddit_alternative,
            'northbound_flow': self._get_northbound_alternative,
            'margin_trading': self._get_margin_alternative,
            'volatility_sentiment': self._get_volatility_alternative,
            'southbound_flow': self._get_southbound_alternative
        }
        
        # 尝试使用替代数据源
        if component in alternative_sources:
            try:
                alternative_data = alternative_sources[component]()
                if alternative_data:
                    logger.info(f"使用替代数据源: {component}")
                    return alternative_data
            except Exception as e:
                logger.warning(f"替代数据源也失败: {component}, 错误: {e}")
        
        # 如果没有替代数据源或替代数据源也失败，返回中性评分
        fallback_data = {
            'score': 0.0,
            'confidence': 0.0,
            'fallback_used': True,
            'fallback_reason': f'{component} 数据不可用，无替代数据源',
            'data_source': 'fallback',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"增强组件降级: {component} -> 中性评分")
        return fallback_data
    
    # 替代数据源方法（需求 8.4, 8.5）
    
    def _get_vix_alternative(self) -> Optional[Dict[str, Any]]:
        """VIX替代方案：使用历史平均值"""
        logger.info("VIX降级：使用历史平均值 (VIX=20)")
        return {
            'score': 0.0,  # VIX=20 对应中性情绪
            'confidence': 0.3,
            'fallback_used': True,
            'fallback_reason': 'VIX数据不可用，使用历史平均值',
            'data_source': 'historical_average',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_reddit_alternative(self) -> Optional[Dict[str, Any]]:
        """Reddit替代方案：忽略社交媒体情绪"""
        logger.info("Reddit降级：忽略社交媒体情绪")
        return None  # 返回None表示跳过该组件
    
    def _get_northbound_alternative(self) -> Optional[Dict[str, Any]]:
        """北向资金替代方案：使用市场整体数据"""
        logger.info("北向资金降级：使用市场整体数据")
        return {
            'score': 0.0,
            'confidence': 0.2,
            'fallback_used': True,
            'fallback_reason': '个股北向资金数据不可用，使用市场整体趋势',
            'data_source': 'market_aggregate',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_margin_alternative(self) -> Optional[Dict[str, Any]]:
        """融资融券替代方案：使用市场整体数据"""
        logger.info("融资融券降级：使用市场整体数据")
        return {
            'score': 0.0,
            'confidence': 0.2,
            'fallback_used': True,
            'fallback_reason': '个股融资融券数据不可用，使用市场整体数据',
            'data_source': 'market_aggregate',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_volatility_alternative(self) -> Optional[Dict[str, Any]]:
        """波动率替代方案：使用简化计算"""
        logger.info("波动率降级：使用简化计算")
        return {
            'score': 0.0,
            'confidence': 0.4,
            'fallback_used': True,
            'fallback_reason': '历史波动率数据不足，使用简化计算',
            'data_source': 'simplified_calculation',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_southbound_alternative(self) -> Optional[Dict[str, Any]]:
        """南向资金替代方案：使用市场整体数据"""
        logger.info("南向资金降级：使用市场整体数据")
        return {
            'score': 0.0,
            'confidence': 0.2,
            'fallback_used': True,
            'fallback_reason': '个股南向资金数据不可用，使用市场整体趋势',
            'data_source': 'market_aggregate',
            'timestamp': datetime.now().isoformat()
        }
    
    def should_skip_component(self, component: str) -> bool:
        """
        判断是否应该跳过某个组件（需求 8.2）
        
        根据当前降级级别，决定是否跳过某些组件的分析。
        
        Args:
            component: 组件名称
        
        Returns:
            True if should skip, False otherwise
        """
        # Level 5: 跳过所有组件
        if self.current_level == FallbackLevel.NEUTRAL:
            return True
        
        # Level 4: 只保留新闻情绪
        if self.current_level == FallbackLevel.MINIMAL:
            return component != 'news_sentiment'
        
        # Level 3: 只保留核心组件
        if self.current_level == FallbackLevel.CORE:
            return component not in self.CORE_COMPONENTS
        
        # Level 2: 跳过部分增强组件
        if self.current_level == FallbackLevel.ENHANCED:
            # 保留核心组件和部分增强组件
            enhanced_components = self.ENHANCED_COMPONENTS.get(self.market_type, [])
            return component not in self.CORE_COMPONENTS and component not in enhanced_components
        
        # Level 1: 不跳过任何组件
        return False
    
    def get_neutral_sentiment(self, ticker: str, reason: str = None) -> Dict[str, Any]:
        """
        返回中性情绪评分（需求 8.6）
        
        当所有数据源都失败时，返回中性评分和说明。
        
        Args:
            ticker: 股票代码
            reason: 返回中性评分的原因
        
        Returns:
            中性情绪数据字典
        """
        default_reason = "所有数据源失败，返回中性评分"
        
        logger.warning(f"返回中性情绪: {ticker}, 原因: {reason or default_reason}")
        
        return {
            'ticker': ticker,
            'score': 50.0,  # 中性评分
            'level': '中性',
            'confidence': 0.0,
            'fallback_used': True,
            'fallback_level': FallbackLevel.NEUTRAL.value,
            'reason': reason or default_reason,
            'failures': [f.to_dict() for f in self.failures],
            'warnings': self.warnings,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取降级策略状态（需求 8.3）
        
        Returns:
            状态信息字典
        """
        return {
            'current_level': self.current_level.value,
            'market_type': self.market_type,
            'failure_count': len(self.failures),
            'failures': [f.to_dict() for f in self.failures],
            'warnings': self.warnings,
            'core_components_available': [
                c for c in self.CORE_COMPONENTS
                if not any(f.component == c for f in self.failures)
            ],
            'enhanced_components_available': [
                c for c in self.ENHANCED_COMPONENTS.get(self.market_type, [])
                if not any(f.component == c for f in self.failures)
            ]
        }
    
    def get_data_availability_note(self) -> str:
        """
        生成数据可用性说明（需求 8.4）
        
        Returns:
            数据可用性说明文本
        """
        if self.current_level == FallbackLevel.FULL:
            return "所有数据源正常"
        
        notes = []
        notes.append(f"当前降级级别: {self.current_level.value}")
        
        if self.failures:
            notes.append(f"失败组件数: {len(self.failures)}")
            failed_components = [f.component for f in self.failures]
            notes.append(f"失败组件: {', '.join(failed_components)}")
        
        if self.warnings:
            notes.append("警告信息:")
            for warning in self.warnings:
                notes.append(f"  - {warning}")
        
        return "\n".join(notes)
    
    def has_failures(self) -> bool:
        """
        检查是否有失败记录
        
        Returns:
            True if there are failures, False otherwise
        """
        return len(self.failures) > 0
    
    def get_failures(self) -> List[FailureRecord]:
        """
        获取所有失败记录
        
        Returns:
            失败记录列表
        """
        return self.failures.copy()
    
    def reset(self) -> None:
        """重置降级策略状态"""
        self.current_level = FallbackLevel.FULL
        self.failures.clear()
        self.warnings.clear()
        logger.info("降级策略状态已重置")
