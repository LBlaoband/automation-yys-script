import os
from path_helper import get_base_dir, setup_adb_path

# 切换工作目录 + 设置 adb 路径（必须在 import uiautomator2 之前）
base_dir = get_base_dir()
os.chdir(base_dir)
print(f"工作目录: {base_dir}")
setup_adb_path()

import uiautomator2 as u2
import time
import random
import cv2
import glob

# 1. 连接模拟器 (请把 16384 换成你查到的端口号)
device_address = "127.0.0.1:16384"
d = u2.connect(device_address)
print(f"已连接到: {d.info['productName']}")

def load_templates(base_name):
    """
    加载所有模板变体图片，如 start.png, start_2.png, start_3.png ...
    """
    templates = []
    # 匹配 base_name.png, base_name_2.png, base_name_3.png 等
    pattern = os.path.splitext(base_name)[0]
    for f in glob.glob(f"{pattern}*.png"):
        img = cv2.imread(f, cv2.IMREAD_COLOR)
        if img is not None:
            templates.append(img)
            print(f"  加载模板: {f}")
    if not templates:
        print(f"❌ 找不到任何 {pattern}*.png 模板图片！")
    return templates

def click_image(templates, threshold=0.6):
    """
    在屏幕中寻找图片并点击，从模板列表中随机选一张
    """
    if not templates:
        return False
    screen = d.screenshot(format='opencv')
    template = random.choice(templates)

    res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val >= threshold:
        h, w = template.shape[:2]
        target_x = max_loc[0] + w // 2 + random.randint(-5, 5)
        target_y = max_loc[1] + h // 2 + random.randint(-5, 5)
        print(f"找到匹配，置信度 {max_val:.2f}，点击位置 ({target_x}, {target_y})")
        d.click(target_x, target_y)
        return True
    return False

# 预加载所有模板
print("加载模板图片...")
start_templates = load_templates("start.png")
win_templates = load_templates("win.png")

# 2. 挂机主循环
print("脚本开始运行，请切换到游戏界面...")
count = 0
rest_threshold = random.randint(200, 250)
next_pause_battle = random.randint(50, 100)  # 每 50-100 次战斗随机暂停一次
last_clicked = None
consecutive_count = 0
start_time = time.time()
max_runtime = random.uniform(2 * 3600, 4 * 3600)  # 2-4 小时后自动停止
print(f"本次最大运行时间: {max_runtime / 3600:.1f} 小时")

try:
    while True:
        # 运行时间限制
        elapsed = time.time() - start_time
        if elapsed >= max_runtime:
            long_rest = random.uniform(600, 1200)  # 休息 10-20 分钟
            print(f"--- 已运行 {elapsed / 3600:.1f} 小时，休息 {long_rest / 60:.1f} 分钟 ---")
            time.sleep(long_rest)
            start_time = time.time()
            max_runtime = random.uniform(2 * 3600, 4 * 3600)
            print(f"--- 休息结束，重新开始（下次运行上限: {max_runtime / 3600:.1f} 小时）---")

        # 随机打乱检测顺序
        if random.random() < 0.5:
            first, first_t = "start", start_templates
            second, second_t = "win", win_templates
        else:
            first, first_t = "win", win_templates
            second, second_t = "start", start_templates

        clicked = None
        if click_image(first_t):
            clicked = first
            time.sleep(random.uniform(1.5, 2.5))
            if first == "win":
                count += 1
                print(f"--- 战斗结束，已完成 {count} 次 ---")

                if count >= next_pause_battle:
                    pause = random.uniform(5, 15)
                    print(f"[随机暂停] 休息 {pause:.1f} 秒")
                    time.sleep(pause)
                    next_pause_battle = count + random.randint(50, 100)

        elif click_image(second_t):
            clicked = second
            time.sleep(random.uniform(1.5, 2.5))
            if second == "win":
                count += 1
                print(f"--- 战斗结束，已完成 {count} 次 ---")

                if count >= next_pause_battle:
                    pause = random.uniform(5, 15)
                    print(f"[随机暂停] 休息 {pause:.1f} 秒")
                    time.sleep(pause)
                    next_pause_battle = count + random.randint(50, 100)

        # 连续检测同一个按钮超过 5 次，可能卡住了
        if clicked:
            if clicked == last_clicked:
                consecutive_count += 1
            else:
                consecutive_count = 1
                last_clicked = clicked
            if consecutive_count > 5:
                print(f"--- 连续检测到 {clicked} 超过 5 次，可能卡住，自动停止 ---")
                break
        else:
            consecutive_count = 0

        # 长休息逻辑
        if count >= rest_threshold:
            rest_time = random.uniform(120, 180)
            print(f"--- 已连续运行 {count} 次，休息 {rest_time / 60:.1f} 分钟 ---")
            time.sleep(rest_time)
            count = 0
            rest_threshold = random.randint(200, 250)
            print(f"--- 休息结束，继续运行（下次休息阈值: {rest_threshold} 次）---")

        # 每次循环后短暂停顿
        time.sleep(random.uniform(1.5, 2.0))

except KeyboardInterrupt:
    print("脚本已手动停止")
except Exception as e:
    print(f"❌ 发生错误: {e}")
finally:
    input("按回车键退出...")
