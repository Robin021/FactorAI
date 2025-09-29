"""
Locust 压力测试配置
用于测试并发分析任务的处理能力
"""
import json
import random
from locust import HttpUser, task, between, events
from locust.exception import StopUser


class AnalysisUser(HttpUser):
    """模拟分析用户的行为"""
    
    wait_time = between(1, 3)  # 用户操作间隔1-3秒
    
    def on_start(self):
        """用户开始时的初始化操作"""
        self.login()
        
    def login(self):
        """用户登录"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": f"testuser_{random.randint(1, 1000)}",
            "password": "testpass123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # 如果登录失败，使用模拟token
            self.token = "test_token"
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def start_analysis(self):
        """启动股票分析任务"""
        stock_codes = ["000001", "000002", "600000", "600036", "000858"]
        analysts = [
            ["fundamentals"],
            ["technical"],
            ["fundamentals", "technical"],
            ["market", "risk"]
        ]
        
        payload = {
            "stock_code": random.choice(stock_codes),
            "market_type": "A股",
            "analysts": random.choice(analysts),
            "llm_config": {
                "provider": "openai",
                "model": "gpt-3.5-turbo"
            }
        }
        
        with self.client.post(
            "/api/v1/analysis/start",
            json=payload,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.analysis_id = data.get("analysis_id")
                response.success()
            elif response.status_code == 401:
                response.failure("Authentication failed")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(2)
    def check_analysis_status(self):
        """检查分析状态"""
        if hasattr(self, 'analysis_id') and self.analysis_id:
            with self.client.get(
                f"/api/v1/analysis/{self.analysis_id}/status",
                headers=self.headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.success()  # 分析不存在也是正常情况
                else:
                    response.failure(f"Status check failed: {response.status_code}")
    
    @task(1)
    def get_analysis_history(self):
        """获取分析历史"""
        with self.client.get(
            "/api/v1/analysis/history",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"History request failed: {response.status_code}")
    
    @task(1)
    def get_llm_config(self):
        """获取LLM配置"""
        with self.client.get(
            "/api/v1/config/llm",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Config request failed: {response.status_code}")


class WebSocketUser(HttpUser):
    """WebSocket 连接测试用户"""
    
    wait_time = between(5, 10)
    
    def on_start(self):
        """建立WebSocket连接"""
        # 注意：Locust对WebSocket支持有限，这里主要测试HTTP升级请求
        pass
    
    @task
    def websocket_upgrade_request(self):
        """模拟WebSocket升级请求"""
        headers = {
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            "Sec-WebSocket-Version": "13"
        }
        
        with self.client.get(
            "/api/v1/ws/notifications",
            headers=headers,
            catch_response=True
        ) as response:
            # WebSocket升级请求通常返回101或400+
            if response.status_code in [101, 400, 426]:
                response.success()
            else:
                response.failure(f"WebSocket upgrade failed: {response.status_code}")


# 性能监控事件处理
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """请求事件监听器"""
    if exception:
        print(f"Request failed: {name} - {exception}")
    elif response_time > 5000:  # 超过5秒的请求
        print(f"Slow request detected: {name} - {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始事件"""
    print("=== 压力测试开始 ===")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束事件"""
    print("=== 压力测试结束 ===")
    
    # 输出性能统计
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")


# 自定义用户类权重
class StressTestUsers(HttpUser):
    """压力测试用户组合"""
    
    # 80%分析用户，20%WebSocket用户
    tasks = {
        AnalysisUser: 8,
        WebSocketUser: 2
    }
    
    wait_time = between(1, 5)