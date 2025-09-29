#!/usr/bin/env python3
"""
测试新的登录页面设计
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置页面配置
st.set_page_config(
    page_title="登录页面设计测试",
    page_icon="🎨",
    layout="centered"
)

# 导入登录组件
try:
    from web.components.unified_login import render_unified_login_form
    
    st.title("🎨 新登录页面设计预览")
    st.markdown("---")
    
    # 渲染登录表单
    render_unified_login_form()
    
except ImportError as e:
    st.error(f"导入失败: {e}")
    st.info("请确保在项目根目录运行此脚本")