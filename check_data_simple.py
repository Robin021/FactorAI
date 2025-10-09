#!/usr/bin/env python3
"""
简单检查数据问题
"""
import json
import os
from pathlib import Path

def check_data():
    """检查数据"""
    
    print("🔍 开始检查数据...")
    
    # 1. 检查文件系统数据
    print("\n📁 检查文件系统数据...")
    data_dir = Path("data")
    
    if data_dir.exists():
        print(f"✅ data目录存在: {data_dir}")
        
        # 检查分析结果目录
        results_dir = data_dir / "analysis_results"
        if results_dir.exists():
            print(f"✅ 分析结果目录存在: {results_dir}")
            
            # 统计文件数量
            json_files = list(results_dir.rglob("*.json"))
            md_files = list(results_dir.rglob("*.md"))
            
            print(f"  JSON文件数量: {len(json_files)}")
            print(f"  Markdown文件数量: {len(md_files)}")
            
            # 显示目录结构
            print("\n  目录结构:")
            for root, dirs, files in os.walk(results_dir):
                level = root.replace(str(results_dir), '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files[:3]:  # 只显示前3个文件
                    print(f"{subindent}{file}")
                if len(files) > 3:
                    print(f"{subindent}... 还有 {len(files) - 3} 个文件")
        else:
            print("❌ 分析结果目录不存在")
            
        # 检查sessions目录
        sessions_dir = data_dir / "sessions"
        if sessions_dir.exists():
            print(f"\n✅ sessions目录存在: {sessions_dir}")
            session_files = list(sessions_dir.glob("*.json"))
            print(f"  会话文件数量: {len(session_files)}")
            
            # 检查是否有包含目标UUID的会话
            target_uuid = "16fce083-1a14-4bf7-b2d7-bd77597a2725"
            print(f"\n🎯 查找UUID: {target_uuid}")
            
            found = False
            for session_file in session_files:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if target_uuid in content:
                            print(f"  ✅ 在会话文件中找到: {session_file}")
                            
                            # 解析JSON查看详细信息
                            f.seek(0)
                            session_data = json.load(f)
                            print(f"    会话ID: {session_data.get('session_id')}")
                            print(f"    创建时间: {session_data.get('created_at')}")
                            print(f"    股票代码: {session_data.get('stock_code')}")
                            print(f"    状态: {session_data.get('status')}")
                            found = True
                            break
                except Exception as e:
                    continue
            
            if not found:
                print(f"  ❌ 在会话文件中未找到UUID: {target_uuid}")
        else:
            print("❌ sessions目录不存在")
    else:
        print("❌ data目录不存在")
    
    # 2. 检查前端构建文件
    print("\n🌐 检查前端...")
    frontend_dir = Path("frontend")
    if frontend_dir.exists():
        dist_dir = frontend_dir / "dist"
        if dist_dir.exists():
            print("✅ 前端已构建")
        else:
            print("❌ 前端未构建，可能需要运行 npm run build")
    else:
        print("❌ frontend目录不存在")
    
    # 3. 检查后端配置
    print("\n⚙️ 检查后端配置...")
    backend_dir = Path("backend")
    if backend_dir.exists():
        env_file = backend_dir / ".env"
        if env_file.exists():
            print("✅ 后端环境配置存在")
        else:
            print("❌ 后端环境配置不存在")
            
        requirements_file = backend_dir / "requirements.txt"
        if requirements_file.exists():
            print("✅ 依赖文件存在")
        else:
            print("❌ 依赖文件不存在")
    else:
        print("❌ backend目录不存在")
    
    # 4. 提供解决方案
    print("\n🔧 问题分析和解决方案:")
    print("1. 分析ID不匹配问题:")
    print("   - 前端显示的UUID格式ID可能来自旧系统")
    print("   - 后端API只能处理MongoDB的ObjectId格式")
    print("   - 需要数据迁移或清理前端缓存")
    print()
    print("2. 建议的修复步骤:")
    print("   a) 清理浏览器缓存和localStorage")
    print("   b) 重启MongoDB服务")
    print("   c) 运行数据迁移脚本")
    print("   d) 重启后端和前端服务")
    print()
    print("3. 清理命令:")
    print("   # 在浏览器控制台执行:")
    print("   localStorage.clear(); sessionStorage.clear(); location.reload();")

if __name__ == "__main__":
    check_data()