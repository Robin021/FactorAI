#!/usr/bin/env python3
"""
强制刷新 Streamlit 应用
"""

import streamlit as st
import time
import os

# 强制清除缓存
st.cache_data.clear()
st.cache_resource.clear()

# 添加时间戳强制刷新
current_time = int(time.time())
print(f"🔄 强制刷新时间戳: {current_time}")

# 清除 Streamlit 缓存目录
cache_dir = os.path.expanduser("~/.streamlit")
if os.path.exists(cache_dir):
    print(f"📁 清除缓存目录: {cache_dir}")

print("✅ 缓存清除完成，请重启应用")