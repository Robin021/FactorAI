#!/bin/bash

# 启动中文登录界面测试
echo "🚀 启动中文登录界面测试..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未找到，请先安装Python3"
    exit 1
fi

# 检查Streamlit
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "❌ Streamlit 未安装，正在安装..."
    pip3 install streamlit
fi

# 启动测试应用
echo "🌟 启动中文登录界面测试应用..."
echo "📱 浏览器将自动打开 http://localhost:8501"
echo "🔄 按 Ctrl+C 停止应用"
echo ""

streamlit run test_chinese_login.py --server.port 8501 --server.address localhost