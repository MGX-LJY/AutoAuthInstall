from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("macOS 安装助手")

        # 创建布局
        layout = QVBoxLayout()

        # 创建标签并添加到布局
        label = QLabel("欢迎使用 macOS 安装助手")
        layout.addWidget(label)

        # 创建按钮并绑定功能
        self.any_source_button = QPushButton("开启“任何来源”")
        self.any_source_button.clicked.connect(self.enable_any_source)
        layout.addWidget(self.any_source_button)

        self.fix_damaged_button = QPushButton("修复已损坏的应用")
        self.fix_damaged_button.clicked.connect(self.fix_damaged_app)
        layout.addWidget(self.fix_damaged_button)

        # 创建容器并设置布局
        container = QWidget()
        container.setLayout(layout)

        # 设置中央小部件
        self.setCentralWidget(container)

    def enable_any_source(self):
        """启用 '任何来源' 选项"""
        command = "sudo spctl --master-disable"
        stdout, stderr = self.run_command(command)
        if stderr:
            self.show_message("错误", f"启用任何来源时出错:\n{stderr}")
        else:
            self.show_message("成功", "“任何来源”已启用，请前往系统偏好设置->安全性与隐私进行确认。")

    def fix_damaged_app(self):
        """修复已损坏的应用"""
        # 打开文件对话框让用户选择应用程序
        app_path, _ = QFileDialog.getOpenFileName(self, "选择已损坏的应用", "/Applications", "应用程序 (*.app)")
        if app_path:
            command = f"sudo xattr -r -d com.apple.quarantine {app_path}"
            stdout, stderr = self.run_command(command)
            if stderr:
                self.show_message("错误", f"修复应用时出错:\n{stderr}")
            else:
                self.show_message("成功", "应用已修复，可以正常打开。")

    def run_command(self, command):
        """执行 shell 命令并返回输出和错误信息"""
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
        except subprocess.CalledProcessError as e:
            return e.stdout.decode('utf-8'), e.stderr.decode('utf-8')

    def show_message(self, title, message):
        """显示信息对话框"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()
