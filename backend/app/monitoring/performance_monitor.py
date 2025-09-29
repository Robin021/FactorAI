"""
性能监控和报警系统
"""
import time
import asyncio
import psutil
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque, defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    timestamp: float
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


@dataclass
class AlertRule:
    """报警规则"""
    name: str
    metric_name: str
    threshold: float
    operator: str  # '>', '<', '>=', '<=', '=='
    duration: int  # 持续时间（秒）
    severity: str  # 'low', 'medium', 'high', 'critical'
    enabled: bool = True


class PerformanceCollector:
    """性能数据收集器"""
    
    def __init__(self):
        self.process = psutil.Process()
        
    def collect_system_metrics(self) -> List[PerformanceMetric]:
        """收集系统性能指标"""
        metrics = []
        now = time.time()
        
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(PerformanceMetric(
            timestamp=now,
            metric_name="system.cpu.usage",
            value=cpu_percent,
            unit="percent"
        ))
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        metrics.append(PerformanceMetric(
            timestamp=now,
            metric_name="system.memory.usage",
            value=memory.percent,
            unit="percent"
        ))
        
        metrics.append(PerformanceMetric(
            timestamp=now,
            metric_name="system.memory.available",
            value=memory.available / 1024 / 1024,  # MB
            unit="MB"
        ))
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        metrics.append(PerformanceMetric(
            timestamp=now,
            metric_name="system.disk.usage",
            value=(disk.used / disk.total) * 100,
            unit="percent"
        ))
        
        return metrics
    
    def collect_process_metrics(self) -> List[PerformanceMetric]:
        """收集进程性能指标"""
        metrics = []
        now = time.time()
        
        try:
            # 进程 CPU 使用率
            cpu_percent = self.process.cpu_percent()
            metrics.append(PerformanceMetric(
                timestamp=now,
                metric_name="process.cpu.usage",
                value=cpu_percent,
                unit="percent"
            ))
            
            # 进程内存使用
            memory_info = self.process.memory_info()
            metrics.append(PerformanceMetric(
                timestamp=now,
                metric_name="process.memory.rss",
                value=memory_info.rss / 1024 / 1024,  # MB
                unit="MB"
            ))
            
            metrics.append(PerformanceMetric(
                timestamp=now,
                metric_name="process.memory.vms",
                value=memory_info.vms / 1024 / 1024,  # MB
                unit="MB"
            ))
            
            # 文件描述符数量
            num_fds = self.process.num_fds()
            metrics.append(PerformanceMetric(
                timestamp=now,
                metric_name="process.file_descriptors",
                value=num_fds,
                unit="count"
            ))
            
            # 线程数量
            num_threads = self.process.num_threads()
            metrics.append(PerformanceMetric(
                timestamp=now,
                metric_name="process.threads",
                value=num_threads,
                unit="count"
            ))
            
        except psutil.NoSuchProcess:
            logger.warning("Process no longer exists")
        except Exception as e:
            logger.error(f"Error collecting process metrics: {e}")
            
        return metrics


class APIPerformanceTracker:
    """API 性能跟踪器"""
    
    def __init__(self, max_history: int = 1000):
        self.request_history = deque(maxlen=max_history)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'error_count': 0
        })
    
    def track_request(self, endpoint: str, method: str, duration: float, 
                     status_code: int, error: Optional[str] = None):
        """跟踪API请求"""
        now = time.time()
        
        # 记录请求历史
        self.request_history.append({
            'timestamp': now,
            'endpoint': endpoint,
            'method': method,
            'duration': duration,
            'status_code': status_code,
            'error': error
        })
        
        # 更新端点统计
        key = f"{method} {endpoint}"
        stats = self.endpoint_stats[key]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['min_time'] = min(stats['min_time'], duration)
        stats['max_time'] = max(stats['max_time'], duration)
        
        if status_code >= 400 or error:
            stats['error_count'] += 1
    
    def get_metrics(self) -> List[PerformanceMetric]:
        """获取API性能指标"""
        metrics = []
        now = time.time()
        
        for endpoint, stats in self.endpoint_stats.items():
            if stats['count'] > 0:
                avg_time = stats['total_time'] / stats['count']
                error_rate = stats['error_count'] / stats['count'] * 100
                
                metrics.extend([
                    PerformanceMetric(
                        timestamp=now,
                        metric_name="api.response_time.avg",
                        value=avg_time,
                        unit="ms",
                        tags={'endpoint': endpoint}
                    ),
                    PerformanceMetric(
                        timestamp=now,
                        metric_name="api.response_time.max",
                        value=stats['max_time'],
                        unit="ms",
                        tags={'endpoint': endpoint}
                    ),
                    PerformanceMetric(
                        timestamp=now,
                        metric_name="api.error_rate",
                        value=error_rate,
                        unit="percent",
                        tags={'endpoint': endpoint}
                    ),
                    PerformanceMetric(
                        timestamp=now,
                        metric_name="api.request_count",
                        value=stats['count'],
                        unit="count",
                        tags={'endpoint': endpoint}
                    )
                ])
        
        return metrics


class AlertManager:
    """报警管理器"""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Dict] = {}
        self.alert_history = deque(maxlen=1000)
        
    def add_rule(self, rule: AlertRule):
        """添加报警规则"""
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def check_alerts(self, metrics: List[PerformanceMetric]):
        """检查报警条件"""
        now = time.time()
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            # 查找匹配的指标
            matching_metrics = [m for m in metrics if m.metric_name == rule.metric_name]
            
            for metric in matching_metrics:
                alert_key = f"{rule.name}_{metric.tags.get('endpoint', 'global')}"
                
                # 检查阈值
                triggered = self._check_threshold(metric.value, rule.threshold, rule.operator)
                
                if triggered:
                    if alert_key not in self.active_alerts:
                        # 新报警
                        self.active_alerts[alert_key] = {
                            'rule': rule,
                            'metric': metric,
                            'start_time': now,
                            'last_triggered': now
                        }
                        logger.warning(f"Alert triggered: {rule.name}")
                    else:
                        # 更新现有报警
                        self.active_alerts[alert_key]['last_triggered'] = now
                        
                        # 检查是否达到持续时间
                        duration = now - self.active_alerts[alert_key]['start_time']
                        if duration >= rule.duration:
                            self._send_alert(alert_key, self.active_alerts[alert_key])
                else:
                    # 报警恢复
                    if alert_key in self.active_alerts:
                        self._resolve_alert(alert_key, self.active_alerts[alert_key])
                        del self.active_alerts[alert_key]
    
    def _check_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """检查阈值条件"""
        if operator == '>':
            return value > threshold
        elif operator == '<':
            return value < threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '==':
            return value == threshold
        return False
    
    def _send_alert(self, alert_key: str, alert_data: Dict):
        """发送报警"""
        rule = alert_data['rule']
        metric = alert_data['metric']
        
        alert_message = {
            'alert_key': alert_key,
            'rule_name': rule.name,
            'severity': rule.severity,
            'metric_name': metric.metric_name,
            'current_value': metric.value,
            'threshold': rule.threshold,
            'timestamp': time.time(),
            'tags': metric.tags
        }
        
        # 记录到历史
        self.alert_history.append(alert_message)
        
        # 发送通知（这里可以集成邮件、短信、Slack等）
        logger.critical(f"ALERT: {rule.name} - {metric.metric_name} = {metric.value} {metric.unit}")
        
        # TODO: 集成实际的通知系统
        self._notify_alert(alert_message)
    
    def _resolve_alert(self, alert_key: str, alert_data: Dict):
        """解决报警"""
        rule = alert_data['rule']
        logger.info(f"Alert resolved: {rule.name}")
        
        # TODO: 发送恢复通知
    
    def _notify_alert(self, alert_message: Dict):
        """发送报警通知"""
        # 这里可以集成各种通知渠道
        # 例如：邮件、短信、Slack、钉钉等
        pass


class PerformanceMonitor:
    """性能监控主类"""
    
    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.collector = PerformanceCollector()
        self.api_tracker = APIPerformanceTracker()
        self.alert_manager = AlertManager()
        self.running = False
        
        # 设置默认报警规则
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """设置默认报警规则"""
        default_rules = [
            AlertRule(
                name="High CPU Usage",
                metric_name="system.cpu.usage",
                threshold=80.0,
                operator=">",
                duration=300,  # 5分钟
                severity="high"
            ),
            AlertRule(
                name="High Memory Usage",
                metric_name="system.memory.usage",
                threshold=85.0,
                operator=">",
                duration=300,
                severity="high"
            ),
            AlertRule(
                name="Slow API Response",
                metric_name="api.response_time.avg",
                threshold=5000.0,  # 5秒
                operator=">",
                duration=60,  # 1分钟
                severity="medium"
            ),
            AlertRule(
                name="High API Error Rate",
                metric_name="api.error_rate",
                threshold=10.0,  # 10%
                operator=">",
                duration=120,  # 2分钟
                severity="high"
            )
        ]
        
        for rule in default_rules:
            self.alert_manager.add_rule(rule)
    
    async def start_monitoring(self):
        """开始监控"""
        self.running = True
        logger.info("Performance monitoring started")
        
        while self.running:
            try:
                # 收集性能指标
                metrics = []
                metrics.extend(self.collector.collect_system_metrics())
                metrics.extend(self.collector.collect_process_metrics())
                metrics.extend(self.api_tracker.get_metrics())
                
                # 检查报警
                self.alert_manager.check_alerts(metrics)
                
                # 等待下次收集
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(5)  # 错误时短暂等待
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        logger.info("Performance monitoring stopped")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标"""
        metrics = []
        metrics.extend(self.collector.collect_system_metrics())
        metrics.extend(self.collector.collect_process_metrics())
        metrics.extend(self.api_tracker.get_metrics())
        
        return {
            'timestamp': time.time(),
            'metrics': [asdict(m) for m in metrics],
            'active_alerts': len(self.alert_manager.active_alerts),
            'alert_history': list(self.alert_manager.alert_history)[-10:]  # 最近10条
        }


# 全局监控实例
performance_monitor = PerformanceMonitor()