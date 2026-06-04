# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

阴阳师（Onmyoji）手游自动挂机脚本。通过 uiautomator2 连接 Android 模拟器，结合 OpenCV 模板匹配实现自动战斗循环。

## Commands

```bash
# 安装依赖（使用 uv）
uv sync

# 运行脚本（需要模拟器已启动并连接 ADB）
uv run main.py              # 命令行版主挂机
uv run chapter28hard.py     # 困28副本专用
uv run gui.py               # GUI 版本

# 截取模拟器屏幕到 img/ 目录（用于准备模板图片）
uv run shot.py

# 打包为可执行文件（Nuitka + Python 3.12）
# 注意：必须使用 Python 3.12，Python 3.14 下 cv2.imread 会 segfault
D:\迅雷云盘\yys_script\.venv312\Scripts\python.exe build.py main       # 打包 main.py
D:\迅雷云盘\yys_script\.venv312\Scripts\python.exe build.py chapter    # 打包 chapter28hard.py
D:\迅雷云盘\yys_script\.venv312\Scripts\python.exe build.py gui        # 打包 gui.py
D:\迅雷云盘\yys_script\.venv312\Scripts\python.exe build.py all        # 打包全部
```

## Architecture

### 脚本文件

- **main.py** — 命令行版主挂机脚本。连接模拟器 → 加载模板图片 → 循环截屏+模板匹配+点击，包含反检测随机化和异常保护逻辑。
- **chapter28hard.py** — 困28副本专用挂机脚本。优先级驱动的状态机：胜利结算 > 进入副本 > 打首领 > 打经验怪 > 退出副本，支持自动跑图和宝箱跳过。
- **gui.py** — GUI 版本（CustomTkinter）。支持配置端口（多开）、匹配阈值、运行时长，实时日志显示。
- **shot.py** — 屏幕截图工具，用于截取模拟器画面制作模板图片。
- **path_helper.py** — 路径辅助模块，处理打包后 vs 开发模式的路径差异，自动设置 ADB 路径。
- **build.py** — Nuitka 打包脚本，自动复制资源文件（模板图片、adb.exe、u2.jar）到输出目录。

### 资源文件

- **start.png / win.png** — 模板图片（根目录），分别对应"开始战斗"按钮和"胜利"画面。支持多变体（如 `start_2.png`），脚本会随机选取以降低检测风险。
- **img/** — 存放通过 `shot.py` 截取的屏幕截图和关联模板（困28脚本使用）。

### 打包系统

使用 Nuitka standalone 模式打包，输出到 `dist/<script>.dist/` 目录。

**关键配置：**
- 必须使用 Python 3.12（`.venv312`），Python 3.14 下 cv2.imread 会 segfault
- GUI 版本需要 `--enable-plugin=tk-inter`
- 不要使用 `--include-module=cv2` 和 `--include-module=numpy`（会导致 segfault）
- `build.py` 会自动复制 `adbutils/binaries/` 和 `uiautomator2/assets/` 到输出目录

## Key Technical Details

- 模拟器连接地址默认 `127.0.0.1:16384`（雷电模拟器端口），GUI 版本支持修改端口实现多开。
- 图像匹配使用 `cv2.TM_CCOEFF_NORMED`，阈值默认 0.6（main.py）或 0.8（chapter28hard.py）。
- 模板图片支持多变体（如 `start.png`, `start_2.png`），脚本会随机选取以降低检测风险。
- 反检测机制：随机点击偏移、随机暂停、随机运行时长、随机休息间隔。
- `path_helper.py` 的 `setup_adb_path()` 必须在 `import uiautomator2` 之前调用，否则打包后找不到 adb.exe。

## 发送给其他人

只需发送 `dist/` 下对应的 `.dist` 文件夹，不需要 Python 环境。目标机器需要安装 Android 模拟器。
