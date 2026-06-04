import os
from path_helper import get_base_dir, setup_adb_path

# 切换工作目录 + 设置 adb 路径（必须在 import uiautomator2 之前）
os.chdir(get_base_dir())
setup_adb_path()

import uiautomator2 as u2
import time
import random
import cv2

# 1. 连接模拟器
device_address = "127.0.0.1:16384"
d = u2.connect(device_address)
print(f"已连接到设备: {d.info['productName']}")

# 模板图片目录
IMG_DIR = "img"


def load_template(name):
    path = os.path.join(IMG_DIR, name)
    if not os.path.exists(path):
        print(f"模板不存在: {path}")
        return None
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"无法读取: {path}")
    return img


def click_image(template, name="", threshold=0.8, do_click=True, corner=None):
    if template is None:
        return False

    screen = d.screenshot(format='opencv')
    res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    print(f"  [{name}] 相似度: {max_val:.2f} (阈值: {threshold})")

    if max_val >= threshold:
        if do_click:
            h, w = template.shape[:2]
            if corner == "top_right":
                target_x = max_loc[0] + w + random.randint(-5, 5)
                target_y = max_loc[1] + random.randint(-5, 5)
            else:
                target_x = max_loc[0] + w // 2 + random.randint(-5, 5)
                target_y = max_loc[1] + h // 2 + random.randint(-5, 5)
            print(f"匹配成功 (相似度: {max_val:.2f}) -> 点击 ({target_x}, {target_y})")
            d.click(target_x, target_y)
        else:
            print(f"匹配成功 (相似度: {max_val:.2f}) -> 仅检测，不点击")
        return True
    return False


def click_relative(x_ratio, y_ratio):
    width, height = d.window_size()
    x = int(width * x_ratio) + random.randint(-10, 10)
    y = int(height * y_ratio) + random.randint(-10, 10)
    d.click(x, y)


# 加载模板
print("加载模板图片...")
template_win = load_template("cctc1.png")
template_association = load_template("association1.png")
template_chapter = load_template("chapter1.png")
template_explore = load_template("explore1.png")
template_boss = load_template("boss1.png")
template_exp = load_template("exp1.png")
template_chest = load_template("chest2.png")
template_confirm_exit = load_template("confirm_exit1.png")

# 困28 挂机主循环
print("困 28 极速版挂机启动！（无视宝箱，打完秒退）")
print("确保游戏已开启：自动准备、自动换狗粮。按 Ctrl + C 随时停止。")

count = 0
idle_count = 0
start_time = time.time()
max_runtime = random.uniform(2 * 3600, 4 * 3600)

try:
    while True:
        elapsed = time.time() - start_time
        if elapsed >= max_runtime:
            rest = random.uniform(600, 1200)
            print(f"--- 已运行 {elapsed/3600:.1f}h，休息 {rest/60:.0f}min ---")
            time.sleep(rest)
            start_time = time.time()
            max_runtime = random.uniform(2 * 3600, 4 * 3600)

        if click_image(template_association, name="association", threshold=0.8, corner="top_right"):
            print("   -> 关闭意外弹窗")
            idle_count = 0
            time.sleep(1.0)

        elif click_image(template_win, name="win", threshold=0.8):
            time.sleep(random.uniform(1.5, 2.5))
            click_relative(0.86, 0.83)
            count += 1
            print(f"------ 已击败 {count} 队怪物 ------")
            idle_count = 0
            time.sleep(1.5)

        elif click_image(template_chapter, name="chapter", threshold=0.8):
            print("   -> 选择章节")
            idle_count = 0
            time.sleep(2.0)

        elif click_image(template_explore, name="explore", threshold=0.8):
            print("   -> 进入副本")
            idle_count = 0
            time.sleep(2.5)

        elif click_image(template_boss, name="boss", threshold=0.8):
            print("   -> 发现首领，出击！")
            idle_count = 0
            time.sleep(10.0)

        elif click_image(template_exp, name="exp", threshold=0.8):
            print("   -> 发现经验怪，出击！")
            idle_count = 0
            time.sleep(5.0)

        elif click_image(template_chest, name="chest", threshold=0.8, do_click=False):
            print("   -> 确认首领已被击败且掉落宝箱，退出副本！")
            click_relative(0.05, 0.08)
            time.sleep(1.0)
            click_image(template_confirm_exit, name="confirm_exit", threshold=0.8)
            idle_count = 0
            time.sleep(2.5)

        else:
            idle_count += 1
            if idle_count >= 3:
                print(f"   [发呆 {idle_count} 次] 向右滑动跑图...")
                width, height = d.window_size()
                sx, sy = int(width * 0.8), int(height * 0.5)
                ex, ey = int(width * 0.2), int(height * 0.5)
                d.shell(f"input swipe {sx} {sy} {ex} {ey} 500")
                idle_count = 0
                time.sleep(1.5)
            else:
                time.sleep(1.5)

except KeyboardInterrupt:
    print("\n困 28 极速版挂机结束，辛苦啦！")
except Exception as e:
    print(f"发生错误: {e}")
finally:
    input("按回车键退出...")
