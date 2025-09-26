#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现代化主窗口模块
简洁美观的用户界面，专注于两个核心功能
"""

import sys
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QMessageBox, QFileDialog, QApplication
)
from PyQt6.QtGui import QFont, QIcon

from config.constants import (
    APP_TITLE, APP_DESCRIPTION, WINDOW_WIDTH, WINDOW_HEIGHT,
    CARD_SPACING, COLORS, DESCRIPTIONS, MESSAGES
)
from gui.widgets import FeatureCard, ModernButton, ModernProgressDialog, PasswordDialog
from core.executor import RepairExecutor
from utils.helpers import validate_app_path, get_app_name, is_password_valid


class MainWindow(QMainWindow):
    """
    现代化主窗口
    采用卡片式设计，专注于两个核心功能的简洁界面
    """
    
    # 异步任务完成信号
    task_finished = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        
        # 初始化核心组件
        try:
            self.executor = RepairExecutor()
        except RuntimeError as e:
            QMessageBox.critical(None, "系统错误", str(e))
            sys.exit(1)
        
        # 异步任务管理
        self.thread_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="repair")
        self.current_task: Optional[Future] = None
        self.progress_dialog: Optional[ModernProgressDialog] = None
        
        # 初始化界面
        self.setup_ui()
        self.setup_window()
        self.connect_signals()
    
    def setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle(APP_TITLE)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 设置窗口样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['background']};
            }}
        """)
        
        # 居中显示
        self.center_window()
    
    def center_window(self):
        """将窗口居中显示"""
        screen = QApplication.primaryScreen().geometry()
        window_rect = self.frameGeometry()
        center_point = screen.center()
        window_rect.moveCenter(center_point)
        self.move(window_rect.topLeft())
    
    def setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(CARD_SPACING)
        
        # 标题区域
        self.create_header(main_layout)
        
        # 添加一些垂直间距
        main_layout.addSpacing(10)
        
        # 功能卡片区域
        self.create_feature_cards(main_layout)
        
        # 底部区域
        self.create_footer(main_layout)
    
    def create_header(self, layout: QVBoxLayout):
        """创建标题区域"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # 主标题
        title_label = QLabel(APP_TITLE)
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            padding: 8px 0px;
            letter-spacing: -0.5px;
        """)
        
        # 副标题
        subtitle_label = QLabel(APP_DESCRIPTION)
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            padding: 4px 0px 12px 0px;
            line-height: 1.4;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
    
    def create_feature_cards(self, layout: QVBoxLayout):
        """创建功能卡片区域"""
        # 创建一个容器来居中卡片
        cards_container = QHBoxLayout()
        cards_container.setContentsMargins(0, 0, 0, 0)
        cards_container.setSpacing(CARD_SPACING)
        
        # 添加左侧弹性空间
        cards_container.addStretch()
        
        # 开启任何来源卡片
        enable_desc = DESCRIPTIONS["enable_anywhere"]
        self.enable_card = FeatureCard(
            icon=enable_desc["icon"],
            title=enable_desc["title"],
            detail=enable_desc["detail"],
            button_text="开启任何来源"
        )
        self.enable_card.action_clicked.connect(self.on_enable_anywhere)
        
        # 修复损坏应用卡片
        fix_desc = DESCRIPTIONS["fix_damaged_app"]
        self.fix_card = FeatureCard(
            icon=fix_desc["icon"],
            title=fix_desc["title"],
            detail=fix_desc["detail"],
            button_text="选择应用修复"
        )
        self.fix_card.action_clicked.connect(self.on_fix_damaged_app)
        
        cards_container.addWidget(self.enable_card)
        cards_container.addWidget(self.fix_card)
        
        # 添加右侧弹性空间
        cards_container.addStretch()
        
        layout.addLayout(cards_container)
    
    def create_footer(self, layout: QVBoxLayout):
        """创建底部区域"""
        # 添加适当的垂直间距
        layout.addSpacing(20)
        
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        
        # 退出按钮
        self.quit_button = ModernButton("退出应用")
        self.quit_button.clicked.connect(self.close)
        self.quit_button.setFixedWidth(110)
        
        footer_layout.addStretch()
        footer_layout.addWidget(self.quit_button)
        
        layout.addLayout(footer_layout)
    
    def connect_signals(self):
        """连接信号槽"""
        self.task_finished.connect(self.on_task_finished)
    
    def on_enable_anywhere(self):
        """处理开启任何来源功能"""
        password, ok = PasswordDialog.get_password(self, "系统授权", MESSAGES["password_prompt"])
        
        if not ok or not is_password_valid(password):
            return
        
        self.run_async_task("开启任何来源", self.executor.enable_anywhere_source, password)
    
    def on_fix_damaged_app(self):
        """处理修复损坏应用功能"""
        # 选择应用文件
        app_path, _ = QFileDialog.getOpenFileName(
            self,
            MESSAGES["select_app"],
            "/Applications",
            "应用程序 (*.app);;所有文件 (*)"
        )
        
        if not app_path:
            return
        
        # 验证应用路径
        if not validate_app_path(app_path):
            QMessageBox.warning(
                self, 
                "路径错误", 
                "请选择有效的 .app 应用程序文件"
            )
            return
        
        # 获取密码
        app_name = get_app_name(app_path)
        password, ok = PasswordDialog.get_password(
            self, 
            "系统授权", 
            f"即将修复应用 {app_name}\n\n{MESSAGES['password_prompt']}"
        )
        
        if not ok or not is_password_valid(password):
            return
        
        self.run_async_task("修复损坏应用", self.executor.fix_damaged_app, app_path, password)
    
    def run_async_task(self, task_name: str, func, *args):
        """
        在后台线程中运行任务
        
        Args:
            task_name: 任务名称
            func: 要执行的函数
            *args: 函数参数
        """
        # 显示进度对话框
        self.progress_dialog = ModernProgressDialog(task_name, self)
        self.progress_dialog.show()
        
        # 禁用卡片按钮
        self.set_cards_enabled(False)
        
        # 提交任务到线程池
        def task_done_callback(future: Future):
            try:
                result = future.result()
            except Exception as e:
                result = {
                    "success": False,
                    "message": f"执行异常: {str(e)}",
                    "returncode": -1,
                    "stdout": "",
                    "stderr": str(e)
                }
            
            # 发送完成信号
            self.task_finished.emit(task_name, result)
        
        self.current_task = self.thread_pool.submit(func, *args)
        self.current_task.add_done_callback(task_done_callback)
    
    def on_task_finished(self, task_name: str, result: Dict[str, Any]):
        """
        处理异步任务完成
        
        Args:
            task_name: 任务名称
            result: 执行结果
        """
        # 隐藏进度对话框
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # 启用卡片按钮
        self.set_cards_enabled(True)
        
        # 处理执行结果
        if result.get("success", False):
            self.show_success_message(task_name, result)
        elif result.get("needs_manual_confirmation", False):
            self.show_manual_confirmation_message()
        else:
            self.show_error_message(task_name, result)
    
    def show_success_message(self, task_name: str, result: Dict[str, Any]):
        """显示成功消息"""
        message = result.get("message", f"{task_name}执行成功")
        QMessageBox.information(self, "操作成功", message)
    
    def show_manual_confirmation_message(self):
        """显示需要手动确认的消息（用于macOS 15+）"""
        QMessageBox.information(
            self, 
            "需要手动确认", 
            MESSAGES["sequoia_guide"]
        )
    
    def show_error_message(self, task_name: str, result: Dict[str, Any]):
        """显示错误消息"""
        message = result.get("message", f"{task_name}执行失败")
        
        # 如果有详细错误信息，添加到消息中
        stderr = result.get("stderr", "").strip()
        if stderr:
            message += f"\n\n错误详情：{stderr}"
        
        QMessageBox.critical(self, "操作失败", message)
    
    def set_cards_enabled(self, enabled: bool):
        """设置功能卡片的启用状态"""
        self.enable_card.action_button.setEnabled(enabled)
        self.fix_card.action_button.setEnabled(enabled)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 关闭线程池
        try:
            self.thread_pool.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        
        # 关闭进度对话框
        if self.progress_dialog:
            self.progress_dialog.close()
        
        super().closeEvent(event)