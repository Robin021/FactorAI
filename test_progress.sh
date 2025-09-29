#!/bin/bash

# 获取token
echo "🔐 正在登录..."
TOKEN=$(curl -s http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  grep -o '"access_token":"[^"]*"' | \
  cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ 登录失败"
  exit 1
fi

echo "✅ 登录成功"

# 启动分析
echo "🚀 启动分析..."
ANALYSIS_ID=$(curl -s http://localhost:8000/api/v1/analysis/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"symbol":"AAPL","market_type":"US","analysis_type":"comprehensive"}' | \
  grep -o '"analysis_id":"[^"]*"' | \
  cut -d'"' -f4)

if [ -z "$ANALYSIS_ID" ]; then
  echo "❌ 启动分析失败"
  exit 1
fi

echo "✅ 分析启动成功，ID: $ANALYSIS_ID"

# 监控进度
echo "📊 开始监控进度..."
LAST_PROGRESS=""
LAST_MESSAGE=""

for i in {1..60}; do
  RESPONSE=$(curl -s http://localhost:8000/api/v1/analysis/$ANALYSIS_ID/progress \
    -H "Authorization: Bearer $TOKEN")
  
  if [ $? -eq 0 ]; then
    PROGRESS=$(echo "$RESPONSE" | grep -o '"progress_percentage":[0-9.]*' | cut -d':' -f2)
    STATUS=$(echo "$RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    MESSAGE=$(echo "$RESPONSE" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$PROGRESS" ]; then
      PROGRESS_PERCENT=$(echo "$PROGRESS * 100" | bc -l | cut -d'.' -f1)
      
      # 只在进度或消息变化时显示
      if [ "$PROGRESS$MESSAGE" != "$LAST_PROGRESS$LAST_MESSAGE" ]; then
        printf "[%2d] %3d%% | %-10s | %s\n" $i $PROGRESS_PERCENT "$STATUS" "$MESSAGE"
        LAST_PROGRESS=$PROGRESS
        LAST_MESSAGE=$MESSAGE
      fi
      
      # 检查是否完成
      if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] || [ "$STATUS" = "cancelled" ]; then
        echo "🎯 分析$STATUS!"
        break
      fi
    else
      echo "[$i] ❌ 无法解析进度数据"
    fi
  else
    echo "[$i] ❌ 请求失败"
  fi
  
  sleep 10
done

echo "✅ 监控完成"