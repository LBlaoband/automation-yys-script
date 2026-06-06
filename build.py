"""
Nuitka 打包脚本

用法：
  uv run build.py                # 打包 main.py（默认）
  uv run build.py main           # 打包 main.py
  uv run build.py chapter        # 打包 chapter28hard.py
  uv run build.py all            # 打包两个脚本

打包前请先安装 Nuitka：
  uv pip install nuitka ordered-set
"""

import subprocess
import sys
import os
import shutil

# ── 配置 ──────────────────────────────────────────────
TARGETS = {
    "main": {
        "script": "main.py",
        "name": "yys-auto",
    },
    "chapter": {
        "script": "chapter28hard.py",
        "name": "yys-chapter28",
    },
    "gui": {
        "script": "gui.py",
        "name": "yys-gui",
        "icon": "icon.ico",
    },
}

COMMON_ARGS = [
    "--standalone",                      # 独立模式，不依赖本地 Python
    "--assume-yes-for-downloads",        # 自动下载 C 编译器等依赖
    "--output-dir=dist",                 # 输出到 dist/ 目录
    "--enable-plugin=tk-inter",          # tkinter 支持
    "--include-package=customtkinter",   # customtkinter 完整打包
    "--include-package-data=customtkinter",  # 包含主题/字体等资源文件
    "--include-package=uiautomator2",    # uiautomator2 完整打包
    "--include-package-data=uiautomator2",  # 包含 u2.jar 等资源文件
    "--include-package=adbutils",        # adbutils 完整打包
    "--include-module=adbutils._adb",
    "--include-module=adbutils._device",
    "--include-module=adbutils._device_base",
    "--include-module=decorator",
    "--include-module=retry",
    "--include-module=retry.api",
    "--include-module=lxml",
    "--include-module=lxml.etree",
    "--include-module=packaging",
]

# GUI 版本不弹黑窗口，命令行版本保留控制台
GUI_CONSOLE_MODE = "--windows-console-mode=disable"
CLI_CONSOLE_MODE = "--windows-console-mode=force"


def find_adbutils_binaries() -> str:
    """找到 adbutils 自带的 adb.exe 所在目录"""
    # 从 Python 3.12 venv 中查找
    base_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir = os.path.join(base_dir, ".venv312", "Lib", "site-packages", "adbutils", "binaries")
    if os.path.isdir(bin_dir):
        return bin_dir
    # 回退到当前环境
    import adbutils
    pkg_dir = os.path.dirname(adbutils.__file__)
    bin_dir = os.path.join(pkg_dir, "binaries")
    if os.path.isdir(bin_dir):
        return bin_dir
    raise FileNotFoundError(f"找不到 adbutils/binaries 目录")


def copy_resources(script_name: str):
    """打包完成后，手动复制资源文件到输出目录"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Nuitka 用脚本名（不含扩展名）做目录名
    stem = os.path.splitext(script_name)[0]
    dist_dir = os.path.join(base_dir, "dist", f"{stem}.dist")

    if not os.path.isdir(dist_dir):
        print(f"⚠️ 输出目录不存在: {dist_dir}")
        return

    # 复制模板图片
    resources = ["start.png", "win.png", "full_screen.png", "full_screen_over.png"]
    for f in resources:
        src = os.path.join(base_dir, f)
        dst = os.path.join(dist_dir, f)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"  复制: {f}")


    # 复制 img/ 目录
    img_src = os.path.join(base_dir, "img")
    img_dst = os.path.join(dist_dir, "img")
    if os.path.isdir(img_src):
        if os.path.exists(img_dst):
            shutil.rmtree(img_dst)
        shutil.copytree(img_src, img_dst)
        print(f"  复制: img/ ({len(os.listdir(img_dst))} 个文件)")

    # 复制 path_helper.py
    ph_src = os.path.join(base_dir, "path_helper.py")
    ph_dst = os.path.join(dist_dir, "path_helper.py")
    if os.path.isfile(ph_src):
        shutil.copy2(ph_src, ph_dst)
        print(f"  复制: path_helper.py")

    # 复制 adbutils/binaries/（含 adb.exe）
    adb_bin_dir = find_adbutils_binaries()
    adb_dst = os.path.join(dist_dir, "adbutils", "binaries")
    os.makedirs(adb_dst, exist_ok=True)
    copied = 0
    for f in os.listdir(adb_bin_dir):
        src = os.path.join(adb_bin_dir, f)
        dst = os.path.join(adb_dst, f)
        if os.path.isfile(src):
            try:
                shutil.copy2(src, dst)
                copied += 1
            except PermissionError:
                print(f"  ⚠️ 跳过（文件被占用）: {f}")
    print(f"  复制: adbutils/binaries/ ({copied} 个文件)")

    # 复制 uiautomator2/assets/（含 u2.jar）
    # 从 Python 3.12 venv 中查找
    base_dir = os.path.dirname(os.path.abspath(__file__))
    u2_assets = os.path.join(base_dir, ".venv312", "Lib", "site-packages", "uiautomator2", "assets")
    if not os.path.isdir(u2_assets):
        # 回退到当前环境
        import uiautomator2
        u2_assets = os.path.join(os.path.dirname(uiautomator2.__file__), "assets")
    if os.path.isdir(u2_assets):
        u2_dst = os.path.join(dist_dir, "uiautomator2", "assets")
        if os.path.exists(u2_dst):
            shutil.rmtree(u2_dst)
        try:
            shutil.copytree(u2_assets, u2_dst)
            print(f"  复制: uiautomator2/assets/ ({len(os.listdir(u2_dst))} 个文件)")
        except PermissionError:
            print(f"  ⚠️ uiautomator2/assets/ 部分文件被占用，已跳过")


def find_python():
    """查找用于打包的 Python 解释器（优先使用 Python 3.12）"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 优先使用 Python 3.12 venv
    py312 = os.path.join(base_dir, ".venv312", "Scripts", "python.exe")
    if os.path.isfile(py312):
        return py312
    # 回退到当前 Python
    return sys.executable


def build(target_name: str):
    if target_name not in TARGETS:
        print(f"未知目标: {target_name}")
        print(f"可选: {', '.join(TARGETS.keys())}")
        sys.exit(1)

    t = TARGETS[target_name]
    python_exe = find_python()
    # GUI 版本隐藏控制台窗口，命令行版本保留
    console_mode = GUI_CONSOLE_MODE if target_name == "gui" else CLI_CONSOLE_MODE
    print(f"  使用 Python: {python_exe}")
    cmd = [
        python_exe, "-m", "nuitka",
        f"--output-filename={t['name']}",
        console_mode,
        *COMMON_ARGS,
        t["script"],
    ]
    # 如果配置了图标，添加图标参数
    icon = t.get("icon")
    if icon and os.path.isfile(icon):
        cmd.insert(3, f"--windows-icon-from-ico={icon}")
        print(f"  图标: {icon}")
    print(f"\n{'='*60}")
    print(f"  打包 {t['script']} → dist/{t['name']}.exe")
    print(f"{'='*60}\n")
    print(" ".join(cmd))
    print()
    subprocess.run(cmd, check=True)

    # 打包完成后复制资源文件
    print("\n复制资源文件...")
    copy_resources(t["script"])

    print(f"\n[OK] 完成！输出: dist/{t['name']}.dist/")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    choice = sys.argv[1] if len(sys.argv) > 1 else "main"

    if choice == "all":
        for name in TARGETS:
            build(name)
    else:
        build(choice)
