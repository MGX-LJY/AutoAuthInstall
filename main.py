#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS 修复助手 - 重构版
简洁的双功能修复工具：开启任何来源 + 修复损坏应用

架构特点：
- 解耦设计：GUI、业务逻辑、配置分离
- 现代化界面：卡片式布局，响应式设计
- 安全优化：密码安全传递，异步操作
- 功能专注：仅保留两个核心功能
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from gui.main_window import MainWindow


def main():
    """应用程序入口函数"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, False)
    
    # 设置应用程序信息
    app.setApplicationName("macOS修复助手")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("AutoAuthInstall")
    
    # 创建并显示主窗口
    try:
        window = MainWindow()
        window.show()
        
        # 启动事件循环
        return app.exec()
        
    except Exception as e:
        print(f"启动失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())