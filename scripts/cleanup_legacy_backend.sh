#!/bin/bash

# 清理旧版后端系统脚本
# 运行前请确保新系统运行正常

set -e

echo "🧹 开始清理旧版后端系统..."
echo ""

# 创建备份目录
BACKUP_DIR="backend/legacy_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 步骤 1: 备份旧系统文件到 $BACKUP_DIR"
echo ""

# 备份旧的main.py
if [ -f "backend/main.py" ]; then
    echo "  ✓ 备份 backend/main.py"
    cp backend/main.py "$BACKUP_DIR/"
else
    echo "  ⚠️  backend/main.py 不存在，跳过"
fi

# 备份旧的API目录
if [ -d "backend/app/api" ]; then
    echo "  ✓ 备份 backend/app/api/"
    cp -r backend/app/api "$BACKUP_DIR/"
else
    echo "  ⚠️  backend/app/api/ 不存在，跳过"
fi

echo ""
echo "📝 步骤 2: 创建说明文件"
cat > "$BACKUP_DIR/README.md" << 'EOF'
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
EOF

echo ""
echo "⚠️  步骤 3: 确认是否删除旧文件"
echo ""
echo "备份已完成，现在准备删除以下文件："
echo "  - backend/main.py"
echo "  - backend/app/api/"
echo ""
read -p "确认删除吗？(y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🗑️  正在删除旧文件..."
    
    # 删除旧的main.py
    if [ -f "backend/main.py" ]; then
        rm backend/main.py
        echo "  ✓ 删除 backend/main.py"
    fi
    
    # 删除旧的API目录
    if [ -d "backend/app/api" ]; then
        rm -rf backend/app/api
        echo "  ✓ 删除 backend/app/api/"
    fi
    
    echo ""
    echo "✅ 清理完成！"
    echo ""
    echo "📋 备份位置: $BACKUP_DIR"
    echo "💡 提示: 如果系统运行正常，1个月后可以删除备份"
    echo ""
    echo "🧪 建议测试："
    echo "  1. 重启后端服务"
    echo "  2. 访问 http://localhost:8000/api/v1/docs 查看API文档"
    echo "  3. 测试分析功能是否正常"
else
    echo ""
    echo "❌ 取消删除操作"
    echo "📋 备份位置: $BACKUP_DIR"
    echo ""
    echo "如果确认要删除，请手动运行："
    echo "  rm backend/main.py"
    echo "  rm -rf backend/app/api/"
fi

echo ""
echo "🎉 脚本执行完毕"
