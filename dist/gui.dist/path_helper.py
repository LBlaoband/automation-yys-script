"""打包路径辅助模块

在开发模式下返回脚本所在目录，
在 Nuitka/PyInstaller 打包后返回可执行文件所在目录。
"""
import sys
import os


def get_base_dir() -> str:
    """返回资源文件的基准目录。"""
    if getattr(sys, "frozen", False):
        # 打包后的可执行文件
        return os.path.dirname(sys.executable)
    # 开发模式
    return os.path.dirname(os.path.abspath(__file__))


def setup_adb_path():
    """打包后自动设置 ADBUTILS_ADB_PATH，让 adbutils 找到内置的 adb.exe。"""
    if getattr(sys, "frozen", False):
        base = get_base_dir()
        adb_exe = os.path.join(base, "adbutils", "binaries", "adb.exe")
        if os.path.isfile(adb_exe):
            os.environ["ADBUTILS_ADB_PATH"] = adb_exe
            print(f"  ADB 路径: {adb_exe}")
        else:
            print(f"⚠️ 找不到 adb.exe: {adb_exe}")
