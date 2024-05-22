import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QFileDialog, QInputDialog, QLineEdit

# 定义执行 shell 命令的函数
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return e.stdout.decode('utf-8'), e.stderr.decode('utf-8')

# 创建主窗口类
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("macOS 安装助手")
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 创建按钮并绑定功能
        self.any_source_button = QPushButton("开启“任何来源”")
        self.any_source_button.clicked.connect(self.prompt_password_for_any_source)
        layout.addWidget(self.any_source_button)
        
        self.fix_damaged_button = QPushButton("修复已损坏的应用")
        self.fix_damaged_button.clicked.connect(self.prompt_password_for_fix_damaged_app)
        layout.addWidget(self.fix_damaged_button)
        
        # 创建容器并设置布局
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
    def prompt_password_for_any_source(self):
        """提示输入密码以启用 '任何来源' 选项"""
        password, ok = QInputDialog.getText(self, "输入密码", "请输入您的系统密码:", QLineEdit.Password)
        if ok and password:
            self.enable_any_source(password)

    def prompt_password_for_fix_damaged_app(self):
        """提示输入密码以修复已损坏的应用"""
        app_path, _ = QFileDialog.getOpenFileName(self, "选择已损坏的应用", "/Applications", "应用程序 (*.app)")
        if app_path:
            password, ok = QInputDialog.getText(self, "输入密码", "请输入您的系统密码:", QLineEdit.Password)
            if ok and password:
                self.fix_damaged_app(app_path, password)

    def enable_any_source(self, password):
        """启用 '任何来源' 选项"""
        command = f"echo {password} | sudo -S spctl --master-disable"
        stdout, stderr = run_command(command)
        if stderr:
            self.show_message("错误", f"启用任何来源时出错:\n{stderr}")
        else:
            self.show_message("成功", "“任何来源”已启用，请前往系统偏好设置->安全性与隐私进行确认。")

    def fix_damaged_app(self, app_path, password):
        """修复已损坏的应用"""
        command = f"echo {password} | sudo -S xattr -r -d com.apple.quarantine {app_path}"
        stdout, stderr = run_command(command)
        if stderr:
            self.show_message("错误", f"修复应用时出错:\n{stderr}")
        else:
            self.show_message("成功", "应用已修复，可以正常打开。")

    def show_message(self, title, message):
        """显示信息对话框"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()

# 主函数
def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
