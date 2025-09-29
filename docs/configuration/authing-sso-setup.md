# Authing SSO 配置说明

## 问题分析
当前 SSO 登录失败的原因是环境变量没有设置，导致 Authing 配置为空，出现 `redirect_uri_mismatch` 错误。

## 解决方案

### 1. 创建环境变量文件
在项目根目录创建 `.env` 文件，内容如下：

```bash
# Authing SSO 配置
AUTHING_APP_ID=68d3879e03d9b1907f220731
AUTHING_APP_SECRET=your_app_secret_here
AUTHING_APP_HOST=https://sxkc6t59wbj9-demo.authing.cn
AUTHING_REDIRECT_URI=http://localhost:3000/api/v1/auth/authing/callback

# 前端环境变量
VITE_AUTHING_APP_ID=68d3879e03d9b1907f220731
VITE_AUTHING_APP_HOST=https://sxkc6t59wbj9-demo.authing.cn
VITE_AUTHING_REDIRECT_URI=http://localhost:3000/api/v1/auth/authing/callback
```

### 2. 获取 Authing 应用密钥
1. 登录 Authing 控制台
2. 进入应用管理
3. 找到应用 ID `68d3879e03d9b1907f220731`
4. 获取应用密钥（App Secret）

### 3. 配置回调地址
在 Authing 控制台中确保回调地址配置为：
```
http://localhost:3000/api/v1/auth/authing/callback
```

### 4. 启动服务
设置环境变量后重新启动服务：

```bash
# 加载环境变量并启动后端
source .env && python tradingagents_server.py

# 或者使用 python-dotenv
pip install python-dotenv
python tradingagents_server.py
```

## 调试步骤

### 1. 检查环境变量
```bash
echo $AUTHING_APP_ID
echo $AUTHING_APP_HOST
echo $AUTHING_REDIRECT_URI
```

### 2. 检查 Authing 配置
访问 Authing 配置端点：
```
https://sxkc6t59wbj9-demo.authing.cn/.well-known/openid_configuration
```

### 3. 测试回调地址
确保回调地址可以正常访问：
```
http://localhost:3000/api/v1/auth/authing/callback
```

## 常见问题

### 1. redirect_uri_mismatch
- 检查 Authing 控制台中的回调地址配置
- 确保与代码中的 `AUTHING_REDIRECT_URI` 完全一致
- 注意协议（http/https）和端口号

### 2. 环境变量未加载
- 确保 `.env` 文件在项目根目录
- 检查文件权限
- 使用 `source .env` 或 `python-dotenv` 加载

### 3. 应用密钥错误
- 确保 `AUTHING_APP_SECRET` 正确
- 检查应用密钥是否过期

## 测试流程

1. 设置环境变量
2. 启动后端服务
3. 访问前端登录页面
4. 点击 SSO 登录按钮
5. 完成 Authing 登录
6. 检查回调是否成功

## 注意事项

- 回调地址必须与 Authing 应用配置完全一致
- 确保服务运行在正确的端口（3000）
- 检查防火墙和网络连接
- 查看服务器日志获取详细错误信息
