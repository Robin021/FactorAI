"""
API向后兼容性层
保持现有API接口的兼容性，提供平滑的升级路径
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from backend.models.analysis import AnalysisRequest, Analysis, AnalysisStatus
from backend.models.user import User
from backend.services.analysis_service import AnalysisService
from backend.core.auth import get_current_user


logger = logging.getLogger(__name__)

# 创建兼容性路由器
compatibility_router = APIRouter(prefix="/api/legacy", tags=["Legacy Compatibility"])


class LegacyAPIAdapter:
    """旧版API适配器"""
    
    def __init__(self):
        self.analysis_service = AnalysisService()
    
    def convert_legacy_request(self, legacy_request: Dict[str, Any]) -> AnalysisRequest:
        """转换旧版分析请求格式到新格式"""
        try:
            # 旧版请求格式映射
            stock_code = legacy_request.get('symbol') or legacy_request.get('stock_code', '')
            
            # 检测市场类型
            market_type = self._detect_market_type_legacy(stock_code)
            
            # 转换分析师列表
            analysts = legacy_request.get('analysts', [])
            if isinstance(analysts, str):
                analysts = [analysts]
            
            # 转换LLM配置
            llm_config = None
            if 'llm_provider' in legacy_request or 'model' in legacy_request:
                llm_config = {
                    'provider': legacy_request.get('llm_provider', 'openai'),
                    'model_name': legacy_request.get('model', 'gpt-4o-mini'),
                    'temperature': legacy_request.get('temperature', 0.7),
                    'max_tokens': legacy_request.get('max_tokens')
                }
            
            # 创建新格式请求
            new_request = AnalysisRequest(
                stock_code=stock_code,
                market_type=market_type,
                analysis_date=legacy_request.get('date'),
                analysts=analysts,
                llm_config=llm_config,
                custom_params=legacy_request.get('params', {})
            )
            
            return new_request
            
        except Exception as e:
            logger.error(f"转换旧版请求失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid legacy request format: {str(e)}"
            )
    
    def convert_analysis_to_legacy(self, analysis: Analysis) -> Dict[str, Any]:
        """转换新格式分析结果到旧版格式"""
        try:
            legacy_response = {
                'id': analysis.id,
                'symbol': analysis.stock_code,
                'stock_code': analysis.stock_code,
                'market': analysis.market_type,
                'status': self._convert_status_to_legacy(analysis.status),
                'progress': analysis.progress,
                'created_at': analysis.created_at.isoformat(),
                'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
                'config': analysis.config
            }
            
            # 转换结果数据
            if analysis.result_data:
                legacy_response['results'] = self._convert_results_to_legacy(analysis.result_data)
            
            # 添加错误信息
            if analysis.error_message:
                legacy_response['error'] = analysis.error_message
            
            return legacy_response
            
        except Exception as e:
            logger.error(f"转换分析结果到旧版格式失败: {e}")
            return {
                'id': analysis.id,
                'symbol': analysis.stock_code,
                'status': 'error',
                'error': f"Format conversion failed: {str(e)}"
            }
    
    def _detect_market_type_legacy(self, stock_code: str) -> str:
        """检测市场类型（旧版逻辑）"""
        if not stock_code:
            return "cn"
        
        stock_code = stock_code.upper()
        
        # 港股
        if stock_code.startswith('HK') or (stock_code.isdigit() and len(stock_code) == 5):
            return "hk"
        
        # 美股
        if stock_code.isalpha() and len(stock_code) <= 5:
            return "us"
        
        # 默认A股
        return "cn"
    
    def _convert_status_to_legacy(self, status: AnalysisStatus) -> str:
        """转换状态到旧版格式"""
        status_mapping = {
            AnalysisStatus.PENDING: "pending",
            AnalysisStatus.RUNNING: "running",
            AnalysisStatus.COMPLETED: "completed",
            AnalysisStatus.FAILED: "failed",
            AnalysisStatus.CANCELLED: "cancelled"
        }
        return status_mapping.get(status, "unknown")
    
    def _convert_results_to_legacy(self, result_data: Any) -> Dict[str, Any]:
        """转换结果数据到旧版格式"""
        try:
            if hasattr(result_data, 'dict'):
                result_dict = result_data.dict()
            elif isinstance(result_data, dict):
                result_dict = result_data
            else:
                return {"raw_data": str(result_data)}
            
            # 旧版格式映射
            legacy_results = {}
            
            # 映射各个分析部分
            if 'summary' in result_dict:
                legacy_results['summary'] = result_dict['summary']
            
            if 'technical_analysis' in result_dict:
                legacy_results['technical'] = result_dict['technical_analysis']
            
            if 'fundamental_analysis' in result_dict:
                legacy_results['fundamental'] = result_dict['fundamental_analysis']
            
            if 'news_analysis' in result_dict:
                legacy_results['news'] = result_dict['news_analysis']
            
            if 'risk_assessment' in result_dict:
                legacy_results['risk'] = result_dict['risk_assessment']
            
            if 'charts' in result_dict:
                legacy_results['charts'] = result_dict['charts']
            
            # 保留原始数据
            if 'raw_data' in result_dict:
                legacy_results['raw_data'] = result_dict['raw_data']
            
            return legacy_results
            
        except Exception as e:
            logger.error(f"转换结果数据失败: {e}")
            return {"error": f"Result conversion failed: {str(e)}"}


# 创建适配器实例
legacy_adapter = LegacyAPIAdapter()


@compatibility_router.post("/analysis/start")
async def start_legacy_analysis(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    启动分析（旧版API兼容）
    
    支持旧版请求格式:
    {
        "symbol": "000001",
        "analysts": ["technical", "fundamental"],
        "llm_provider": "openai",
        "model": "gpt-4o-mini",
        "params": {...}
    }
    """
    try:
        # 转换请求格式
        analysis_request = legacy_adapter.convert_legacy_request(request_data)
        
        # 调用新版分析服务
        analysis = await legacy_adapter.analysis_service.start_analysis(
            analysis_request, current_user.id
        )
        
        # 转换响应格式
        legacy_response = legacy_adapter.convert_analysis_to_legacy(analysis)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": legacy_response,
                "message": "Analysis started successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"旧版分析启动失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": str(e),
                "message": "Failed to start analysis"
            }
        )


@compatibility_router.get("/analysis/{analysis_id}/status")
async def get_legacy_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取分析状态（旧版API兼容）"""
    try:
        analysis = await legacy_adapter.analysis_service.get_analysis(
            analysis_id, current_user.id
        )
        
        if not analysis:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "error": "Analysis not found",
                    "message": "Analysis not found"
                }
            )
        
        legacy_response = legacy_adapter.convert_analysis_to_legacy(analysis)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": legacy_response,
                "message": "Status retrieved successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"获取旧版分析状态失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": str(e),
                "message": "Failed to get analysis status"
            }
        )


@compatibility_router.get("/analysis/{analysis_id}/result")
async def get_legacy_analysis_result(
    analysis_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取分析结果（旧版API兼容）"""
    try:
        analysis = await legacy_adapter.analysis_service.get_analysis_result(
            analysis_id, current_user.id
        )
        
        if not analysis:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "error": "Analysis not found",
                    "message": "Analysis not found"
                }
            )
        
        legacy_response = legacy_adapter.convert_analysis_to_legacy(analysis)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": legacy_response,
                "message": "Result retrieved successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"获取旧版分析结果失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": str(e),
                "message": "Failed to get analysis result"
            }
        )


@compatibility_router.get("/analysis/history")
async def get_legacy_analysis_history(
    symbol: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """获取分析历史（旧版API兼容）"""
    try:
        # 构建查询参数
        from backend.models.analysis import AnalysisHistoryQuery
        
        query = AnalysisHistoryQuery(
            stock_code=symbol,
            page=offset // limit + 1,
            page_size=limit
        )
        
        # 获取分析历史
        history_response = await legacy_adapter.analysis_service.get_analysis_history(
            query, current_user.id
        )
        
        # 转换为旧版格式
        legacy_analyses = [
            legacy_adapter.convert_analysis_to_legacy(analysis)
            for analysis in history_response.analyses
        ]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "analyses": legacy_analyses,
                    "total": history_response.total,
                    "limit": limit,
                    "offset": offset
                },
                "message": "History retrieved successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"获取旧版分析历史失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": str(e),
                "message": "Failed to get analysis history"
            }
        )


@compatibility_router.delete("/analysis/{analysis_id}")
async def delete_legacy_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除分析记录（旧版API兼容）"""
    try:
        success = await legacy_adapter.analysis_service.delete_analysis(
            analysis_id, current_user.id
        )
        
        if not success:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "error": "Analysis not found",
                    "message": "Analysis not found or already deleted"
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Analysis deleted successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"删除旧版分析记录失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": str(e),
                "message": "Failed to delete analysis"
            }
        )


# 健康检查端点
@compatibility_router.get("/health")
async def legacy_health_check():
    """旧版健康检查端点"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "status": "healthy",
            "version": "legacy-compatible",
            "message": "Legacy API is running"
        }
    )


# 版本信息端点
@compatibility_router.get("/version")
async def legacy_version_info():
    """旧版版本信息端点"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": {
                "api_version": "v1-legacy",
                "compatibility_layer": "active",
                "supported_features": [
                    "analysis_start",
                    "analysis_status",
                    "analysis_result",
                    "analysis_history",
                    "analysis_delete"
                ]
            },
            "message": "Legacy API version information"
        }
    )