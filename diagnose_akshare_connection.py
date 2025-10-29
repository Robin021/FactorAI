#!/usr/bin/env python3
"""诊断 akshare 连接问题"""

import time
import akshare as ak

print("=" * 80)
print("AKShare 连接诊断工具")
print("=" * 80)

print(f"\n📦 AKShare 版本: {ak.__version__}")

# 测试1：基础连接测试
print("\n🔍 测试1：尝试获取A股实时行情...")
for i in range(3):
    try:
        print(f"   尝试 {i+1}/3...", end=" ")
        df = ak.stock_zh_a_spot_em()
        print(f"✅ 成功！获取到 {len(df)} 只股票")
        print(f"   前3只股票: {df['名称'].head(3).tolist()}")
        break
    except Exception as e:
        print(f"❌ 失败: {type(e).__name__}")
        if i < 2:
            print(f"   等待 {(i+1)*2} 秒后重试...")
            time.sleep((i+1)*2)
        else:
            print(f"   详细错误: {e}")

# 测试2：测试其他 akshare 接口
print("\n🔍 测试2：尝试获取上证指数数据...")
try:
    df = ak.stock_zh_index_daily(symbol="sh000001")
    print(f"✅ 成功！获取到 {len(df)} 条数据")
    print(f"   最新日期: {df['日期'].iloc[-1]}")
except Exception as e:
    print(f"❌ 失败: {type(e).__name__}: {e}")

# 测试3：网络连接测试
print("\n🔍 测试3：测试网络连接...")
import socket
try:
    # 测试DNS解析
    host = "push2.eastmoney.com"
    ip = socket.gethostbyname(host)
    print(f"✅ DNS解析成功: {host} -> {ip}")
    
    # 测试端口连接
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((host, 80))
    if result == 0:
        print(f"✅ 端口80连接成功")
    else:
        print(f"❌ 端口80连接失败")
    sock.close()
except Exception as e:
    print(f"❌ 网络测试失败: {e}")

# 诊断建议
print("\n" + "=" * 80)
print("📋 诊断建议")
print("=" * 80)
print("""
如果所有测试都失败，可能的原因：

1. 🌐 网络问题
   - 检查是否能访问外网
   - 尝试使用VPN或代理
   - 检查防火墙设置

2. 🚫 API限流
   - 东方财富网可能限制访问频率
   - 等待10-30分钟后重试
   - 避免短时间内频繁请求

3. 🔧 环境问题
   - 更新 akshare: pip install -U akshare
   - 检查 requests 版本: pip install -U requests
   - 尝试重启Python环境

4. 📅 时间问题
   - 非交易时间数据可能不完整
   - 周末和节假日无法获取实时数据

5. ✅ 使用默认值
   - 系统已配置容错机制
   - 无法获取数据时会使用默认值（正常市场）
   - 不影响系统正常运行
""")

print("=" * 80)
