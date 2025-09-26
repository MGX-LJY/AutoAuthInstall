#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义GUI组件模块
提供现代化的UI组件
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, 
    QFrame, QProgressDialog, QInputDialog, QLineEdit
)
from PyQt6.QtGui import QFont, QPalette

from config.constants import COLORS, BUTTON_HEIGHT, CARD_WIDTH, CARD_HEIGHT


class FeatureCard(QFrame):
    """
    功能卡片组件
    现代化的卡片式设计，包含图标、标题、描述和操作按钮
    """
    
    action_clicked = pyqtSignal()  # 操作按钮点击信号
    
    def __init__(self, icon: str, title: str, detail: str, button_text: str, parent=None):
        super().__init__(parent)
        self.setup_ui(icon, title, detail, button_text)
        self.setup_style()
    
    def setup_ui(self, icon: str, title: str, detail: str, button_text: str):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 头部：图标和标题
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)
        
        # 图标
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(44, 44)
        icon_font = QFont()
        icon_font.setPointSize(26)
        icon_label.setFont(icon_font)
        
        # 标题
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(17)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; line-height: 1.3;")
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # 详细说明区域
        detail_label = QLabel(detail)
        detail_label.setWordWrap(True)
        detail_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']}; 
            font-size: 11px; 
            line-height: 1.4;
            padding: 4px 0px 8px 0px;
        """)
        detail_label.setMinimumHeight(50)
        
        # 操作按钮
        self.action_button = ModernButton(button_text, primary=True)
        self.action_button.clicked.connect(self.action_clicked.emit)
        
        # 添加到主布局
        layout.addLayout(header_layout)
        layout.addWidget(detail_label)
        layout.addStretch()
        layout.addWidget(self.action_button)
    
    def setup_style(self):
        """设置卡片样式"""
        self.setStyleSheet(f"""
            FeatureCard {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
                margin: 2px;
            }}
            FeatureCard:hover {{
                border-color: {COLORS['primary']};
                background-color: #FAFAFA;
            }}
        """)
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)


class ModernButton(QPushButton):
    """
    现代化按钮组件
    支持主要和次要样式
    """
    
    def __init__(self, text: str, primary: bool = False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setup_style()
        self.setup_properties()
    
    def setup_properties(self):
        """设置按钮属性"""
        self.setFixedHeight(BUTTON_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置字体
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.setFont(font)
        
        # 设置最小宽度确保按钮不会太窄
        self.setMinimumWidth(120)
    
    def setup_style(self):
        """设置按钮样式"""
        if self.primary:
            style = f"""
                QPushButton {{
                    background-color: {COLORS['primary']};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 20px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: #0051D0;
                }}
                QPushButton:pressed {{
                    background-color: #003A9B;
                }}
                QPushButton:disabled {{
                    background-color: #E5E5EA;
                    color: #8E8E93;
                }}
            """
        else:
            style = f"""
                QPushButton {{
                    background-color: {COLORS['background']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 10px;
                    padding: 12px 20px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: #E8E8ED;
                    border-color: {COLORS['primary']};
                }}
                QPushButton:pressed {{
                    background-color: #D8D8DD;
                }}
                QPushButton:disabled {{
                    background-color: #F2F2F7;
                    color: #8E8E93;
                    border-color: #E5E5EA;
                }}
            """
        self.setStyleSheet(style)


class ModernProgressDialog(QProgressDialog):
    """
    现代化进度对话框
    """
    
    def __init__(self, title: str, parent=None):
        super().__init__(f"{title}，请稍候...", None, 0, 0, parent)
        self.setup_style()
        self.setup_properties()
    
    def setup_properties(self):
        """设置对话框属性"""
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setCancelButton(None)
        self.setAutoReset(False)
        self.setAutoClose(False)
        self.setMinimumWidth(300)
        
        # 设置字体
        font = QFont()
        font.setPointSize(12)
        self.setFont(font)
    
    def setup_style(self):
        """设置样式"""
        self.setStyleSheet(f"""
            QProgressDialog {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            QProgressBar {{
                border: none;
                border-radius: 8px;
                background-color: {COLORS['background']};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 8px;
            }}
        """)


class PasswordDialog:
    """
    密码输入对话框
    静态方法提供简洁的密码输入接口
    """
    
    @staticmethod
    def get_password(parent=None, title="输入密码", prompt="请输入系统密码："):
        """
        获取密码输入
        
        Args:
            parent: 父窗口
            title: 对话框标题
            prompt: 提示信息
            
        Returns:
            (password, ok) - 密码和确认状态的元组
        """
        dialog = QInputDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setLabelText(prompt)
        dialog.setTextEchoMode(QLineEdit.EchoMode.Password)
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.resize(350, 120)
        
        # 设置样式
        dialog.setStyleSheet(f"""
            QInputDialog {{
                background-color: {COLORS['card_bg']};
                color: {COLORS['text_primary']};
            }}
            QLineEdit {{
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                background-color: {COLORS['card_bg']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0051D0;
            }}
            QPushButton:pressed {{
                background-color: #003A9B;
            }}
        """)
        
        ok = dialog.exec() == QInputDialog.DialogCode.Accepted
        return dialog.textValue(), ok