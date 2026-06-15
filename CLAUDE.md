# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

阴阳师（Onmyoji）手游自动挂机脚本。通过 uiautomator2 连接 Android 模拟器，结合 OpenCV 模板匹配实现自动战斗循环。

## Commands

```bash
# 安装依赖（使用 uv）
uv sync                        # 仅运行依赖
uv sync --extra build          # 包含 Nuitka 打包依赖

# 运行脚本（需要模拟器已启动并连接 ADB）
uv run main.py              # 命令行版主挂机
uv run chapter28hard.py     # 困28副本专用
uv run gui.py               # GUI 版本

# 截取模拟器屏幕到 img/ 目录（用于准备模板图片）
uv run shot.py

# 打包为可执行文件（Nuitka standalone）
# Python 3.14 下 cv2.imread 会 segfault，需用 3.12
uv run build.py main       # 打包 main.py
uv run build.py chapter    # 打包 chapter28hard.py
uv run build.py gui        # 打包 gui.py
uv run build.py all        # 打包全部
```

## Architecture

### 脚本文件

- **main.py** — 命令行版主挂机脚本。连接模拟器 → 加载模板图片 → 循环截屏+模板匹配+点击，包含反检测随机化和异常保护逻辑。
- **chapter28hard.py** — 困28副本专用挂机脚本。优先级驱动的状态机：胜利结算 > 进入副本 > 打首领 > 打经验怪 > 退出副本，支持自动跑图和宝箱跳过。
- **gui.py** — GUI 版本（CustomTkinter）。支持配置端口（多开）、匹配阈值、运行时长、总次数上限、司机/打手定位，实时日志显示。特性：模板缓存（避免重复加载）、线程安全配置读取（`_config` 字典）、`cv2.setNumThreads(1)` 限制 CPU 占用。
- **shot.py** — 屏幕截图工具，文件名带时间戳（`shot_20260605_164416.png`），用于截取模拟器画面制作模板图片。
- **path_helper.py** — 路径辅助模块，处理打包后 vs 开发模式的路径差异，自动设置 ADB 路径。
- **build.py** — Nuitka 打包脚本，自动复制资源文件（模板图片、adb.exe、u2.jar）到输出目录。
- **label_tool.py** — OpenCV 实现的简易图片标注工具，用于标注 YOLO 训练数据。鼠标拖拽画框，按键分类（1=start, 2=win），自动缩放适配屏幕。
- **train.py** — YOLO 模型训练脚本。使用 ultralytics 训练目标检测模型，产出 `best.pt` 用于替代模板匹配。

### 资源文件

- **start.png / win.png** — 模板图片（根目录），`main.py` 使用。支持多变体（如 `start1.png`），脚本会随机选取以降低检测风险。
- **img/** — 困28副本和 GUI 版本使用的模板目录。命名规则：`<类型><编号>.png`（如 `boss1.png`, `boss2.png`）。通过 `load_templates("boss", "img")` 加载同名前缀的所有变体。
- **yolo/** — YOLO 训练数据目录。截图放根目录，标注文件在 `yolo/labels/`，格式为 YOLO 的 `.txt`（class_id x_center y_center width height，归一化坐标）。

### 打包系统

使用 Nuitka standalone 模式打包，输出到 `dist/<script>.dist/` 目录。

**关键配置：**
- Python 3.14 下 cv2.imread 会 segfault，需用 Python 3.12
- 不要使用 `--include-module=cv2` 和 `--include-module=numpy`（会导致 segfault）
- customtkinter 必须显式打包资源：`--include-package=customtkinter --include-package-data=customtkinter`，否则打包后运行会报 `Invalid src type: nuitka_resource_reader_files`
- `build.py` 会自动复制 `start.png`、`win.png`、`img/`、`adbutils/binaries/`、`uiautomator2/assets/` 到输出目录

## Key Technical Details

- 模拟器连接地址默认 `127.0.0.1:16384`（雷电模拟器端口），GUI 版本支持修改端口实现多开。
- 图像匹配使用 `cv2.TM_CCOEFF_NORMED`，阈值默认 0.6（main.py）或 0.8（chapter28hard.py / gui.py）。
- 模板图片支持多变体，脚本会随机选取以降低检测风险。
- 反检测机制：随机点击偏移（±5px）、随机暂停、随机运行时长（2-4h）、随机休息间隔。
- 所有脚本入口处的初始化顺序必须为：`get_base_dir()` → `os.chdir()` → `setup_adb_path()` → `import uiautomator2`。`setup_adb_path()` 必须在 `import uiautomator2` 之前调用，否则打包后找不到 adb.exe。
- `gui.py` 中的 `_run_loop_chapter28` 与 `chapter28hard.py` 逻辑基本一致，修改一处时需同步另一处。
- **司机/打手定位**：司机模式匹配 start/win 两个模板（负责开始战斗），打手模式只匹配 win 模板（只需等待战斗结束）。
- **CPU 优化**：`gui.py` 使用 `cv2.setNumThreads(1)` 限制 OpenCV 线程数，防止多线程环境下 CPU 占用过高。
- **线程安全**：`gui.py` 在启动时将 UI 配置读取到 `self._config` 字典，后台线程只读取缓存值，避免跨线程访问 Tkinter 控件导致闪退。
- **模板缓存**：`gui.py` 的 `load_templates()` 使用 `self._template_cache` 缓存已加载的模板，避免重复启动时重复加载。
- **延时配置**：普通挂机模式的检测延时受 UI 输入框控制（`random.uniform(0.5, delay)`），困28副本模式使用固定的、针对不同操作优化的延时（boss 10秒、exp 5秒、其他 1~2.5秒）。

## YOLO 训练

用于替代模板匹配，解决评分波动问题。依赖 `ultralytics`（已在 `pyproject.toml` 中声明）。

```bash
# 1. 截图（用 shot.py 或模拟器截图，保存到 yolo/）
uv run shot.py

# 2. 标注（OpenCV 标注工具，画框 → 按1/2分类 → 按s保存）
uv run label_tool.py

# 3. 训练（产出 best.pt 模型）
uv run train.py
```

## 发送给其他人

只需发送 `dist/` 下对应的 `.dist` 文件夹（如 `dist/gui.dist/`），不需要 Python 环境。目标机器需要安装 Android 模拟器。
