#!/bin/bash
# Authing SSO 修复验证脚本

echo "🔍 Authing SSO 修复验证脚本"
echo "================================"

# 检查环境变量
echo "📋 检查环境变量配置..."
if [ -z "$AUTHING_APP_ID" ]; then
    echo "❌ AUTHING_APP_ID 未设置"
    echo "请先运行: ./setup_authing_env_fixed.sh <your_app_secret>"
    exit 1
fi

if [ -z "$AUTHING_APP_SECRET" ]; then
    echo "❌ AUTHING_APP_SECRET 未设置"
    echo "请先运行: ./setup_authing_env_fixed.sh <your_app_secret>"
    exit 1
fi

if [ "$AUTHING_APP_SECRET" = "your_app_secret_here" ]; then
    echo "❌ AUTHING_APP_SECRET 还是占位符"
    echo "请先运行: ./setup_authing_env_fixed.sh <your_app_secret>"
    exit 1
fi

echo "✅ 环境变量配置正确"
echo "   AUTHING_APP_ID: $AUTHING_APP_ID"
echo "   AUTHING_APP_SECRET: ${AUTHING_APP_SECRET:0:8}..."
echo "   AUTHING_APP_HOST: $AUTHING_APP_HOST"

# 检查服务器是否运行
echo ""
echo "🌐 检查服务器状态..."
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ 服务器正在运行"
else
    echo "❌ 服务器未运行"
    echo "请先启动服务器: python tradingagents_server.py"
    exit 1
fi

# 检查 Authing 配置端点
echo ""
echo "🔧 检查 Authing 配置..."
CONFIG_URL="$AUTHING_APP_HOST/.well-known/openid_configuration"
if curl -s "$CONFIG_URL" > /dev/null 2>&1; then
    echo "✅ Authing 配置端点可访问"
else
    echo "❌ Authing 配置端点不可访问"
    echo "请检查 AUTHING_APP_HOST: $AUTHING_APP_HOST"
    exit 1
fi

# 生成测试 URL
echo ""
echo "🔗 生成测试 URL..."
SCOPE="openid profile email phone username roles unionid external_id extended_fields"
STATE=$(date +%s)_$(shuf -i 1000-9999 -n 1)
TEST_URL="$AUTHING_APP_HOST/oidc/auth?client_id=$AUTHING_APP_ID&response_type=code&scope=$SCOPE&redirect_uri=$AUTHING_REDIRECT_URI&state=$STATE"

echo "✅ 测试 URL 已生成"
echo ""
echo "🧪 测试步骤："
echo "1. 在浏览器中打开以下 URL："
echo "   $TEST_URL"
echo ""
echo "2. 使用 Authing 用户池中的用户登录"
echo "3. 检查是否跳转回回调地址"
echo "4. 验证获取到的用户信息是否为真实数据"
echo ""
echo "📝 注意事项："
echo "- 确保 Authing 用户池中有测试用户"
echo "- 确保用户信息完整（邮箱、手机号）"
echo "- 确保回调地址配置正确"
echo ""
echo "🔍 如果测试失败，请检查："
echo "- Authing 控制台中的应用配置"
echo "- 用户是否存在并已激活"
echo "- 网络连接是否正常"
echo "- 服务器日志中的错误信息"
