# AutoAuthInstall

AutoAuthInstall是一个基于[知乎老哥的文章](https://zhuanlan.zhihu.com/p/135948430)的项目，旨在解决某些Mac应用无法直接安装的问题。这是一个使用Python和PyQt开发的可视化应用程序，你可以通过图形界面来解决这些安装问题。

## 下载

你可以在[这里](https://github.com/MGX-LJY/AutoAuthInstall/releases/tag/pak)直接下载并使用该程序。下载后，只需输入系统密码即可使用。

## 从源码安装

如果你想从源码安装，可以按照以下步骤操作：

1. 克隆仓库：
    ```bash
    git clone https://github.com/MGX-LJY/AutoAuthInstall.git
    cd AutoAuthInstall
    ```

2. 创建并激活虚拟环境：
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. 安装依赖：
    ```bash
    pip install -r requirements.txt
    ```

## 使用

以下是如何运行应用程序：

```bash
python main.py
```

在应用程序中，你可以通过图形界面来启用“任何来源”选项以及修复已损坏的应用。具体步骤如下：

- 启用“任何来源”选项：
    1. 点击“开启‘任何来源’”按钮。
    2. 在弹出的对话框中输入您的系统密码并确认。

- 修复已损坏的应用：
    1. 点击“修复已损坏的应用”按钮。
    2. 在文件选择对话框中选择需要修复的应用程序。
    3. 在弹出的对话框中输入您的系统密码并确认。

## 打包应用

如果你想将应用程序打包成macOS下的.dmg文件，可以按照以下步骤操作：

1. 安装pyinstaller和create-dmg：
    ```bash
    pip install pyinstaller
    brew install create-dmg
    ```

2. 使用PyInstaller打包应用：
    ```bash
    pyinstaller main.spec
    ```

3. 使用create-dmg创建DMG文件：
    ```bash
    create-dmg 'dist/macOSInstallerAssistant'
    ```

## 参考资料

- [知乎文章](https://zhuanlan.zhihu.com/p/135948430)：了解更多关于为什么某些mac应用无法直接安装的背景知识。
- [PyInstaller文档](http://www.pyinstaller.org/)：了解更多关于如何使用PyInstaller打包Python应用。
- [create-dmg文档](https://github.com/create-dmg/create-dmg)：了解更多关于如何使用create-dmg创建macOS安装包。