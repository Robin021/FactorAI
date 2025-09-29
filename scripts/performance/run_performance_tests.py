#!/usr/bin/env python3
"""
性能测试运行脚本
"""
import os
import sys
import subprocess
import argparse
import time
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def run_backend_performance_tests():
    """运行后端性能测试"""
    print("🚀 Running Backend Performance Tests...")
    
    # 安装性能测试依赖
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-r", 
        "backend/requirements-dev.txt"
    ], check=True)
    
    # 运行 pytest-benchmark 测试
    cmd = [
        "pytest", 
        "backend/tests/performance/test_api_performance.py",
        "--benchmark-only",
        "--benchmark-sort=mean",
        "--benchmark-json=performance_results/backend_benchmark.json",
        "--benchmark-columns=min,max,mean,stddev,rounds,iterations",
        "-v"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Backend performance tests completed successfully")
        print(result.stdout)
    else:
        print("❌ Backend performance tests failed")
        print(result.stderr)
        return False
    
    return True


def run_load_tests(host="http://localhost:8000"):
    """运行负载测试"""
    print(f"🔥 Running Load Tests against {host}...")
    
    # 检查 Locust 是否安装
    try:
        subprocess.run(["locust", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing Locust...")
        subprocess.run([sys.executable, "-m", "pip", "install", "locust"], check=True)
    
    # 运行压力测试
    cmd = [
        sys.executable,
        "backend/tests/performance/stress_test_runner.py",
        "--host", host,
        "--test", "all"
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ Load tests completed successfully")
    else:
        print("❌ Load tests failed")
        return False
    
    return True


def run_frontend_performance_tests():
    """运行前端性能测试"""
    print("🎨 Running Frontend Performance Tests...")
    
    # 切换到前端目录
    frontend_dir = project_root / "frontend"
    
    # 安装依赖
    subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
    
    # 运行性能测试
    test_commands = [
        # 运行单元测试
        ["npm", "run", "test", "--", "--run"],
        # 运行 Lighthouse CI (如果配置了)
        # ["npx", "lhci", "autorun"],
        # 构建并分析包大小
        ["npm", "run", "build"],
    ]
    
    for cmd in test_commands:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=frontend_dir)
        
        if result.returncode != 0:
            print(f"❌ Command failed: {' '.join(cmd)}")
            return False
    
    # 分析构建结果
    analyze_build_performance(frontend_dir)
    
    print("✅ Frontend performance tests completed")
    return True


def analyze_build_performance(frontend_dir):
    """分析构建性能"""
    dist_dir = frontend_dir / "dist"
    
    if not dist_dir.exists():
        print("⚠️ Build directory not found, skipping build analysis")
        return
    
    print("\n📊 Build Performance Analysis:")
    
    # 分析文件大小
    total_size = 0
    file_sizes = []
    
    for file_path in dist_dir.rglob("*"):
        if file_path.is_file():
            size = file_path.stat().st_size
            total_size += size
            
            if size > 100 * 1024:  # 大于100KB的文件
                file_sizes.append((file_path.name, size))
    
    # 排序并显示大文件
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Total build size: {total_size / 1024 / 1024:.2f} MB")
    print("\nLargest files:")
    for name, size in file_sizes[:10]:
        print(f"  {name}: {size / 1024:.1f} KB")
    
    # 检查是否有性能问题
    if total_size > 10 * 1024 * 1024:  # 10MB
        print("⚠️ Warning: Build size is quite large (>10MB)")
    
    # 检查是否有未压缩的大文件
    large_files = [f for f, s in file_sizes if s > 1024 * 1024]  # >1MB
    if large_files:
        print(f"⚠️ Warning: Found {len(large_files)} files larger than 1MB")


def setup_monitoring():
    """设置性能监控"""
    print("📈 Setting up Performance Monitoring...")
    
    # 创建结果目录
    results_dir = project_root / "performance_results"
    results_dir.mkdir(exist_ok=True)
    
    # 创建监控配置
    monitoring_config = {
        "collection_interval": 30,
        "alert_rules": [
            {
                "name": "High CPU Usage",
                "metric": "cpu_usage",
                "threshold": 80,
                "duration": 300
            },
            {
                "name": "High Memory Usage", 
                "metric": "memory_usage",
                "threshold": 85,
                "duration": 300
            }
        ]
    }
    
    config_file = results_dir / "monitoring_config.json"
    with open(config_file, "w") as f:
        json.dump(monitoring_config, f, indent=2)
    
    print(f"✅ Monitoring configuration saved to {config_file}")


def generate_performance_report():
    """生成性能测试报告"""
    print("📋 Generating Performance Report...")
    
    results_dir = project_root / "performance_results"
    
    if not results_dir.exists():
        print("⚠️ No performance results found")
        return
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests_run": [],
        "summary": {}
    }
    
    # 收集测试结果
    for result_file in results_dir.glob("*.json"):
        try:
            with open(result_file) as f:
                data = json.load(f)
                report["tests_run"].append({
                    "file": result_file.name,
                    "data": data
                })
        except Exception as e:
            print(f"⚠️ Failed to read {result_file}: {e}")
    
    # 生成报告
    report_file = results_dir / "performance_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Performance report saved to {report_file}")
    
    # 生成 HTML 报告
    generate_html_report(report, results_dir / "performance_report.html")


def generate_html_report(report_data, output_file):
    """生成 HTML 格式的性能报告"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Performance Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
            .section {{ margin: 20px 0; }}
            .metric {{ background: #fff; border: 1px solid #ddd; padding: 15px; margin: 10px 0; }}
            .success {{ color: #52c41a; }}
            .warning {{ color: #faad14; }}
            .error {{ color: #ff4d4f; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Performance Test Report</h1>
            <p>Generated: {report_data['timestamp']}</p>
        </div>
        
        <div class="section">
            <h2>Test Summary</h2>
            <p>Total tests run: {len(report_data['tests_run'])}</p>
        </div>
        
        <div class="section">
            <h2>Test Results</h2>
            {''.join([f'<div class="metric"><h3>{test["file"]}</h3><pre>{json.dumps(test["data"], indent=2)}</pre></div>' for test in report_data['tests_run']])}
        </div>
    </body>
    </html>
    """
    
    with open(output_file, "w") as f:
        f.write(html_content)
    
    print(f"✅ HTML report saved to {output_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Run performance tests")
    parser.add_argument("--backend", action="store_true", help="Run backend performance tests")
    parser.add_argument("--frontend", action="store_true", help="Run frontend performance tests")
    parser.add_argument("--load", action="store_true", help="Run load tests")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host for load tests")
    parser.add_argument("--all", action="store_true", help="Run all performance tests")
    parser.add_argument("--setup", action="store_true", help="Setup monitoring only")
    parser.add_argument("--report", action="store_true", help="Generate report only")
    
    args = parser.parse_args()
    
    # 创建结果目录
    os.makedirs("performance_results", exist_ok=True)
    
    success = True
    
    if args.setup:
        setup_monitoring()
        return
    
    if args.report:
        generate_performance_report()
        return
    
    if args.all or args.backend:
        success &= run_backend_performance_tests()
    
    if args.all or args.frontend:
        success &= run_frontend_performance_tests()
    
    if args.all or args.load:
        success &= run_load_tests(args.host)
    
    if not any([args.backend, args.frontend, args.load, args.all]):
        print("No tests specified. Use --help for options.")
        return
    
    # 设置监控
    setup_monitoring()
    
    # 生成报告
    generate_performance_report()
    
    if success:
        print("\n🎉 All performance tests completed successfully!")
    else:
        print("\n💥 Some performance tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()