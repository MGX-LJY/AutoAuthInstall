#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常量配置模块
包含应用程序的所有常量定义
"""

# 应用程序基本信息
APP_TITLE = "macOS 修复助手"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "简洁高效的 macOS 应用修复工具"

# 系统设置相关常量
PRIVACY_SECURITY_URL = "x-apple.systempreferences:com.apple.settings.PrivacySecurity"
CONFIRM_STRINGS = (
    "Globally disabling the assessment system needs to be confirmed in System Settings.",
    "This operation is no longer supported",
)

# UI 相关常量
WINDOW_WIDTH = 580
WINDOW_HEIGHT = 450
CARD_SPACING = 25
BUTTON_HEIGHT = 44
CARD_WIDTH = 260
CARD_HEIGHT = 220

# 颜色主题
COLORS = {
    "primary": "#007AFF",       # 蓝色主色调
    "success": "#34C759",       # 成功绿色
    "warning": "#FF9500",       # 警告橙色
    "danger": "#FF3B30",        # 错误红色
    "background": "#F2F2F7",    # 背景色
    "card_bg": "#FFFFFF",       # 卡片背景
    "text_primary": "#000000",  # 主要文字
    "text_secondary": "#8E8E93", # 次要文字
    "border": "#E5E5EA",        # 边框色
}

# 功能描述文本
DESCRIPTIONS = {
    "enable_anywhere": {
        "title": "开启任何来源",
        "icon": "🔓",
        "detail": "此功能会关闭 Gatekeeper 安全检查，允许您安装未经 Apple 验证的应用程序。"
    },
    "fix_damaged_app": {
        "title": "修复损坏应用",
        "icon": "🔧",
        "detail": "某些从网络下载的应用可能被系统标记为已损坏，此功能通过移除隔离标记来解决无法打开的问题。"
    }
}

# 消息文本
MESSAGES = {
    "password_prompt": "请输入系统密码以继续操作",
    "select_app": "请选择需要修复的应用程序",
    "processing": "正在处理请求，请稍候...",
    "success_enable": "任何来源已成功开启！",
    "success_fix_app": "应用修复完成！",
    "error_not_macos": "此工具仅支持 macOS 系统",
    "error_no_password": "需要系统密码才能继续操作",
    "error_operation_failed": "操作失败，请检查系统权限",
    "sequoia_guide": (
        "macOS 15+ 系统检测：\n\n"
        "已请求关闭 Gatekeeper，但需要在系统设置中手动确认：\n\n"
        "1. 打开「系统设置 → 隐私与安全性」\n"
        "2. 滚动到页面底部\n"
        "3. 将允许从以下位置下载的 App改为「任何来源」\n\n"
        "系统设置页面将自动为您打开。"
    )
}