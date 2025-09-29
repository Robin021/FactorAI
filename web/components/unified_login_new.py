"""
优化的中文统一登录组件
改善用户名密码输入框可见性，减少图标上方空间，表单居中显示
"""

import streamlit as st
import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入统一认证管理器
from web.utils.unified_auth_manager import unified_auth_manager

# 导入用户体验管理器
try:
    from web.utils.user_experience_manager import (
        get_error_manager, get_redirect_manager, get_feedback_manager,
        initialize_user_experience_manager
    )
    # 初始化用户体验管理器
    initialize_user_experience_manager(unified_auth_manager)
    UX_AVAILABLE = True
except ImportError:
    UX_AVAILABLE = False

# 导入Authing管理器（用于SSO）
try:
    from web.utils.authing_manager import authing_manager
except ImportError:
    authing_manager = None

def render_unified_login_form():
    """渲染优化的中文统一登录表单"""
    
    # 首先处理SSO回调 - 必须在页面渲染前处理
    if authing_manager and 'code' in st.query_params:
        code = st.query_params['code']
        with st.spinner("正在验证 SSO 登录..."):
            success, user_info = authing_manager.login_with_authing(code)
            if success and user_info:
                # 使用统一认证管理器处理SSO登录
                unified_auth_manager.login_sso(user_info)
                
                st.success(f"✅ SSO 登录成功！欢迎 {user_info.get('name', user_info.get('username', '用户'))}")
                time.sleep(1)
                # 使用重定向管理器处理登录后跳转
                if UX_AVAILABLE:
                    redirect_manager = get_redirect_manager()
                    redirect_manager.redirect_after_login('sso')
                else:
                    # 清除URL参数并添加默认分析参数
                    st.query_params.clear()
                    st.query_params['state'] = 'default_state'
                    st.query_params['provider'] = 'dashscope'
                    st.query_params['category'] = 'openai'
                    st.query_params['model'] = 'qwen-plus-latest'
                    st.rerun()
            else:
                st.error("❌ SSO 登录验证失败，请重试")
                # 清除URL参数
                if 'code' in st.query_params:
                    del st.query_params['code']
                st.rerun()
    
    # 优化的中文登录页面样式
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700;800;900&display=swap');
    
    /* 深色渐变背景 */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #1e293b 75%, #0f172a 100%);
        font-family: 'Noto Sans SC', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* 网格背景 */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            linear-gradient(rgba(59, 130, 246, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59, 130, 246, 0.1) 1px, transparent 1px);
        background-size: 40px 40px;
        opacity: 0.3;
        z-index: -1;
    }

    /* 去除默认边距和内边距 */
    section.main { 
        padding-top: 0 !important; 
        padding-bottom: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 100vh !important;
    }
    
    div[data-testid="stAppViewContainer"] { 
        padding-top: 0 !important; 
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 100vh !important;
    }
    
    /* 居中的登录卡片 */
    div[data-testid="stAppViewContainer"] .main .block-container {
        max-width: 420px;
        width: clamp(320px, 90vw, 420px);
        background: 
            linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%),
            rgba(15, 23, 42, 0.9);
        backdrop-filter: blur(20px) saturate(180%);
        border-radius: 24px;
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.4),
            0 0 0 1px rgba(255, 255, 255, 0.05) inset;
        padding: 32px 28px;
        margin: 0 auto;
        box-sizing: border-box;
        position: relative;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)    

    # 继续添加样式
    st.markdown("""
    /* 卡片顶部光效 */
    div[data-testid="stAppViewContainer"] .main .block-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(59, 130, 246, 0.8) 20%, 
            rgba(139, 92, 246, 0.8) 50%, 
            rgba(6, 182, 212, 0.8) 80%, 
            transparent 100%);
    }
    
    /* 登录容器 */
    .login-container {
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 20px;
        position: relative;
    }
    
    /* 紧凑的品牌标识区 - 减少上方空间 */
    .login-header {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
        margin-bottom: 24px;
        text-align: center;
    }
    
    /* 紧凑的品牌图标 */
    .brand-icon {
        width: 64px;
        height: 64px;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%);
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        color: white;
        box-shadow: 
            0 8px 24px rgba(59, 130, 246, 0.3),
            0 0 0 1px rgba(255, 255, 255, 0.1) inset;
        margin-bottom: 8px;
    }
    
    /* 中文标题 */
    .brand-title {
        font-family: 'Noto Sans SC', sans-serif;
        font-weight: 700;
        font-size: 24px;
        background: linear-gradient(135deg, #ffffff 0%, #3b82f6 50%, #8b5cf6 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin: 0;
        letter-spacing: 1px;
    }
    
    /* 中文副标题 */
    .brand-subtitle {
        font-family: 'Noto Sans SC', sans-serif;
        font-weight: 400;
        font-size: 13px;
        color: #94a3b8;
        margin: 0;
        opacity: 0.9;
    }
    
    /* 优化的输入框组 */
    .input-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
        width: 100%;
        margin-bottom: 16px;
    }
    
    /* 中文标签 */
    .input-label {
        font-family: 'Noto Sans SC', sans-serif;
        font-weight: 500;
        font-size: 14px;
        color: #e2e8f0;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* 高对比度输入框 - 提升可见性 */
    .stTextInput > div > div > input {
        width: 100% !important;
        height: 48px !important;
        background: rgba(255, 255, 255, 0.95) !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 0 16px !important;
        font-family: 'Noto Sans SC', sans-serif !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        color: #1e293b !important;
        box-sizing: border-box !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #64748b !important;
        font-family: 'Noto Sans SC', sans-serif !important;
        font-weight: 400 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 
            0 0 0 3px rgba(59, 130, 246, 0.2) !important,
            0 4px 12px rgba(0, 0, 0, 0.15) !important;
        outline: none !important;
        background: #ffffff !important;
        color: #0f172a !important;
    }
    
    .stTextInput > div > div > input:hover {
        border-color: #64748b !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* 密码输入框特殊样式 */
    .password-input .stTextInput > div > div > input {
        font-family: 'Courier New', monospace !important;
        letter-spacing: 2px !important;
    }
    
    /* 忘记密码链接 */
    .forgot-password {
        display: flex;
        justify-content: flex-end;
        margin-top: 4px;
        margin-bottom: 8px;
    }
    
    .forgot-password a {
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 13px;
        font-weight: 400;
        color: #3b82f6;
        text-decoration: none;
        transition: color 0.2s ease;
    }
    
    .forgot-password a:hover {
        color: #2563eb;
        text-decoration: underline;
    }
    
    /* 中文登录按钮 */
    .stButton > button {
        width: 100% !important;
        height: 48px !important;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-family: 'Noto Sans SC', sans-serif !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton > button:disabled {
        background: #94a3b8 !important;
        color: #64748b !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* 分隔符 */
    .divider {
        display: flex;
        align-items: center;
        margin: 20px 0;
        position: relative;
    }
    
    .divider::before,
    .divider::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(148, 163, 184, 0.3) 50%, 
            transparent 100%);
    }
    
    .divider span {
        padding: 0 16px;
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 12px;
        font-weight: 400;
        color: #94a3b8;
        background: rgba(15, 23, 42, 0.9);
    }
    
    /* SSO按钮 */
    .stLinkButton > a {
        width: 100% !important;
        height: 48px !important;
        background: rgba(255, 255, 255, 0.05) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(148, 163, 184, 0.3) !important;
        border-radius: 12px !important;
        font-family: 'Noto Sans SC', sans-serif !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        text-decoration: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.3s ease !important;
        box-sizing: border-box !important;
    }
    
    .stLinkButton > a:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    
    /* 用户信息卡片 */
    .user-info-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        border: 1px solid rgba(59, 130, 246, 0.2);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        position: relative;
    }
    
    .user-info-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        border-radius: 16px 16px 0 0;
    }
    
    .user-name {
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 12px;
        color: #1e293b;
    }
    
    .user-details {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 13px;
        color: #64748b;
        font-weight: 400;
        margin-bottom: 16px;
    }
    
    .user-role {
        display: inline-block;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        padding: 6px 12px;
        border-radius: 8px;
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 12px;
        font-weight: 500;
    }
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        div[data-testid="stAppViewContainer"] .main .block-container {
            width: clamp(280px, 95vw, 380px);
            padding: 24px 20px;
        }
        
        .brand-icon {
            width: 56px;
            height: 56px;
            font-size: 24px;
        }
        
        .brand-title {
            font-size: 20px;
        }
        
        .stTextInput > div > div > input,
        .stButton > button,
        .stLinkButton > a {
            height: 44px !important;
            font-size: 14px !important;
        }
    }
    
    /* 成功状态 */
    .success-glow {
        animation: successGlow 0.6s ease-out;
    }
    
    @keyframes successGlow {
        0% { 
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        }
        70% { 
            box-shadow: 0 8px 24px rgba(34, 197, 94, 0.3);
        }
        100% { 
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 登录容器
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # 紧凑的品牌标识区
        st.markdown("""
        <div class="login-header">
            <div class="brand-icon">🚀</div>
            <h1 class="brand-title">智能交易平台</h1>
            <p class="brand-subtitle">AI驱动的量化交易系统</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 检查是否已认证
        if unified_auth_manager.is_authenticated():
            user_info = unified_auth_manager.get_current_user()
            if user_info:
                auth_type = user_info.get('auth_type', 'unknown')
                auth_display = "单点登录" if auth_type == 'sso' else "本地登录"
                role_display = "管理员" if user_info.get('role') == 'admin' else "普通用户"
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    <div class="user-info-card">
                        <div>
                            <h3 class="user-name">👋 欢迎回来，{user_info.get('display_name', '用户')}</h3>
                            <div class="user-details">
                                <span>🎯 {role_display}</span>
                                <span>🌐 {auth_display}</span>
                                <span>🌟 在线中</span>
                            </div>
                        </div>
                        <div class="user-role">{role_display}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("🚪 退出登录", use_container_width=True, type="secondary"):
                        unified_auth_manager.logout()
                        # 使用重定向管理器处理登出
                        if UX_AVAILABLE:
                            redirect_manager = get_redirect_manager()
                            redirect_manager.redirect_after_logout()
                        else:
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
                return
        
        # 登录表单
        with st.form("login_form", clear_on_submit=False):
            # 用户名输入
            st.markdown("""
            <div class="input-group">
                <label class="input-label">👤 用户名</label>
            </div>
            """, unsafe_allow_html=True)
            username = st.text_input(
                "用户名",
                placeholder="请输入您的用户名",
                label_visibility="collapsed",
                key="username_input"
            )
            
            # 密码输入
            st.markdown("""
            <div class="input-group password-input">
                <label class="input-label">🔒 密码</label>
            </div>
            """, unsafe_allow_html=True)
            password = st.text_input(
                "密码",
                type="password",
                placeholder="请输入您的密码",
                label_visibility="collapsed",
                key="password_input"
            )
            
            # 忘记密码链接
            st.markdown("""
            <div class="forgot-password">
                <a href="#" onclick="alert('请联系管理员重置密码')">忘记密码？</a>
            </div>
            """, unsafe_allow_html=True)
            
            # 登录按钮
            login_submitted = st.form_submit_button("🔐 立即登录", use_container_width=True)
            
            if login_submitted:
                if not username or not password:
                    st.error("❌ 请输入用户名和密码")
                else:
                    with st.spinner("正在验证登录信息..."):
                        success, user_info = unified_auth_manager.login_local(username, password)
                        if success:
                            st.success(f"✅ 登录成功！欢迎 {user_info.get('display_name', username)}")
                            time.sleep(1)
                            # 使用重定向管理器处理登录后跳转
                            if UX_AVAILABLE:
                                redirect_manager = get_redirect_manager()
                                redirect_manager.redirect_after_login('local')
                            else:
                                st.rerun()
                        else:
                            st.error("❌ 用户名或密码错误，请重试")
        
        # SSO登录选项
        if authing_manager:
            st.markdown("""
            <div class="divider">
                <span>或者</span>
            </div>
            """, unsafe_allow_html=True)
            
            sso_url = authing_manager.get_sso_login_url()
            if sso_url:
                st.link_button(
                    "🌐 使用单点登录 (SSO)",
                    sso_url,
                    use_container_width=True
                )
        
        st.markdown('</div>', unsafe_allow_html=True)

def check_unified_authentication():
    """检查统一认证状态"""
    return unified_auth_manager.is_authenticated()

def require_unified_permission(required_permission, redirect_to_login=True):
    """要求特定权限"""
    if not unified_auth_manager.is_authenticated():
        if redirect_to_login:
            render_unified_login_form()
            return False
        return False
    
    return unified_auth_manager.check_permission(required_permission)

def render_unified_sidebar_user_info():
    """渲染侧边栏用户信息"""
    if unified_auth_manager.is_authenticated():
        user_info = unified_auth_manager.get_current_user()
        if user_info:
            with st.sidebar:
                st.markdown("---")
                st.markdown(f"**👤 {user_info.get('display_name', '用户')}**")
                st.markdown(f"🎯 {user_info.get('role', '用户')}")
                auth_type = user_info.get('auth_type', 'unknown')
                auth_display = "单点登录" if auth_type == 'sso' else "本地登录"
                st.markdown(f"🌐 {auth_display}")

def render_unified_sidebar_logout():
    """渲染侧边栏退出按钮"""
    if unified_auth_manager.is_authenticated():
        with st.sidebar:
            if st.button("🚪 退出登录", use_container_width=True):
                unified_auth_manager.logout()
                if UX_AVAILABLE:
                    redirect_manager = get_redirect_manager()
                    redirect_manager.redirect_after_logout()
                else:
                    st.rerun()