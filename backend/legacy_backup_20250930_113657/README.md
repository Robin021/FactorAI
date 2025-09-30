# 旧版后端系统备份

## 备份时间
$(date +"%Y-%m-%d %H:%M:%S")

## 备份原因
这些文件是早期的"简单进度跟踪系统"，已被新的完整FastAPI后端系统替代。

## 文件说明
- `main.py`: 旧版主应用，使用 `/api` 作为路由前缀
- `api/`: 旧版API路由（analysis.py, auth.py, compatibility.py）

## 新系统位置
- 主应用: `backend/app/main.py`
- API路由: `backend/api/v1/`
- 路由前缀: `/api/v1`

## 恢复方法（如果需要）
```bash
# 恢复 main.py
cp main.py ../../main.py

# 恢复 api 目录
cp -r api ../../app/
```

## 可以永久删除的时间
如果系统运行正常超过1个月，可以安全删除此备份目录。
