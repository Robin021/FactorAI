# 升级和回滚指南

## 平滑升级路径

### 1. 升级前准备

#### 数据备份
```bash
# 备份用户数据
python backend/scripts/migration/run_migration.py --type check

# 创建数据备份
cp -r web/data web/data_backup_$(date +%Y%m%d)
cp -r data data_backup_$(date +%Y%m%d)
```

#### 配置备份
```bash
# 备份配置文件
cp tradingagents/default_config.py config_backup/
cp .env .env.backup
```

### 2. 升级步骤

#### 第一步：启动新系统
```bash
# 启动新的FastAPI后端
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 启动新的React前端
cd frontend
npm start
```

#### 第二步：数据迁移
```bash
# 执行完整数据迁移
python backend/scripts/migration/run_migration.py --type full

# 验证迁移结果
python backend/scripts/migration/validate_migration.py
```

#### 第三步：兼容性测试
```bash
# 测试旧版API兼容性
curl -X POST http://localhost:8000/api/legacy/analysis/start \
  -H "Content-Type: application/json" \
  -d '{"symbol": "000001", "analysts": ["technical"]}'
```

### 3. 回滚机制

#### 快速回滚
如果新系统出现问题，可以快速回滚到旧版本：

```bash
# 停止新系统
pkill -f "uvicorn main:app"
pkill -f "npm start"

# 恢复数据备份
rm -rf web/data
mv web/data_backup_$(date +%Y%m%d) web/data

# 启动旧版Streamlit应用
cd web
python run_web.py
```

#### 数据回滚
```bash
# 恢复配置文件
cp config_backup/default_config.py tradingagents/
cp .env.backup .env

# 恢复分析数据
rm -rf data
mv data_backup_$(date +%Y%m%d) data
```

### 4. 兼容性保证

#### API兼容性
- 旧版API端点通过 `/api/legacy/` 前缀访问
- 保持相同的请求/响应格式
- 自动转换数据格式

#### 配置兼容性
- 自动读取旧版配置文件
- 转换为新格式配置
- 保持配置项的向后兼容

#### 数据格式兼容性
- 自动检测和转换结果格式
- 保持分析结果的一致性
- 支持新旧格式并存

### 5. 渐进式升级

#### 阶段1：并行运行
- 新旧系统同时运行
- 用户可以选择使用哪个版本
- 数据同步保持一致

#### 阶段2：功能迁移
- 逐步迁移用户到新系统
- 保持旧版API的可用性
- 监控系统稳定性

#### 阶段3：完全切换
- 停用旧版Streamlit应用
- 保留兼容性API
- 完成升级过程

### 6. 故障排除

#### 常见问题

**数据迁移失败**
```bash
# 检查数据库连接
python -c "from backend.core.database import get_database; import asyncio; asyncio.run(get_database())"

# 重新运行迁移
python backend/scripts/migration/run_migration.py --type streamlit
```

**API兼容性问题**
```bash
# 检查兼容性API状态
curl http://localhost:8000/api/legacy/health

# 查看API文档
curl http://localhost:8000/api/legacy/version
```

**配置转换问题**
```bash
# 验证配置兼容性
python -c "from backend.core.compatibility.config_compatibility import load_and_convert_legacy_config; print(load_and_convert_legacy_config())"
```

### 7. 监控和验证

#### 升级后检查清单
- [ ] 数据库连接正常
- [ ] Redis缓存工作正常
- [ ] 用户数据完整迁移
- [ ] 分析功能正常工作
- [ ] 旧版API兼容性正常
- [ ] 配置正确转换
- [ ] 性能指标正常

#### 持续监控
- 监控API响应时间
- 检查错误日志
- 验证数据一致性
- 用户反馈收集

### 8. 支持和维护

#### 兼容性支持期限
- 旧版API支持：6个月
- 数据格式兼容：永久支持
- 配置格式兼容：永久支持

#### 维护计划
- 定期更新兼容性层
- 修复发现的兼容性问题
- 优化性能和稳定性