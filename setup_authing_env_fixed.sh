#!/bin/bash
# Authing SSO 环境变量设置脚本 - 修复版

echo "🔧 设置 Authing SSO 环境变量..."

# 检查是否提供了应用密钥
if [ "$1" = "" ]; then
    echo "❌ 错误：请提供 Authing 应用密钥"
    echo "用法: $0 <your_app_secret>"
    echo "示例: $0 abc123def456ghi789"
    exit 1
fi

AUTHING_APP_SECRET="$1"

# 设置 Authing 配置
export AUTHING_APP_ID="68d3879e03d9b1907f220731"
export AUTHING_APP_SECRET="$AUTHING_APP_SECRET"
export AUTHING_APP_HOST="https://sxkc6t59wbj9-demo.authing.cn"
export AUTHING_REDIRECT_URI="http://localhost:3000/api/v1/auth/authing/callback"

# 设置前端环境变量
export VITE_AUTHING_APP_ID="68d3879e03d9b1907f220731"
export VITE_AUTHING_APP_HOST="https://sxkc6t59wbj9-demo.authing.cn"
export VITE_AUTHING_REDIRECT_URI="http://localhost:3000/api/v1/auth/authing/callback"

# 设置 JWT 配置
export JWT_SECRET_KEY="your_jwt_secret_key_$(date +%s)"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"

echo "✅ 环境变量设置完成"
echo ""
echo "📋 当前配置："
echo "AUTHING_APP_ID: $AUTHING_APP_ID"
echo "AUTHING_APP_SECRET: ${AUTHING_APP_SECRET:0:8}..."
echo "AUTHING_APP_HOST: $AUTHING_APP_HOST"
echo "AUTHING_REDIRECT_URI: $AUTHING_REDIRECT_URI"
echo ""
echo "⚠️  重要提醒："
echo "1. 确保 Authing 控制台中的应用密钥与上面设置的一致"
echo "2. 确保回调地址与 Authing 控制台配置完全一致"
echo "3. 确保 Authing 用户池中有测试用户"
echo ""
echo "🚀 现在可以启动服务："
echo "python tradingagents_server.py"
echo ""
echo "🔍 测试 SSO 登录："
echo "1. 访问 http://localhost:3000/login"
echo "2. 点击 'Authing SSO 登录' 按钮"
echo "3. 使用 Authing 用户池中的用户登录"
