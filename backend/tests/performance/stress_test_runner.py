"""
压力测试运行器
自动化运行不同场景的压力测试
"""
import subprocess
import time
import json
import os
from typing import Dict, List, Any
import requests


class StressTestRunner:
    """压力测试运行器"""
    
    def __init__(self, host: str = "http://localhost:8000"):
        self.host = host
        self.results_dir = "performance_results"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def run_load_test(self, users: int, spawn_rate: int, duration: str, test_name: str) -> Dict[str, Any]:
        """运行负载测试"""
        print(f"Running load test: {test_name}")
        print(f"Users: {users}, Spawn rate: {spawn_rate}, Duration: {duration}")
        
        # 构建Locust命令
        cmd = [
            "locust",
            "-f", "backend/tests/performance/locustfile.py",
            "--host", self.host,
            "--users", str(users),
            "--spawn-rate", str(spawn_rate),
            "--run-time", duration,
            "--headless",
            "--html", f"{self.results_dir}/{test_name}_report.html",
            "--csv", f"{self.results_dir}/{test_name}"
        ]
        
        # 运行测试
        start_time = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            end_time = time.time()
            
            return {
                "test_name": test_name,
                "duration": end_time - start_time,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "test_name": test_name,
                "duration": 300,
                "success": False,
                "error": "Test timed out"
            }
    
    def run_spike_test(self) -> Dict[str, Any]:
        """运行峰值测试"""
        return self.run_load_test(
            users=100,
            spawn_rate=50,
            duration="2m",
            test_name="spike_test"
        )
    
    def run_endurance_test(self) -> Dict[str, Any]:
        """运行耐久性测试"""
        return self.run_load_test(
            users=20,
            spawn_rate=2,
            duration="10m",
            test_name="endurance_test"
        )
    
    def run_concurrent_analysis_test(self) -> Dict[str, Any]:
        """运行并发分析测试"""
        return self.run_load_test(
            users=50,
            spawn_rate=10,
            duration="5m",
            test_name="concurrent_analysis"
        )
    
    def check_server_health(self) -> bool:
        """检查服务器健康状态"""
        try:
            response = requests.get(f"{self.host}/api/v1/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """运行所有性能测试"""
        if not self.check_server_health():
            print("Server is not healthy, skipping tests")
            return []
        
        tests = [
            ("Spike Test", self.run_spike_test),
            ("Endurance Test", self.run_endurance_test),
            ("Concurrent Analysis Test", self.run_concurrent_analysis_test)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{'='*50}")
            print(f"Running {test_name}")
            print(f"{'='*50}")
            
            result = test_func()
            results.append(result)
            
            if result["success"]:
                print(f"✅ {test_name} completed successfully")
            else:
                print(f"❌ {test_name} failed")
                if "error" in result:
                    print(f"Error: {result['error']}")
            
            # 测试间隔
            time.sleep(10)
        
        # 保存测试结果
        self.save_test_summary(results)
        return results
    
    def save_test_summary(self, results: List[Dict[str, Any]]):
        """保存测试摘要"""
        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "host": self.host,
            "results": results
        }
        
        with open(f"{self.results_dir}/test_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nTest summary saved to {self.results_dir}/test_summary.json")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run performance stress tests")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host")
    parser.add_argument("--test", choices=["spike", "endurance", "concurrent", "all"], 
                       default="all", help="Test type to run")
    
    args = parser.parse_args()
    
    runner = StressTestRunner(args.host)
    
    if args.test == "spike":
        result = runner.run_spike_test()
    elif args.test == "endurance":
        result = runner.run_endurance_test()
    elif args.test == "concurrent":
        result = runner.run_concurrent_analysis_test()
    else:
        results = runner.run_all_tests()
        return
    
    print(f"Test completed: {result}")


if __name__ == "__main__":
    main()