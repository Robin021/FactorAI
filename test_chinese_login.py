#!/usr/bin/env python3
"""
测试优化的中文登录界面
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入新的登录组件
try:
    from web.components.unified_login_new import render_unified_login_form
    
    # 设置页面配置
    st.set_page_config(
        page_title="智能交易平台 - 登录",
        page_icon="🚀",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # 渲染登录表单
    render_unified_login_form()
    
except ImportError as e:
    st.error(f"❌ 导入登录组件失败: {e}")
    st.info("请确保所有依赖项已正确安装")
except Exception as e:
    st.error(f"❌ 渲染登录界面时出错: {e}")
    st.info("请检查配置和依赖项")