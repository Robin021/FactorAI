"""
性能监控 API 端点
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from pydantic import BaseModel
from backend.app.monitoring.performance_monitor import performance_monitor
from backend.core.auth import get_current_user

router = APIRouter(prefix="/performance", tags=["performance"])


class FrontendMetrics(BaseModel):
    """前端性能指标模型"""
    loadTime: float
    domContentLoaded: float
    firstContentfulPaint: float
    largestContentfulPaint: float
    firstInputDelay: float
    cumulativeLayoutShift: float
    memoryUsage: float = None
    timestamp: int
    userAgent: str
    url: str


class AlertRuleCreate(BaseModel):
    """创建报警规则模型"""
    name: str
    metric_name: str
    threshold: float
    operator: str
    duration: int
    severity: str


@router.get("/metrics")
async def get_performance_metrics(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前性能指标"""
    try:
        metrics = performance_monitor.get_current_metrics()
        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/metrics")
async def report_frontend_metrics(
    metrics: FrontendMetrics
) -> Dict[str, str]:
    """接收前端性能指标"""
    try:
        # 这里可以将前端指标存储到数据库或发送到监控系统
        # 暂时只记录日志
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Frontend metrics received: {metrics.dict()}")
        
        # 检查性能阈值
        if metrics.loadTime > 5000:  # 5秒
            logger.warning(f"Slow page load detected: {metrics.loadTime}ms for {metrics.url}")
        
        if metrics.largestContentfulPaint > 4000:  # 4秒
            logger.warning(f"Poor LCP detected: {metrics.largestContentfulPaint}ms for {metrics.url}")
        
        if metrics.cumulativeLayoutShift > 0.25:
            logger.warning(f"Poor CLS detected: {metrics.cumulativeLayoutShift} for {metrics.url}")
        
        return {"message": "Metrics received successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process metrics: {str(e)}")


@router.get("/alerts")
async def get_active_alerts(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取活跃的报警"""
    try:
        active_alerts = performance_monitor.alert_manager.active_alerts
        alert_history = list(performance_monitor.alert_manager.alert_history)[-20:]  # 最近20条
        
        return {
            "success": True,
            "data": {
                "active_alerts": active_alerts,
                "alert_history": alert_history
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.post("/alerts/rules")
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    current_user = Depends(get_current_user)
) -> Dict[str, str]:
    """创建报警规则"""
    try:
        from backend.app.monitoring.performance_monitor import AlertRule
        
        rule = AlertRule(
            name=rule_data.name,
            metric_name=rule_data.metric_name,
            threshold=rule_data.threshold,
            operator=rule_data.operator,
            duration=rule_data.duration,
            severity=rule_data.severity
        )
        
        performance_monitor.alert_manager.add_rule(rule)
        
        return {"message": "Alert rule created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert rule: {str(e)}")


@router.get("/alerts/rules")
async def get_alert_rules(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取报警规则列表"""
    try:
        rules = performance_monitor.alert_manager.rules
        
        rules_data = []
        for rule in rules:
            rules_data.append({
                "name": rule.name,
                "metric_name": rule.metric_name,
                "threshold": rule.threshold,
                "operator": rule.operator,
                "duration": rule.duration,
                "severity": rule.severity,
                "enabled": rule.enabled
            })
        
        return {
            "success": True,
            "data": rules_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert rules: {str(e)}")


@router.get("/health")
async def performance_health_check() -> Dict[str, Any]:
    """性能监控健康检查"""
    try:
        import psutil
        
        # 获取基本系统信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status = "healthy"
        issues = []
        
        # 检查健康状态
        if cpu_percent > 90:
            health_status = "warning"
            issues.append(f"High CPU usage: {cpu_percent}%")
        
        if memory.percent > 90:
            health_status = "critical"
            issues.append(f"High memory usage: {memory.percent}%")
        
        if (disk.used / disk.total) * 100 > 90:
            health_status = "warning"
            issues.append(f"High disk usage: {(disk.used / disk.total) * 100:.1f}%")
        
        return {
            "status": health_status,
            "timestamp": performance_monitor.get_current_metrics()["timestamp"],
            "system": {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": (disk.used / disk.total) * 100,
                "available_memory": memory.available / 1024 / 1024  # MB
            },
            "issues": issues,
            "monitoring_active": performance_monitor.running
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }