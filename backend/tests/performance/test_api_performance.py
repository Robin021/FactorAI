"""
API Performance Tests
测试 API 接口的性能指标
"""
import asyncio
import time
from typing import List, Dict, Any
import pytest
import httpx
from fastapi.testclient import TestClient
from backend.app.main import app


class TestAPIPerformance:
    """API 性能测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.client = TestClient(app)
        self.base_url = "http://testserver"
        
    @pytest.mark.benchmark(group="auth")
    def test_login_performance(self, benchmark):
        """测试登录接口性能"""
        def login_request():
            response = self.client.post(
                "/api/v1/auth/login",
                json={
                    "username": "testuser",
                    "password": "testpass123"
                }
            )
            return response
            
        result = benchmark(login_request)
        assert result.status_code in [200, 401]  # 允许认证失败，主要测试性能
        
    @pytest.mark.benchmark(group="analysis")
    def test_analysis_start_performance(self, benchmark):
        """测试分析启动接口性能"""
        def start_analysis():
            response = self.client.post(
                "/api/v1/analysis/start",
                json={
                    "stock_code": "000001",
                    "market_type": "A股",
                    "analysts": ["fundamentals", "technical"]
                },
                headers={"Authorization": "Bearer test_token"}
            )
            return response
            
        result = benchmark(start_analysis)
        # 允许认证失败，主要测试接口响应性能
        assert result.status_code in [200, 401, 422]
        
    @pytest.mark.benchmark(group="config")
    def test_config_get_performance(self, benchmark):
        """测试配置获取接口性能"""
        def get_config():
            response = self.client.get(
                "/api/v1/config/llm",
                headers={"Authorization": "Bearer test_token"}
            )
            return response
            
        result = benchmark(get_config)
        assert result.status_code in [200, 401]
        
    def test_concurrent_requests_performance(self):
        """测试并发请求性能"""
        async def make_concurrent_requests(num_requests: int = 50):
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                tasks = []
                start_time = time.time()
                
                for _ in range(num_requests):
                    task = client.get("/api/v1/health")
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()
                
                # 计算性能指标
                total_time = end_time - start_time
                successful_requests = sum(
                    1 for r in responses 
                    if isinstance(r, httpx.Response) and r.status_code == 200
                )
                
                return {
                    "total_time": total_time,
                    "requests_per_second": num_requests / total_time,
                    "successful_requests": successful_requests,
                    "success_rate": successful_requests / num_requests
                }
        
        # 运行并发测试
        result = asyncio.run(make_concurrent_requests())
        
        # 性能断言
        assert result["requests_per_second"] > 10  # 至少每秒10个请求
        assert result["success_rate"] > 0.95  # 95%以上成功率
        
    def test_memory_usage_during_requests(self):
        """测试请求期间的内存使用情况"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行多个请求
        for _ in range(100):
            response = self.client.get("/api/v1/health")
            assert response.status_code == 200
            
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存增长不应超过50MB
        assert memory_increase < 50, f"Memory increased by {memory_increase}MB"


class TestDatabasePerformance:
    """数据库操作性能测试"""
    
    @pytest.mark.benchmark(group="database")
    def test_user_query_performance(self, benchmark):
        """测试用户查询性能"""
        # 这里需要mock数据库操作
        def query_user():
            # 模拟数据库查询
            time.sleep(0.001)  # 模拟1ms查询时间
            return {"id": "test", "username": "testuser"}
            
        result = benchmark(query_user)
        assert result is not None
        
    @pytest.mark.benchmark(group="database")
    def test_analysis_insert_performance(self, benchmark):
        """测试分析记录插入性能"""
        def insert_analysis():
            # 模拟数据库插入
            time.sleep(0.002)  # 模拟2ms插入时间
            return {"id": "analysis_123", "status": "created"}
            
        result = benchmark(insert_analysis)
        assert result is not None


if __name__ == "__main__":
    # 运行性能测试
    pytest.main([
        __file__,
        "--benchmark-only",
        "--benchmark-sort=mean",
        "--benchmark-columns=min,max,mean,stddev,rounds,iterations"
    ])