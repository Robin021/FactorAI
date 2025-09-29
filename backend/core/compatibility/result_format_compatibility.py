"""
分析结果格式向后兼容性
确保分析结果格式的一致性，支持旧版结果格式
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import logging
import json

from backend.models.analysis import AnalysisResult


logger = logging.getLogger(__name__)


class ResultFormatCompatibility:
    """结果格式兼容性管理器"""
    
    def __init__(self):
        self.legacy_format_version = "1.0"
        self.current_format_version = "2.0"
    
    def convert_legacy_result_to_new(self, legacy_result: Dict[str, Any]) -> AnalysisResult:
        """转换旧版结果格式到新格式"""
        try:
            # 创建新格式的分析结果
            new_result = AnalysisResult()
            
            # 映射旧版字段到新版字段
            field_mapping = {
                'summary': 'summary',
                'technical': 'technical_analysis',
                'technical_analysis': 'technical_analysis',
                'fundamental': 'fundamental_analysis', 
                'fundamental_analysis': 'fundamental_analysis',
                'news': 'news_analysis',
                'news_analysis': 'news_analysis',
                'risk': 'risk_assessment',
                'risk_analysis': 'risk_assessment',
                'risk_assessment': 'risk_assessment',
                'charts': 'charts',
                'chart_data': 'charts'
            }
            
            # 转换已知字段
            for old_field, new_field in field_mapping.items():
                if old_field in legacy_result:
                    setattr(new_result, new_field, legacy_result[old_field])
            
            # 处理特殊字段
            self._process_special_fields(legacy_result, new_result)
            
            # 保存原始数据
            new_result.raw_data = {
                'original_format': legacy_result,
                'format_version': self.legacy_format_version,
                'converted_at': datetime.utcnow().isoformat(),
                'conversion_notes': 'Converted from legacy format'
            }
            
            logger.info("成功转换旧版结果格式到新格式")
            return new_result
            
        except Exception as e:
            logger.error(f"转换旧版结果格式失败: {e}")
            # 返回包含原始数据的结果
            return AnalysisResult(
                raw_data={
                    'original_format': legacy_result,
                    'conversion_error': str(e),
                    'converted_at': datetime.utcnow().isoformat()
                }
            )
    
    def convert_new_result_to_legacy(self, new_result: AnalysisResult) -> Dict[str, Any]:
        """转换新格式结果到旧版格式"""
        try:
            legacy_result = {}
            
            # 转换基本字段
            if new_result.summary:
                legacy_result['summary'] = new_result.summary
            
            if new_result.technical_analysis:
                legacy_result['technical'] = new_result.technical_analysis
                legacy_result['technical_analysis'] = new_result.technical_analysis
            
            if new_result.fundamental_analysis:
                legacy_result['fundamental'] = new_result.fundamental_analysis
                legacy_result['fundamental_analysis'] = new_result.fundamental_analysis
            
            if new_result.news_analysis:
                legacy_result['news'] = new_result.news_analysis
                legacy_result['news_analysis'] = new_result.news_analysis
            
            if new_result.risk_assessment:
                legacy_result['risk'] = new_result.risk_assessment
                legacy_result['risk_analysis'] = new_result.risk_assessment
                legacy_result['risk_assessment'] = new_result.risk_assessment
            
            if new_result.charts:
                legacy_result['charts'] = new_result.charts
                legacy_result['chart_data'] = new_result.charts
            
            # 添加格式信息
            legacy_result['_format_info'] = {
                'version': self.legacy_format_version,
                'converted_from': self.current_format_version,
                'converted_at': datetime.utcnow().isoformat()
            }
            
            # 如果有原始数据，尝试恢复旧版特有字段
            if new_result.raw_data and 'original_format' in new_result.raw_data:
                original = new_result.raw_data['original_format']
                if isinstance(original, dict):
                    # 恢复旧版特有的字段
                    legacy_specific_fields = [
                        'analyst_opinions', 'market_sentiment', 'trading_signals',
                        'price_targets', 'recommendations', 'confidence_scores'
                    ]
                    
                    for field in legacy_specific_fields:
                        if field in original:
                            legacy_result[field] = original[field]
            
            logger.info("成功转换新格式结果到旧版格式")
            return legacy_result
            
        except Exception as e:
            logger.error(f"转换新格式结果到旧版格式失败: {e}")
            return {
                'error': f"Format conversion failed: {str(e)}",
                'raw_data': new_result.dict() if hasattr(new_result, 'dict') else str(new_result)
            }
    
    def _process_special_fields(self, legacy_result: Dict[str, Any], new_result: AnalysisResult) -> None:
        """处理特殊字段的转换"""
        try:
            # 处理分析师意见
            if 'analyst_opinions' in legacy_result:
                opinions = legacy_result['analyst_opinions']
                if isinstance(opinions, dict):
                    # 将分析师意见分配到相应的分析类别
                    for analyst_type, opinion in opinions.items():
                        if analyst_type == 'technical_analyst':
                            if not new_result.technical_analysis:
                                new_result.technical_analysis = {}
                            new_result.technical_analysis['analyst_opinion'] = opinion
                        elif analyst_type == 'fundamental_analyst':
                            if not new_result.fundamental_analysis:
                                new_result.fundamental_analysis = {}
                            new_result.fundamental_analysis['analyst_opinion'] = opinion
                        elif analyst_type == 'news_analyst':
                            if not new_result.news_analysis:
                                new_result.news_analysis = {}
                            new_result.news_analysis['analyst_opinion'] = opinion
            
            # 处理市场情绪
            if 'market_sentiment' in legacy_result:
                sentiment = legacy_result['market_sentiment']
                if not new_result.summary:
                    new_result.summary = {}
                new_result.summary['market_sentiment'] = sentiment
            
            # 处理交易信号
            if 'trading_signals' in legacy_result:
                signals = legacy_result['trading_signals']
                if not new_result.technical_analysis:
                    new_result.technical_analysis = {}
                new_result.technical_analysis['trading_signals'] = signals
            
            # 处理价格目标
            if 'price_targets' in legacy_result:
                targets = legacy_result['price_targets']
                if not new_result.summary:
                    new_result.summary = {}
                new_result.summary['price_targets'] = targets
            
            # 处理推荐评级
            if 'recommendations' in legacy_result:
                recommendations = legacy_result['recommendations']
                if not new_result.summary:
                    new_result.summary = {}
                new_result.summary['recommendations'] = recommendations
            
            # 处理置信度分数
            if 'confidence_scores' in legacy_result:
                scores = legacy_result['confidence_scores']
                if not new_result.summary:
                    new_result.summary = {}
                new_result.summary['confidence_scores'] = scores
            
        except Exception as e:
            logger.error(f"处理特殊字段失败: {e}")
    
    def detect_result_format(self, result_data: Union[Dict[str, Any], AnalysisResult]) -> str:
        """检测结果数据的格式版本"""
        try:
            if isinstance(result_data, AnalysisResult):
                return self.current_format_version
            
            if isinstance(result_data, dict):
                # 检查格式信息
                if '_format_info' in result_data:
                    return result_data['_format_info'].get('version', self.legacy_format_version)
                
                # 根据字段特征判断
                legacy_indicators = [
                    'technical', 'fundamental', 'news', 'risk',
                    'analyst_opinions', 'market_sentiment', 'trading_signals'
                ]
                
                new_indicators = [
                    'technical_analysis', 'fundamental_analysis', 
                    'news_analysis', 'risk_assessment'
                ]
                
                legacy_score = sum(1 for field in legacy_indicators if field in result_data)
                new_score = sum(1 for field in new_indicators if field in result_data)
                
                if new_score > legacy_score:
                    return self.current_format_version
                else:
                    return self.legacy_format_version
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"检测结果格式失败: {e}")
            return "unknown"
    
    def normalize_result_format(self, result_data: Any, target_format: str = None) -> Union[AnalysisResult, Dict[str, Any]]:
        """标准化结果格式"""
        try:
            if target_format is None:
                target_format = self.current_format_version
            
            current_format = self.detect_result_format(result_data)
            
            # 如果已经是目标格式，直接返回
            if current_format == target_format:
                return result_data
            
            # 转换格式
            if target_format == self.current_format_version:
                # 转换到新格式
                if isinstance(result_data, dict):
                    return self.convert_legacy_result_to_new(result_data)
                else:
                    return result_data
            
            elif target_format == self.legacy_format_version:
                # 转换到旧格式
                if isinstance(result_data, AnalysisResult):
                    return self.convert_new_result_to_legacy(result_data)
                else:
                    return result_data
            
            else:
                logger.warning(f"不支持的目标格式: {target_format}")
                return result_data
            
        except Exception as e:
            logger.error(f"标准化结果格式失败: {e}")
            return result_data
    
    def validate_result_format(self, result_data: Any) -> Dict[str, Any]:
        """验证结果格式"""
        validation_result = {
            'valid': True,
            'format_version': 'unknown',
            'errors': [],
            'warnings': [],
            'missing_fields': [],
            'extra_fields': []
        }
        
        try:
            # 检测格式版本
            format_version = self.detect_result_format(result_data)
            validation_result['format_version'] = format_version
            
            if format_version == self.current_format_version:
                # 验证新格式
                validation_result.update(self._validate_new_format(result_data))
            elif format_version == self.legacy_format_version:
                # 验证旧格式
                validation_result.update(self._validate_legacy_format(result_data))
            else:
                validation_result['valid'] = False
                validation_result['errors'].append("无法识别的结果格式")
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"验证过程失败: {str(e)}")
        
        return validation_result
    
    def _validate_new_format(self, result_data: AnalysisResult) -> Dict[str, Any]:
        """验证新格式结果"""
        validation = {'valid': True, 'errors': [], 'warnings': []}
        
        try:
            # 检查必需字段
            if not hasattr(result_data, 'summary') or result_data.summary is None:
                validation['warnings'].append("缺少摘要信息")
            
            # 检查分析类型
            analysis_types = [
                'technical_analysis', 'fundamental_analysis', 
                'news_analysis', 'risk_assessment'
            ]
            
            has_analysis = any(
                hasattr(result_data, attr) and getattr(result_data, attr) is not None
                for attr in analysis_types
            )
            
            if not has_analysis:
                validation['warnings'].append("缺少分析内容")
            
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(f"新格式验证失败: {str(e)}")
        
        return validation
    
    def _validate_legacy_format(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证旧格式结果"""
        validation = {'valid': True, 'errors': [], 'warnings': []}
        
        try:
            # 检查基本结构
            if not isinstance(result_data, dict):
                validation['valid'] = False
                validation['errors'].append("旧格式结果必须是字典类型")
                return validation
            
            # 检查常见字段
            common_fields = ['summary', 'technical', 'fundamental', 'news', 'risk']
            found_fields = [field for field in common_fields if field in result_data]
            
            if not found_fields:
                validation['warnings'].append("未找到常见的分析字段")
            
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(f"旧格式验证失败: {str(e)}")
        
        return validation


# 全局结果格式兼容性管理器实例
result_format_compatibility = ResultFormatCompatibility()


def ensure_result_compatibility(result_data: Any, target_format: str = None) -> Any:
    """确保结果兼容性的便捷函数"""
    try:
        return result_format_compatibility.normalize_result_format(result_data, target_format)
    except Exception as e:
        logger.error(f"确保结果兼容性失败: {e}")
        return result_data


def validate_and_convert_result(result_data: Any) -> Dict[str, Any]:
    """验证并转换结果的便捷函数"""
    try:
        # 验证格式
        validation_result = result_format_compatibility.validate_result_format(result_data)
        
        # 转换到新格式
        if validation_result['valid']:
            converted_result = result_format_compatibility.normalize_result_format(
                result_data, result_format_compatibility.current_format_version
            )
            
            return {
                'success': True,
                'result': converted_result,
                'validation': validation_result
            }
        else:
            return {
                'success': False,
                'error': 'Validation failed',
                'validation': validation_result,
                'original_result': result_data
            }
            
    except Exception as e:
        logger.error(f"验证和转换结果失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'original_result': result_data
        }