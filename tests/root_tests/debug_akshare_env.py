#!/usr/bin/env python3
"""
调试 akshare 在不同环境下的行为差异
"""

import sys
import os

print("=" * 80)
print("🔍 环境信息对比")
print("=" * 80)

# 1. Python 路径
print("\n📁 Python 路径:")
for i, path in enumerate(sys.path[:5]):
    print(f"   {i+1}. {path}")

# 2. 工作目录
print(f"\n📂 当前工作目录: {os.getcwd()}")

# 3. 环境变量
print(f"\n🌍 关键环境变量:")
for key in ['PYTHONPATH', 'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    value = os.environ.get(key, '未设置')
    print(f"   {key}: {value}")

# 4. 测试 akshare 导入
print("\n📦 测试 akshare 导入...")
try:
    import akshare as ak
    print(f"   ✅ akshare 版本: {ak.__version__}")
    print(f"   ✅ akshare 路径: {ak.__file__}")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")

# 5. 测试 requests 配置
print("\n🌐 测试 requests 配置...")
try:
    import requests
    session = requests.Session()
    print(f"   ✅ requests 版本: {requests.__version__}")
    print(f"   ✅ User-Agent: {session.headers.get('User-Agent', '未设置')}")
    
    # 检查是否有代理
    proxies = session.proxies
    if proxies:
        print(f"   ⚠️ 检测到代理配置: {proxies}")
    else:
        print(f"   ✅ 无代理配置")
        
except Exception as e:
    print(f"   ❌ 检查失败: {e}")

# 6. 测试简单的 HTTP 请求
print("\n🔗 测试 HTTP 请求...")
try:
    import requests
    # 测试访问东方财富
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "1",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "fields": "f12,f14"
    }
    
    response = requests.get(url, params=params, timeout=5)
    print(f"   ✅ HTTP 请求成功")
    print(f"   ✅ 状态码: {response.status_code}")
    print(f"   ✅ Content-Type: {response.headers.get('Content-Type', '未知')}")
    
    # 检查响应内容
    content_preview = response.text[:100]
    if content_preview.startswith('<'):
        print(f"   ⚠️ 响应是 HTML: {content_preview}")
    else:
        print(f"   ✅ 响应是 JSON")
        
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

print("\n" + "=" * 80)
