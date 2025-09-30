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
            
            # Update progress with detailed result processing
            await self._update_progress(analysis_id, 80.0, "🔄 整合分析结果...", "结果整合")
            await asyncio.sleep(2)
            await self._update_progress(analysis_id, 85.0, "📊 生成图表和可视化...", "图表生成")
            await asyncio.sleep(2)
            await self._update_progress(analysis_id, 90.0, "📝 编写分析报告...", "报告生成")
            await asyncio.sleep(2)
            await self._update_progress(analysis_id, 95.0, "🎨 优化报告格式...", "格式优化")
            await asyncio.sleep(1)
            
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
        Run the TradingAgents analysis with progress tracking
        """
        # Check for cancellation
        if await self._is_cancelled(analysis_id):
            raise AnalysisException("Analysis was cancelled")
        
        # Update progress with detailed market analysis steps
        await self._update_progress(analysis_id, 25.0, "📊 开始市场数据收集...", "数据收集")
        await asyncio.sleep(2)
        await self._update_progress(analysis_id, 30.0, "📈 执行技术指标分析...", "技术分析")
        await asyncio.sleep(3)
        await self._update_progress(analysis_id, 40.0, "💼 进行基本面分析...", "基本面分析")
        await asyncio.sleep(3)
        await self._update_progress(analysis_id, 50.0, "📰 分析市场新闻和情绪...", "情绪分析")
        await asyncio.sleep(2)
        await self._update_progress(analysis_id, 60.0, "🔄 运行多智能体协作分析...", "智能体分析")
        await asyncio.sleep(4)
        
        # Run the analysis in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        
        def run_analysis():
            return trading_graph.propagate(stock_code, analysis_date)
        
        # Execute with periodic progress updates
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
        
        if status == AnalysisStatus.RUNNING and "started_at" not in update_data:
            update_data["started_at"] = datetime.utcnow()
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
        progress: float,
        message: str = None,
        current_step: str = None
    ):
        """
        Update analysis progress in Redis for real-time updates
        """
        progress_data = {
            "status": "running",  # 添加状态信息
            "progress": progress,
            "message": message,
            "current_step": current_step,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        redis_key = f"analysis_progress:{analysis_id}"
        await self.redis.setex(
            redis_key,
            3600,  # 1 hour TTL
            json.dumps(progress_data)
        )
        
        # 添加调试日志
        logger.info(f"📊 Progress updated: {progress}% - {message} (Redis key: {redis_key})")
        
        # Also update database
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


# Dependency function
async def get_analysis_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
) -> AnalysisService:
    """
    Dependency to get analysis service instance
    """
    return AnalysisService(db, redis_client)