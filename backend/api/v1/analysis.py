"""
Analysis API endpoints
"""
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.user import UserInDB
from models.analysis import (
    Analysis,
    AnalysisInDB,
    AnalysisRequest,
    AnalysisProgress,
    AnalysisResult,
    AnalysisStatus,
    AnalysisListResponse,
    AnalysisHistoryQuery,
    MarketType
)
from core.security import (
    get_current_active_user,
    require_permissions,
    Permissions
)
from core.database import get_database, get_redis
from core.exceptions import AuthenticationException, ValidationException
from services.analysis_service import AnalysisService, get_analysis_service

# Import logging
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('api.analysis')

router = APIRouter()


@router.post("/start", response_model=dict)
async def start_analysis(
    analysis_request: AnalysisRequest,
    priority: Optional[str] = "normal",
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_CREATE])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Start a new analysis task using async task queue
    """
    # Import here to avoid circular imports
    from services.async_analysis_service import get_async_analysis_service
    from core.task_queue import TaskPriority
    
    # Validate stock code format based on market type
    if not _validate_stock_code(analysis_request.stock_code, analysis_request.market_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stock code format for {analysis_request.market_type.value} market"
        )
    
    # Check if user has reached analysis limit (optional rate limiting)
    user_query = {"$or": [
        {"user_id": current_user.id},
        {"user_id": str(current_user.id)},
        {"user_id": current_user.username}
    ]}
    active_analyses = await db.analyses.count_documents({
        **user_query,
        "status": {"$in": [AnalysisStatus.PENDING.value, AnalysisStatus.RUNNING.value]}
    })
    
    if active_analyses >= 5:  # Limit to 5 concurrent analyses per user
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many active analyses. Please wait for some to complete."
        )
    
    # Parse priority
    priority_map = {
        "low": TaskPriority.LOW,
        "normal": TaskPriority.NORMAL,
        "high": TaskPriority.HIGH,
        "urgent": TaskPriority.URGENT
    }
    task_priority = priority_map.get(priority.lower(), TaskPriority.NORMAL)
    
    # Get async analysis service
    async_analysis_service = await get_async_analysis_service()
    
    # Start analysis using async task queue
    analysis_id = await async_analysis_service.start_analysis(
        analysis_request, current_user, task_priority
    )
    
    return {
        "analysis_id": analysis_id,
        "status": "queued",
        "message": "Analysis queued successfully",
        "priority": priority
    }


@router.get("/{analysis_id}/download/pdf")
async def download_analysis_pdf(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Download a simple PDF report generated from the analysis result.
    - Requires the analysis to belong to the current user (or admin) and be completed.
    - Generates a minimal one-page PDF on the fly with basic info.
    """
    # Validate analysis id
    try:
        analysis_object_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID format"
        )

    # Load analysis
    analysis_doc = await db.analyses.find_one({"_id": analysis_object_id})
    if not analysis_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    analysis = AnalysisInDB(**analysis_doc)

    # Ownership check
    if str(analysis.user_id) != str(current_user.id) and "admin" not in current_user.role.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Must be completed to export
    if analysis.status != AnalysisStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Analysis is not completed")

    # Prepare minimal text content from result (fallbacks provided)
    stock = analysis.stock_code or "UNKNOWN"
    title = f"Analysis Report for {stock}"
    created = analysis.created_at.strftime("%Y-%m-%d %H:%M:%S") if analysis.created_at else ""
    completed = analysis.completed_at.strftime("%Y-%m-%d %H:%M:%S") if analysis.completed_at else ""
    summary_lines = []
    try:
        rd = analysis.result_data or {}
        # Try a few common fields for a short summary
        for key in [
            "summary", "final_trade_decision", "investment_plan", "market_report",
            "fundamentals_report", "sentiment_report", "risk_assessment"
        ]:
            val = rd.get(key)
            if isinstance(val, str) and val.strip():
                summary_lines.append(f"- {key}: {val.strip()[:300]}")
                if len(summary_lines) >= 5:
                    break
            elif isinstance(val, dict):
                # take first few key: value pairs
                inner = [f"{k}: {str(v)[:120]}" for k, v in list(val.items())[:3]]
                if inner:
                    summary_lines.append(f"- {key}: " + "; ".join(inner))
                    if len(summary_lines) >= 5:
                        break
    except Exception:
        pass

    # 进一步增强：如果没有找到常用字段，从 state 中提取兼容字段
    if not summary_lines and analysis.result_data:
        try:
            rd = analysis.result_data if isinstance(analysis.result_data, dict) else analysis.result_data.dict()
            state = rd.get('state') or {}
            ordered_keys = [
                'final_trade_decision', 'trader_investment_plan', 'investment_plan',
                'fundamentals_report', 'market_report', 'sentiment_report', 'risk_assessment'
            ]
            for key in ordered_keys:
                val = state.get(key) or rd.get(key)
                if isinstance(val, str) and val.strip():
                    summary_lines.append(f"【{key}】 {val.strip()[:800]}")
            decision = rd.get('decision')
            if isinstance(decision, dict):
                parts = []
                if decision.get('action'): parts.append(f"操作: {decision.get('action')}")
                if decision.get('target_price') not in (None, 'N/A', 'None', ''):
                    parts.append(f"目标价: {decision.get('target_price')}")
                if decision.get('reasoning'):
                    parts.append(f"理由: {str(decision.get('reasoning'))[:400]}")
                if parts:
                    summary_lines.insert(0, "【决策】 " + '; '.join(parts))
        except Exception:
            pass
    
    # 添加研究团队决策和风险管理团队决策
    if analysis.result_data:
        try:
            rd = analysis.result_data if isinstance(analysis.result_data, dict) else analysis.result_data.dict()
            
            # 研究团队决策
            investment_debate = rd.get('investment_debate_state') or {}
            if investment_debate.get('bull_history'):
                summary_lines.append(f"【多头研究员】 {investment_debate['bull_history'][:600]}")
            if investment_debate.get('bear_history'):
                summary_lines.append(f"【空头研究员】 {investment_debate['bear_history'][:600]}")
            if investment_debate.get('judge_decision'):
                summary_lines.append(f"【研究经理决策】 {investment_debate['judge_decision'][:600]}")
            
            # 风险管理团队决策
            risk_debate = rd.get('risk_debate_state') or {}
            if risk_debate.get('risky_history') or risk_debate.get('current_risky_response'):
                risky_text = risk_debate.get('current_risky_response') or risk_debate.get('risky_history')
                summary_lines.append(f"【激进分析师】 {risky_text[:600]}")
            if risk_debate.get('safe_history') or risk_debate.get('current_safe_response'):
                safe_text = risk_debate.get('current_safe_response') or risk_debate.get('safe_history')
                summary_lines.append(f"【保守分析师】 {safe_text[:600]}")
            if risk_debate.get('neutral_history') or risk_debate.get('current_neutral_response'):
                neutral_text = risk_debate.get('current_neutral_response') or risk_debate.get('neutral_history')
                summary_lines.append(f"【中性分析师】 {neutral_text[:600]}")
            if risk_debate.get('judge_decision'):
                summary_lines.append(f"【投资组合经理决策】 {risk_debate['judge_decision'][:600]}")
        except Exception:
            pass

    body_text = "\n".join(summary_lines) if summary_lines else "No detailed summary available."

    # Generate a minimal valid PDF in-memory
    import io

    def _utf16be_hex(s: str) -> str:
        """Encode a string as UTF-16BE hex for PDF Type0 font."""
        try:
            data = s.encode("utf-16-be", errors="replace")
        except Exception:
            data = str(s).encode("utf-16-be", errors="replace")
        return "<" + (b"\xfe\xff" + data).hex().upper() + ">"

    def generate_pdf_bytes(title_text: str, meta_text: str, body: str) -> bytes:
        buf = io.BytesIO()
        objects = []  # (pos, bytes)

        def w(b: bytes):
            buf.write(b)

        w(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n")

        # 1: Catalog
        pos1 = buf.tell(); w(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        # 2: Pages
        pos2 = buf.tell(); w(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
        # 4: CJK-capable font (Type0 + UniGB-UCS2-H)
        pos4 = buf.tell(); w(
            b"4 0 obj\n"+
            b"<< /Type /Font /Subtype /Type0 /BaseFont /STSong-Light /Name /F1 "
            b"/Encoding /UniGB-UCS2-H /DescendantFonts [5 0 R] >>\nendobj\n"
        )
        # 5: Descendant CIDFont + descriptor (minimal)
        pos5 = buf.tell(); w(
            b"5 0 obj\n"+
            b"<< /Type /Font /Subtype /CIDFontType0 /BaseFont /STSong-Light "
            b"/CIDSystemInfo << /Registry (Adobe) /Ordering (GB1) /Supplement 4 >> "
            b"/FontDescriptor 6 0 R /DW 1000 >>\nendobj\n"
        )
        pos6 = buf.tell(); w(
            b"6 0 obj\n"+
            b"<< /Type /FontDescriptor /FontName /STSong-Light /Flags 4 "
            b"/FontBBox [-250 -250 1000 1000] /ItalicAngle 0 /Ascent 1000 /Descent -250 /CapHeight 800 /StemV 80 >>\nendobj\n"
        )

        # 5: Contents stream
        # Build page content stream (simple texts, line by line)
        lines = []
        lines.append("BT")
        lines.append("/F1 18 Tf")
        lines.append("72 740 Td")
        lines.append(f"{_utf16be_hex(title_text)} Tj")
        lines.append("/F1 11 Tf")
        lines.append("0 -24 Td")
        if meta_text:
            for meta_line in meta_text.split("\n"):
                lines.append(f"{_utf16be_hex(meta_line)} Tj")
                lines.append("0 -14 Td")
        if body:
            for body_line in body.split("\n"):
                safe = body_line[:1000]
                lines.append(f"{_utf16be_hex(safe)} Tj")
                lines.append("0 -14 Td")
        lines.append("ET")
        content_stream = "\n".join(lines).encode("ascii")
        pos7 = buf.tell()
        w(f"7 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode("ascii"))
        w(content_stream)
        w(b"\nendstream\nendobj\n")

        # 3: Page (after contents so we know refs exist)
        pos3 = buf.tell(); w(b"3 0 obj\n" +
                             b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] " +
                             b"/Contents 7 0 R /Resources << /Font << /F1 4 0 R >> >> >>\nendobj\n")

        # xref
        xref_pos = buf.tell()
        xref_entries = [0, pos1, pos2, pos3, pos4, pos5, pos6, pos7]
        w(b"xref\n0 8\n")
        w(b"0000000000 65535 f \n")
        for p in xref_entries[1:]:
            w(f"{p:010d} 00000 n \n".encode("ascii"))

        # trailer
        w(b"trailer\n")
        w(b"<< /Size 8 /Root 1 0 R >>\n")
        w(b"startxref\n")
        w(f"{xref_pos}\n".encode("ascii"))
        w(b"%%EOF\n")

        return buf.getvalue()

    meta_info = []
    if created:
        meta_info.append(f"Created: {created}")
    if completed:
        meta_info.append(f"Completed: {completed}")
    meta = "\n".join(meta_info)

    pdf_bytes = generate_pdf_bytes(title, meta, body_text)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=analysis_{stock}_report.pdf"
        }
    )


@router.get("/{analysis_id}/progress")
async def get_analysis_progress(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    Get analysis progress (polling endpoint)
    Returns detailed progress information for frontend polling
    """
    try:
        analysis_object_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID format"
        )
    
    # Get analysis from database
    analysis_doc = await db.analyses.find_one({"_id": analysis_object_id})
    if not analysis_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis = AnalysisInDB(**analysis_doc)
    
    # Check if user owns this analysis or is admin
    if str(analysis.user_id) != str(current_user.id) and "admin" not in current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get real-time progress from Redis
    progress_data = None
    redis_keys_to_try = [
        f"analysis_progress:{analysis_id}",  # React版本格式
        f"progress:{analysis_id}",           # 备用格式
        f"task_progress:analysis_{analysis_id}"  # TaskQueue格式
    ]
    
    for key in redis_keys_to_try:
        progress_data = await redis_client.get(key)
        if progress_data:
            break
    
    # 解析进度数据
    if progress_data:
        try:
            import json
            progress_info = json.loads(progress_data)
            
            # 返回兼容前端 SevenStepProgress 组件的格式
            # 优先使用 progress_percentage (0-1格式)，如果没有则从 progress (0-100) 转换
            progress_percentage = progress_info.get("progress_percentage")
            if progress_percentage is None:
                # fallback: 从progress字段转换
                progress_percentage = progress_info.get("progress", 0) / 100.0
            
            return {
                "analysis_id": analysis_id,
                "status": progress_info.get("status", analysis.status.value),
                "current_step": progress_info.get("current_step", 0),
                "total_steps": progress_info.get("total_steps", 7),
                "progress_percentage": progress_percentage,  # 0-1 的小数格式
                "message": progress_info.get("message", "正在分析..."),
                "elapsed_time": progress_info.get("elapsed_time", 0),
                "estimated_remaining": progress_info.get("estimated_time_remaining", progress_info.get("estimated_remaining", 0)),
                "current_step_name": progress_info.get("current_step_name") or progress_info.get("current_step") or "分析中",
                "timestamp": datetime.utcnow().timestamp(),
                # 🔧 新增：LLM分析结果
                "llm_result": progress_info.get("llm_result"),
                "analyst_type": progress_info.get("analyst_type")
            }
        except Exception as e:
            logger.warning(f"Failed to parse progress data from Redis: {e}")
    
    # Fallback to database data
    # 从数据库构造进度数据
    progress_percentage = analysis.progress / 100.0 if analysis.progress else 0.0
    
    # 根据进度估算当前步骤
    total_steps = 7
    current_step = int(progress_percentage * total_steps)
    
    # 计算已用时间
    elapsed_time = 0
    estimated_remaining = 0
    
    if analysis.started_at:
        elapsed_time = (datetime.utcnow() - analysis.started_at).total_seconds()
        
        # 根据当前进度估算剩余时间
        if analysis.progress and analysis.progress > 0:
            total_estimated_time = elapsed_time * (100.0 / analysis.progress)
            estimated_remaining = max(0, total_estimated_time - elapsed_time)
    
    # 根据状态返回消息
    status_messages = {
        "pending": "等待开始...",
        "running": "正在分析...",
        "completed": "分析完成",
        "failed": analysis.error_message or "分析失败",
        "cancelled": "已取消"
    }
    
    return {
        "analysis_id": analysis_id,
        "status": analysis.status.value,
        "current_step": current_step,
        "total_steps": total_steps,
        "progress_percentage": progress_percentage,
        "message": status_messages.get(analysis.status.value, "未知状态"),
        "elapsed_time": elapsed_time,
        "estimated_remaining": estimated_remaining,
        "current_step_name": f"步骤 {current_step + 1}/{total_steps}",
        "timestamp": datetime.utcnow().timestamp()
    }


@router.get("/{analysis_id}/status", response_model=AnalysisProgress)
async def get_analysis_status(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    Get analysis status and progress
    """
    try:
        analysis_object_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID format"
        )
    
    # Get analysis from database
    analysis_doc = await db.analyses.find_one({"_id": analysis_object_id})
    if not analysis_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis = AnalysisInDB(**analysis_doc)
    
    # Check if user owns this analysis or is admin
    if str(analysis.user_id) != str(current_user.id) and "admin" not in current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get real-time progress from Redis if available
    # 尝试多种Redis键格式，兼容不同版本
    progress_data = None
    redis_keys_to_try = [
        f"analysis_progress:{analysis_id}",  # React版本格式
        f"progress:{analysis_id}",           # 备用格式
        f"task_progress:analysis_{analysis_id}"  # TaskQueue格式
    ]
    
    for key in redis_keys_to_try:
        progress_data = await redis_client.get(key)
        if progress_data:
            break
    
    if progress_data:
        try:
            import json
            progress_info = json.loads(progress_data)
            
            # 兼容不同的数据格式
            status_value = progress_info.get("status", analysis.status.value)
            if isinstance(status_value, str):
                # 确保状态值正确映射
                status_mapping = {
                    'running': 'running',
                    'completed': 'completed', 
                    'failed': 'failed',
                    'pending': 'pending',
                    'cancelled': 'cancelled'
                }
                status_value = status_mapping.get(status_value, analysis.status.value)
            
            # 兼容不同的进度字段名 - 注意不能用or，因为0会被判断为False
            if "progress" in progress_info:
                progress_value = progress_info["progress"]
            elif "progress_percentage" in progress_info:
                # progress_percentage是0-1格式，需要转换为0-100
                progress_value = progress_info["progress_percentage"] * 100
            else:
                progress_value = analysis.progress
            
            # 兼容不同的步骤字段名
            current_step = progress_info.get("current_step") or progress_info.get("current_step_name")
            
            # 兼容不同的消息字段名
            message = progress_info.get("message") or progress_info.get("last_message")
            
            # 兼容不同的时间字段名
            estimated_time_remaining = progress_info.get("estimated_time_remaining") or progress_info.get("remaining_time")
            
            return AnalysisProgress(
                status=AnalysisStatus(status_value),
                progress=progress_value,
                current_step=current_step,
                message=message,
                estimated_time_remaining=estimated_time_remaining
            )
        except Exception as e:
            logger.warning(f"Failed to parse progress data: {e}")
            pass
    
    # Fallback to database data
    return AnalysisProgress(
        status=analysis.status,
        progress=analysis.progress,
        current_step=None,
        message=analysis.error_message if analysis.status == AnalysisStatus.FAILED else None
    )


@router.get("/{analysis_id}/result", response_model=Analysis)
async def get_analysis_result(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get analysis result
    """
    try:
        analysis_object_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID format"
        )
    
    # Get analysis from database
    analysis_doc = await db.analyses.find_one({"_id": analysis_object_id})
    if not analysis_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis = AnalysisInDB(**analysis_doc)
    
    # Check if user owns this analysis or is admin
    if str(analysis.user_id) != str(current_user.id) and "admin" not in current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if analysis is completed
    if analysis.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not completed. Current status: {analysis.status.value}"
        )
    
    return _convert_to_analysis_response(analysis)


@router.get("/{analysis_id}/results", response_model=Analysis)
async def get_analysis_results(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get analysis results (alias for /result endpoint for frontend compatibility)
    """
    return await get_analysis_result(analysis_id, current_user, db)


@router.get("/history", response_model=AnalysisListResponse)
async def get_analysis_history(
    stock_code: Optional[str] = None,
    market_type: Optional[MarketType] = None,
    status: Optional[AnalysisStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get analysis history with filtering and pagination
    """
    # Validate pagination parameters
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    
    # Build query filter - handle both ObjectId and string user_id formats
    user_id_query = {"$or": [
        {"user_id": current_user.id},  # ObjectId format
        {"user_id": str(current_user.id)},  # String format
        {"user_id": current_user.username}  # Username format (for legacy data)
    ]}
    query_filter = user_id_query
    
    if stock_code:
        query_filter["stock_code"] = stock_code.upper()
    
    if market_type:
        query_filter["market_type"] = market_type.value
    
    if status:
        query_filter["status"] = status.value
    
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        query_filter["created_at"] = date_filter
    
    # Get total count
    total = await db.analyses.count_documents(query_filter)
    
    # Get paginated results
    skip = (page - 1) * page_size
    cursor = db.analyses.find(query_filter).sort("created_at", -1).skip(skip).limit(page_size)
    
    analyses = []
    async for analysis_doc in cursor:
        analysis = AnalysisInDB(**analysis_doc)
        analyses.append(_convert_to_analysis_response(analysis))
    
    return AnalysisListResponse(
        analyses=analyses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_DELETE])),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    Delete an analysis record
    """
    try:
        analysis_object_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID format"
        )
    
    # Get analysis from database
    analysis_doc = await db.analyses.find_one({"_id": analysis_object_id})
    if not analysis_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis = AnalysisInDB(**analysis_doc)
    
    # Check if user owns this analysis or is admin
    if str(analysis.user_id) != str(current_user.id) and "admin" not in current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Cannot delete running analysis
    if analysis.status == AnalysisStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete running analysis. Please cancel it first."
        )
    
    # Delete from database
    await db.analyses.delete_one({"_id": analysis_object_id})
    
    # Clean up Redis cache
    await redis_client.delete(f"analysis_progress:{analysis_id}")
    await redis_client.delete(f"analysis_result:{analysis_id}")
    
    return {"message": "Analysis deleted successfully"}


@router.post("/{analysis_id}/cancel")
async def cancel_analysis(
    analysis_id: str,
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_UPDATE])),
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis_client = Depends(get_redis)
):
    """
    Cancel a running analysis
    """
    try:
        analysis_object_id = ObjectId(analysis_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis ID format"
        )
    
    # Get analysis from database
    analysis_doc = await db.analyses.find_one({"_id": analysis_object_id})
    if not analysis_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis = AnalysisInDB(**analysis_doc)
    
    # Check if user owns this analysis or is admin
    if str(analysis.user_id) != str(current_user.id) and "admin" not in current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Can only cancel pending or running analyses
    if analysis.status not in [AnalysisStatus.PENDING, AnalysisStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel analysis with status: {analysis.status.value}"
        )
    
    # Update status to cancelled
    await db.analyses.update_one(
        {"_id": analysis_object_id},
        {
            "$set": {
                "status": AnalysisStatus.CANCELLED.value,
                "completed_at": datetime.utcnow()
            }
        }
    )
    
    # Set cancellation flag in Redis
    await redis_client.setex(f"analysis_cancel:{analysis_id}", 3600, "true")
    
    return {"message": "Analysis cancellation requested"}


@router.get("/stats")
async def get_analysis_stats(
    current_user: UserInDB = Depends(require_permissions([Permissions.ANALYSIS_READ])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get analysis statistics for the current user
    """
    # Get status counts
    user_match = {"$or": [
        {"user_id": current_user.id},
        {"user_id": str(current_user.id)},
        {"user_id": current_user.username}
    ]}
    pipeline = [
        {"$match": user_match},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    
    status_counts = {}
    async for result in db.analyses.aggregate(pipeline):
        status_counts[result["_id"]] = result["count"]
    
    # Get recent activity (last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_count = await db.analyses.count_documents({
        **user_match,
        "created_at": {"$gte": thirty_days_ago}
    })
    
    # Get most analyzed stocks
    pipeline = [
        {"$match": user_match},
        {"$group": {"_id": "$stock_code", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    top_stocks = []
    async for result in db.analyses.aggregate(pipeline):
        top_stocks.append({
            "stock_code": result["_id"],
            "count": result["count"]
        })
    
    return {
        "status_counts": status_counts,
        "recent_activity": recent_count,
        "top_stocks": top_stocks,
        "total_analyses": sum(status_counts.values())
    }


@router.get("/queue/stats")
async def get_queue_stats(
    current_user: UserInDB = Depends(require_permissions([Permissions.ADMIN]))
):
    """
    Get task queue statistics (admin only)
    """
    from services.async_analysis_service import get_async_analysis_service
    
    async_analysis_service = await get_async_analysis_service()
    stats = await async_analysis_service.get_queue_stats()
    return stats


def _validate_stock_code(stock_code: str, market_type: MarketType) -> bool:
    """
    Validate stock code format based on market type
    """
    if not stock_code:
        return False
    
    stock_code = stock_code.upper()
    
    if market_type == MarketType.CN:
        # Chinese stocks: 6 digits (e.g., 000001, 600000)
        return len(stock_code) == 6 and stock_code.isdigit()
    elif market_type == MarketType.US:
        # US stocks: 1-5 letters (e.g., AAPL, MSFT, GOOGL)
        return 1 <= len(stock_code) <= 5 and stock_code.isalpha()
    elif market_type == MarketType.HK:
        # HK stocks: 4-5 digits (e.g., 0700, 00700)
        return 4 <= len(stock_code) <= 5 and stock_code.isdigit()
    
    return False


def _convert_to_analysis_response(analysis_db: AnalysisInDB) -> Analysis:
    """
    Convert database analysis model to API response model
    """
    return Analysis(
        id=str(analysis_db.id),
        user_id=str(analysis_db.user_id),
        stock_code=analysis_db.stock_code,
        market_type=analysis_db.market_type,
        status=analysis_db.status,
        progress=analysis_db.progress,
        config=analysis_db.config,
        result_data=analysis_db.result_data,
        error_message=analysis_db.error_message,
        created_at=analysis_db.created_at,
        started_at=analysis_db.started_at,
        completed_at=analysis_db.completed_at
    )
