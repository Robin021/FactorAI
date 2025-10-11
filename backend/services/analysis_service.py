"""
Analysis service for executing stock analysis tasks
"""
import asyncio
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.user import UserInDB
from models.analysis import (
    AnalysisRequest,
    AnalysisStatus,
    AnalysisResult,
    MarketType
)
from core.database import get_database, get_redis
from core.exceptions import AnalysisException
from core.database import Depends

# Import TradingAgents components
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Import logging
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('analysis_service')


class AnalysisService:
    """Service for executing stock analysis tasks"""
    
    def __init__(self, db: AsyncIOMotorDatabase, redis_client):
        self.db = db
        self.redis = redis_client
        self._trading_graphs = {}  # Cache for TradingAgentsGraph instances
    
    async def execute_analysis(
        self,
        analysis_id: str,
        analysis_request: AnalysisRequest,
        user: UserInDB
    ):
        """
        Execute analysis task in background
        """
        try:
            logger.info(f"🚀 Starting analysis {analysis_id} for user {user.username}")
            
            # Update status to running
            await self._update_analysis_status(
                analysis_id,
                AnalysisStatus.RUNNING,
                progress=0.0,
                message="Initializing analysis..."
            )
            
            # Get or create TradingAgentsGraph instance
            trading_graph = await self._get_trading_graph(analysis_request, user)
            
            # Update progress with detailed steps
            await self._update_progress(analysis_id, 5.0, "🔍 验证股票代码和市场信息...", "数据验证")
            await asyncio.sleep(1)  # 让用户看到这个步骤
            
            # Prepare analysis parameters
            await self._update_progress(analysis_id, 10.0, "⚙️ 配置分析参数和模型设置...", "参数配置")
            await asyncio.sleep(1)
            stock_code = analysis_request.stock_code
            analysis_date = analysis_request.analysis_date or datetime.now().strftime("%Y-%m-%d")
            
            # Convert stock code format if needed
            formatted_stock_code = self._format_stock_code(stock_code, analysis_request.market_type)
            
            logger.info(f"📊 Executing analysis for {formatted_stock_code} on {analysis_date}")
            
            # Update progress
            await self._update_progress(analysis_id, 15.0, "🚀 初始化AI分析引擎...", "引擎初始化")
            await asyncio.sleep(1)
            await self._update_progress(analysis_id, 20.0, "🤖 加载智能分析模型...", "模型加载")
            await asyncio.sleep(1)
            
            # Execute the analysis
            final_state, decision = await self._run_trading_analysis(
                trading_graph,
                formatted_stock_code,
                analysis_date,
                analysis_id
            )
            
            # 分析完成后的处理
            await self._update_progress(analysis_id, 100.0, "✅ 分析成功完成！", "完成")
            
            # Process and format results
            result_data = await self._process_analysis_results(final_state, decision)
            
            # Update analysis with results
            await self._complete_analysis(analysis_id, result_data)
            
            logger.info(f"✅ Analysis {analysis_id} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Analysis {analysis_id} failed: {str(e)}")
            logger.error(traceback.format_exc())
            
            await self._fail_analysis(analysis_id, str(e))
    
    async def _get_trading_graph(
        self,
        analysis_request: AnalysisRequest,
        user: UserInDB
    ) -> TradingAgentsGraph:
        """
        Get or create TradingAgentsGraph instance with user configuration
        """
        # Create config based on user preferences and request
        config = DEFAULT_CONFIG.copy()
        
        # Apply LLM configuration if provided
        if analysis_request.llm_config:
            config.update(analysis_request.llm_config)
        
        # Apply custom parameters if provided
        if analysis_request.custom_params:
            config.update(analysis_request.custom_params)
        
        # Set market-specific configurations
        if analysis_request.market_type == MarketType.US:
            config["market_type"] = "us"
        elif analysis_request.market_type == MarketType.HK:
            config["market_type"] = "hk"
        else:
            config["market_type"] = "cn"
        
        # Create cache key for this configuration
        config_key = self._get_config_key(config, analysis_request.analysts)
        
        # Return cached instance if available
        if config_key in self._trading_graphs:
            return self._trading_graphs[config_key]
        
        # Create new TradingAgentsGraph instance
        selected_analysts = analysis_request.analysts or ["market", "news", "fundamentals"]
        
        trading_graph = TradingAgentsGraph(
            selected_analysts=selected_analysts,
            debug=False,  # Set to False for production
            config=config
        )
        
        # Cache the instance
        self._trading_graphs[config_key] = trading_graph
        
        return trading_graph
    
    async def _run_trading_analysis(
        self,
        trading_graph: TradingAgentsGraph,
        stock_code: str,
        analysis_date: str,
        analysis_id: str
    ):
        """
        Run the TradingAgents analysis with real-time progress tracking
        """
        # Check for cancellation
        if await self._is_cancelled(analysis_id):
            raise AnalysisException("Analysis was cancelled")
        
        # Define progress callback for real-time updates
        async def progress_callback(message: str, step: int = None, total_steps: int = None, llm_result: str = None, analyst_type: str = None):
            """Progress callback for real-time updates - 支持LLM结果传递"""
            try:
                # Calculate progress based on step (7 total steps)
                if step is not None:
                    # 确保step从0开始，计算正确的进度百分比
                    progress_percentage = ((step + 1) / 7.0) * 80 + 20  # 20-100%范围，前面20%用于初始化
                    step_names = ["股票识别", "市场分析", "基本面分析", "新闻分析", "情绪分析", "投资辩论", "风险评估"]
                    step_name = step_names[min(step, 6)]
                    current_step_number = step + 1  # 传递给前端的步骤编号（1-7）
                    await self._update_progress(analysis_id, progress_percentage, message, step_name, llm_result, analyst_type, current_step_number)
                else:
                    # Auto-detect step from message
                    if "股票识别" in message or "股票类型" in message or "识别股票" in message:
                        await self._update_progress(analysis_id, 31.4, message, "股票识别", llm_result, analyst_type, 1)
                    elif "市场分析师" in message or "Market Analyst" in message or "技术分析" in message:
                        await self._update_progress(analysis_id, 42.9, message, "市场分析", llm_result, analyst_type, 2)
                    elif "基本面分析师" in message or "Fundamentals Analyst" in message or "财务分析" in message:
                        await self._update_progress(analysis_id, 54.3, message, "基本面分析", llm_result, analyst_type, 3)
                    elif "新闻分析师" in message or "News Analyst" in message or "新闻" in message:
                        await self._update_progress(analysis_id, 65.7, message, "新闻分析", llm_result, analyst_type, 4)
                    elif "社交媒体分析师" in message or "Social Media Analyst" in message or "情绪" in message:
                        await self._update_progress(analysis_id, 77.1, message, "情绪分析", llm_result, analyst_type, 5)
                    elif any(keyword in message for keyword in ["Bull Researcher", "Bear Researcher", "Research Manager", "投资辩论", "多空"]):
                        await self._update_progress(analysis_id, 88.6, message, "投资辩论", llm_result, analyst_type, 6)
                    elif any(keyword in message for keyword in ["Risk Judge", "风险管理", "Risky Analyst", "Safe Analyst", "风险评估"]):
                        await self._update_progress(analysis_id, 100.0, message, "风险评估", llm_result, analyst_type, 7)
                    else:
                        # 默认情况，不更新步骤编号
                        await self._update_progress(analysis_id, None, message, None, llm_result, analyst_type)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
        
        # Run the analysis in a separate thread with progress callback
        loop = asyncio.get_event_loop()
        
        def run_analysis():
            # Create a wrapper to handle async callback in sync context
            def sync_progress_callback(message: str, step: int = None, total_steps: int = None, llm_result: str = None, analyst_type: str = None):
                # Schedule the async callback - 支持LLM结果传递
                try:
                    future = asyncio.run_coroutine_threadsafe(progress_callback(message, step, total_steps, llm_result, analyst_type), loop)
                    future.result(timeout=1.0)  # Wait up to 1 second
                except Exception as e:
                    logger.error(f"Sync progress callback error: {e}")
            
            return trading_graph.propagate(stock_code, analysis_date, sync_progress_callback)
        
        # Execute analysis with real-time progress updates
        final_state, decision = await loop.run_in_executor(None, run_analysis)
        
        return final_state, decision
    
    async def _process_analysis_results(
        self,
        final_state: Dict[str, Any],
        decision: Any
    ) -> AnalysisResult:
        """
        Process and format analysis results
        """
        # Extract different types of analysis from the final state
        messages = final_state.get("messages", [])
        
        # Initialize result components
        summary = {}
        technical_analysis = {}
        fundamental_analysis = {}
        news_analysis = {}
        risk_assessment = {}
        charts = []
        
        # Process messages to extract analysis results
        for message in messages:
            if hasattr(message, 'content'):
                content = message.content
                
                # Determine message type and extract relevant information
                if "Market Analyst" in str(message.name) if hasattr(message, 'name') else False:
                    technical_analysis = self._extract_technical_analysis(content)
                elif "Fundamentals Analyst" in str(message.name) if hasattr(message, 'name') else False:
                    fundamental_analysis = self._extract_fundamental_analysis(content)
                elif "News Analyst" in str(message.name) if hasattr(message, 'name') else False:
                    news_analysis = self._extract_news_analysis(content)
                elif "Risk Judge" in str(message.name) if hasattr(message, 'name') else False:
                    risk_assessment = self._extract_risk_assessment(content)
        
        # Extract final decision
        if hasattr(decision, 'content'):
            summary = {
                "final_decision": decision.content,
                "recommendation": self._extract_recommendation(decision.content),
                "confidence_score": self._extract_confidence_score(decision.content)
            }
        else:
            summary = {
                "final_decision": str(decision),
                "recommendation": "HOLD",  # Default
                "confidence_score": 0.5
            }
        
        return AnalysisResult(
            summary=summary,
            technical_analysis=technical_analysis,
            fundamental_analysis=fundamental_analysis,
            news_analysis=news_analysis,
            risk_assessment=risk_assessment,
            charts=charts,
            raw_data={
                "final_state": final_state,
                "decision": str(decision)
            }
        )
    
    def _extract_technical_analysis(self, content: str) -> Dict[str, Any]:
        """Extract technical analysis information"""
        return {
            "content": content,
            "indicators": {},  # TODO: Parse technical indicators
            "trends": {},      # TODO: Parse trend analysis
            "signals": {}      # TODO: Parse trading signals
        }
    
    def _extract_fundamental_analysis(self, content: str) -> Dict[str, Any]:
        """Extract fundamental analysis information"""
        return {
            "content": content,
            "financials": {},  # TODO: Parse financial metrics
            "valuation": {},   # TODO: Parse valuation metrics
            "growth": {}       # TODO: Parse growth metrics
        }
    
    def _extract_news_analysis(self, content: str) -> Dict[str, Any]:
        """Extract news analysis information"""
        return {
            "content": content,
            "sentiment": "neutral",  # TODO: Parse sentiment
            "key_events": [],        # TODO: Parse key events
            "impact_score": 0.5      # TODO: Parse impact score
        }
    
    def _extract_risk_assessment(self, content: str) -> Dict[str, Any]:
        """Extract risk assessment information"""
        return {
            "content": content,
            "risk_level": "medium",  # TODO: Parse risk level
            "risk_factors": [],      # TODO: Parse risk factors
            "risk_score": 0.5        # TODO: Parse risk score
        }
    
    def _extract_recommendation(self, content: str) -> str:
        """Extract investment recommendation from content"""
        content_lower = content.lower()
        if "buy" in content_lower or "bullish" in content_lower:
            return "BUY"
        elif "sell" in content_lower or "bearish" in content_lower:
            return "SELL"
        else:
            return "HOLD"
    
    def _extract_confidence_score(self, content: str) -> float:
        """Extract confidence score from content"""
        # TODO: Implement more sophisticated confidence extraction
        return 0.7  # Default confidence score
    
    def _format_stock_code(self, stock_code: str, market_type: MarketType) -> str:
        """
        Format stock code according to market conventions
        """
        stock_code = stock_code.upper()
        
        if market_type == MarketType.CN:
            # Chinese stocks might need exchange suffix
            if len(stock_code) == 6 and stock_code.isdigit():
                if stock_code.startswith(('60', '68')):
                    return f"{stock_code}.SH"  # Shanghai
                elif stock_code.startswith(('00', '30')):
                    return f"{stock_code}.SZ"  # Shenzhen
            return stock_code
        elif market_type == MarketType.HK:
            # HK stocks might need .HK suffix
            if stock_code.isdigit():
                return f"{stock_code}.HK"
            return stock_code
        else:
            # US stocks usually don't need suffix
            return stock_code
    
    def _get_config_key(self, config: Dict[str, Any], analysts: list) -> str:
        """
        Generate cache key for configuration
        """
        key_parts = [
            config.get("llm_provider", "default"),
            config.get("market_type", "cn"),
            "-".join(sorted(analysts or []))
        ]
        return "|".join(key_parts)
    
    async def _update_analysis_status(
        self,
        analysis_id: str,
        status: AnalysisStatus,
        progress: float = None,
        message: str = None
    ):
        """
        Update analysis status in database
        """
        update_data = {"status": status.value}
        
        if progress is not None:
            update_data["progress"] = progress
        
        # 如果状态变为RUNNING，且数据库中还没有started_at，则设置开始时间
        if status == AnalysisStatus.RUNNING:
            # 检查数据库中是否已经有started_at
            analysis_doc = await self.db.analyses.find_one({"_id": ObjectId(analysis_id)})
            if analysis_doc and not analysis_doc.get("started_at"):
                update_data["started_at"] = datetime.utcnow()
                logger.info(f"🚀 Analysis {analysis_id} started at {update_data['started_at']}")
        elif status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
            update_data["completed_at"] = datetime.utcnow()
        
        if message:
            if status == AnalysisStatus.FAILED:
                update_data["error_message"] = message
        
        await self.db.analyses.update_one(
            {"_id": ObjectId(analysis_id)},
            {"$set": update_data}
        )
    
    async def _update_progress(
        self,
        analysis_id: str,
        progress: float = None,
        message: str = None,
        current_step: str = None,
        llm_result: str = None,
        analyst_type: str = None,
        current_step_number: int = None
    ):
        """
        Update analysis progress in Redis for real-time updates
        """
        # 计算已用时间
        elapsed_time = 0
        estimated_remaining = 0
        
        try:
            # 从数据库获取分析开始时间
            analysis_doc = await self.db.analyses.find_one({"_id": ObjectId(analysis_id)})
            if analysis_doc and analysis_doc.get("started_at"):
                started_at = analysis_doc["started_at"]
                elapsed_time = (datetime.utcnow() - started_at).total_seconds()
                
                # 根据当前进度估算剩余时间
                if progress and progress > 0:
                    total_estimated_time = elapsed_time * (100.0 / progress)
                    estimated_remaining = max(0, total_estimated_time - elapsed_time)
        except Exception as e:
            logger.warning(f"Failed to calculate elapsed time: {e}")
        
        redis_key = f"analysis_progress:{analysis_id}"

        # 读取现有进度，避免覆盖已有的progress字段
        existing_progress_data = {}
        try:
            cached_progress = await self.redis.get(redis_key)
            if cached_progress:
                existing_progress_data = json.loads(cached_progress)
        except Exception as e:
            logger.warning(f"Failed to load existing progress from Redis: {e}")

        # 构建进度数据，默认继承已有字段
        progress_data = dict(existing_progress_data or {})
        progress_data.update({
            "status": "running",  # 添加状态信息
            "elapsed_time": elapsed_time,
            "estimated_remaining": estimated_remaining,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        # 只在有进度值时更新进度相关字段
        if progress is not None:
            progress_data["progress"] = progress
            progress_data["progress_percentage"] = progress / 100.0  # 添加0-1格式的进度
        
        # 只在有消息时更新消息
        if message is not None:
            progress_data["message"] = message
        
        # 只在有步骤信息时更新步骤
        if current_step is not None:
            progress_data["current_step_name"] = current_step
        
        # 只在有步骤编号时更新步骤编号
        if current_step_number is not None:
            progress_data["current_step"] = current_step_number
            progress_data["total_steps"] = 7
        
        # 添加LLM结果信息
        if llm_result:
            progress_data["llm_result"] = llm_result
        if analyst_type:
            progress_data["analyst_type"] = analyst_type
        await self.redis.setex(
            redis_key,
            3600,  # 1 hour TTL
            json.dumps(progress_data)
        )
        
        # 添加调试日志
        if progress is not None:
            logger.info(f"📊 Progress updated: {progress}% - {message} (Redis key: {redis_key})")
        else:
            logger.info(f"📊 Progress message updated: {message} (Redis key: {redis_key})")
        
        # 只在有进度值时更新数据库
        if progress is not None:
            await self.db.analyses.update_one(
                {"_id": ObjectId(analysis_id)},
                {"$set": {"progress": progress}}
            )
    
    async def _complete_analysis(self, analysis_id: str, result_data: AnalysisResult):
        """
        Mark analysis as completed with results
        """
        await self.db.analyses.update_one(
            {"_id": ObjectId(analysis_id)},
            {
                "$set": {
                    "status": AnalysisStatus.COMPLETED.value,
                    "progress": 100.0,
                    "result_data": result_data.dict(),
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Cache result in Redis
        await self.redis.setex(
            f"analysis_result:{analysis_id}",
            86400,  # 24 hours TTL
            json.dumps(result_data.dict())
        )
        
        # 🔧 新增：保存分析结果到MongoDB（用于历史记录和报告管理）
        try:
            await self._save_to_mongodb(analysis_id, result_data)
        except Exception as e:
            logger.error(f"Failed to save analysis to MongoDB: {e}")
            # 不影响主流程，继续执行
        
        # Clean up progress cache
        await self.redis.delete(f"analysis_progress:{analysis_id}")
    
    async def _fail_analysis(self, analysis_id: str, error_message: str):
        """
        Mark analysis as failed with error message
        """
        await self.db.analyses.update_one(
            {"_id": ObjectId(analysis_id)},
            {
                "$set": {
                    "status": AnalysisStatus.FAILED.value,
                    "error_message": error_message,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Clean up progress cache
        await self.redis.delete(f"analysis_progress:{analysis_id}")
    
    async def _is_cancelled(self, analysis_id: str) -> bool:
        """
        Check if analysis has been cancelled
        """
        cancel_flag = await self.redis.get(f"analysis_cancel:{analysis_id}")
        return cancel_flag is not None
    
    async def _save_to_mongodb(self, analysis_id: str, result_data: AnalysisResult):
        """
        保存分析结果到MongoDB（用于历史记录和报告管理）
        """
        try:
            # 获取分析记录
            analysis_doc = await self.db.analyses.find_one({"_id": ObjectId(analysis_id)})
            if not analysis_doc:
                logger.error(f"Analysis document not found: {analysis_id}")
                return
            
            # 准备MongoDB文档
            stock_symbol = analysis_doc.get("stock_code", "")
            timestamp = datetime.utcnow()
            
            # 构建分析结果摘要
            summary = result_data.summary or {}
            recommendation = summary.get("recommendation", "HOLD")
            confidence_score = summary.get("confidence_score", 0.5)
            
            # 构建报告内容
            reports = {}
            if result_data.technical_analysis:
                reports["technical_analysis"] = result_data.technical_analysis.get("content", "")
            if result_data.fundamental_analysis:
                reports["fundamental_analysis"] = result_data.fundamental_analysis.get("content", "")
            if result_data.news_analysis:
                reports["news_analysis"] = result_data.news_analysis.get("content", "")
            if result_data.risk_assessment:
                reports["risk_assessment"] = result_data.risk_assessment.get("content", "")
            if summary.get("final_decision"):
                reports["final_decision"] = summary["final_decision"]
            
            # 构建MongoDB文档
            mongodb_doc = {
                "analysis_id": analysis_id,
                "stock_symbol": stock_symbol,
                "analysis_date": timestamp.strftime('%Y-%m-%d'),
                "timestamp": timestamp,
                "status": "completed",
                "source": "backend_api",
                
                # 分析结果摘要
                "summary": {
                    "recommendation": recommendation,
                    "confidence_score": confidence_score,
                    "final_decision": summary.get("final_decision", "")
                },
                "analysts": analysis_doc.get("config", {}).get("analysts", []),
                "research_depth": 1,  # 默认研究深度
                
                # 报告内容
                "reports": reports,
                
                # 原始数据
                "raw_data": result_data.raw_data or {},
                
                # 元数据
                "created_at": timestamp,
                "updated_at": timestamp,
                "user_id": str(analysis_doc.get("user_id", "")),
                "market_type": analysis_doc.get("market_type", "")
            }
            
            # 保存到MongoDB
            await self.db.analysis_reports.insert_one(mongodb_doc)
            logger.info(f"✅ Analysis result saved to MongoDB: {analysis_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save analysis to MongoDB: {e}")
            raise


# Dependency function
async def get_analysis_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
) -> AnalysisService:
    """
    Dependency to get analysis service instance
    """
    return AnalysisService(db, redis_client)
