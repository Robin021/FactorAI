#!/bin/bash

echo "🚀 启动详细分析进度测试"

# 启动简单后端服务
echo "🚀 启动简单后端服务..."
python start_simple_backend.py &
BACKEND_PID=$!

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 3

# 检查后端是否运行
echo "📡 检查后端服务..."
if ! curl -s http://localhost:8001/health > /dev/null; then
    echo "❌ 后端服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ 后端服务正常"

# 启动Python测试脚本
echo "🐍 启动Python进度监控..."
python test_detailed_progress.py &
PYTHON_PID=$!

# 等待一下让Python脚本启动
sleep 2

# 打开HTML测试页面
echo "🌐 打开HTML测试页面..."
if command -v open > /dev/null; then
    # macOS
    open test_progress_display.html
elif command -v xdg-open > /dev/null; then
    # Linux
    xdg-open test_progress_display.html
elif command -v start > /dev/null; then
    # Windows
    start test_progress_display.html
else
    echo "请手动打开 test_progress_display.html 文件"
fi

echo ""
echo "📊 测试说明："
echo "1. Python脚本会在终端显示详细的进度信息"
echo "2. HTML页面提供可视化的进度监控界面"
echo "3. 你可以在HTML页面中点击'开始分析'按钮"
echo "4. 观察两个界面的进度显示是否详细和同步"
echo ""
echo "按 Ctrl+C 停止测试"

# 等待用户中断
wait $PYTHON_PID

# 清理后端进程
echo "🧹 清理后端进程..."
kill $BACKEND_PID 2>/dev/null