#!/bin/bash
# Authing SSO 环境变量设置脚本

echo "🔧 设置 Authing SSO 环境变量..."

# 设置 Authing 配置
export AUTHING_APP_ID="68d3879e03d9b1907f220731"
export AUTHING_APP_SECRET="your_app_secret_here"  # 请替换为实际的密钥
export AUTHING_APP_HOST="https://sxkc6t59wbj9-demo.authing.cn"
export AUTHING_REDIRECT_URI="http://localhost:3000/api/v1/auth/authing/callback"

# 设置前端环境变量
export VITE_AUTHING_APP_ID="68d3879e03d9b1907f220731"
export VITE_AUTHING_APP_HOST="https://sxkc6t59wbj9-demo.authing.cn"
export VITE_AUTHING_REDIRECT_URI="http://localhost:3000/api/v1/auth/authing/callback"

echo "✅ 环境变量设置完成"
echo ""
echo "📋 当前配置："
echo "AUTHING_APP_ID: $AUTHING_APP_ID"
echo "AUTHING_APP_HOST: $AUTHING_APP_HOST"
echo "AUTHING_REDIRECT_URI: $AUTHING_REDIRECT_URI"
echo ""
echo "⚠️  注意：请确保 AUTHING_APP_SECRET 填写正确的应用密钥"
echo "⚠️  注意：回调地址必须与 Authing 控制台配置完全一致"
echo ""
echo "🚀 现在可以启动服务："
echo "python tradingagents_server.py"
