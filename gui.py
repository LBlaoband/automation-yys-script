"""
阴阳师自动挂机 - GUI 版本
支持两种模式：普通挂机（start/win）和 困28副本（状态机）
"""
import os
import sys
import time
import random
import threading
import customtkinter as ctk
import cv2
import glob

from path_helper import get_base_dir, setup_adb_path

# 初始化路径和 ADB
os.chdir(get_base_dir())
setup_adb_path()

import uiautomator2 as u2


class YysAutoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("来杯清补凉吧")
        self.geometry("700x620")
        self.minsize(700, 620)

        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 状态变量
        self.running = False
        self.device = None
        self.thread = None
        self.count = 0

        self._create_widgets()

    def _create_widgets(self):
        # ── 配置区域 ──
        config_frame = ctk.CTkFrame(self)
        config_frame.pack(padx=20, pady=(20, 10), fill="x")

        ctk.CTkLabel(config_frame, text="模拟器配置", font=("", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # 第一行：地址 + 端口
        row1 = ctk.CTkFrame(config_frame, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(row1, text="地址:").pack(side="left")
        self.addr_entry = ctk.CTkEntry(row1, width=160, placeholder_text="127.0.0.1")
        self.addr_entry.pack(side="left", padx=(5, 0))
        self.addr_entry.insert(0, "127.0.0.1")
        self.addr_entry.configure(state="disabled")

        ctk.CTkLabel(row1, text="端口:").pack(side="left", padx=(20, 0))
        self.port_entry = ctk.CTkEntry(row1, width=100, placeholder_text="16384")
        self.port_entry.pack(side="left", padx=(5, 0))
        self.port_entry.insert(0, "16384")

        # 第二行：模式 + 阈值
        row2 = ctk.CTkFrame(config_frame, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(row2, text="运行模式:").pack(side="left")
        self.mode_var = ctk.StringVar(value="困28副本")
        self.mode_menu = ctk.CTkOptionMenu(row2, values=["普通挂机", "困28副本"], variable=self.mode_var, width=120)
        self.mode_menu.pack(side="left", padx=(5, 0))

        ctk.CTkLabel(row2, text="匹配阈值:").pack(side="left", padx=(20, 0))
        self.threshold_entry = ctk.CTkEntry(row2, width=80)
        self.threshold_entry.pack(side="left", padx=(5, 0))
        self.threshold_entry.insert(0, "0.8")

        # 第三行：运行时长
        row3 = ctk.CTkFrame(config_frame, fg_color="transparent")
        row3.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(row3, text="运行时长:").pack(side="left")
        self.runtime_var = ctk.StringVar(value="2-4 小时")
        self.runtime_menu = ctk.CTkOptionMenu(row3, values=["1-2 小时", "2-4 小时", "4-6 小时"], variable=self.runtime_var, width=120)
        self.runtime_menu.pack(side="left", padx=(5, 0))

        # ── 按钮区域 ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=10, fill="x")

        self.start_btn = ctk.CTkButton(btn_frame, text="启动挂机", command=self.start, width=120, height=36)
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ctk.CTkButton(btn_frame, text="停止", command=self.stop, width=80, height=36, state="disabled")
        self.stop_btn.pack(side="left")

        self.screenshot_btn = ctk.CTkButton(btn_frame, text="截图", command=self.screenshot, width=80, height=36, state="disabled")
        self.screenshot_btn.pack(side="left", padx=(10, 0))

        # ── 日志区域 ──
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(padx=20, pady=10, fill="both", expand=True)

        ctk.CTkLabel(log_frame, text="运行日志", font=("", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(log_frame, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # ── 状态栏 ──
        status_frame = ctk.CTkFrame(self, height=36)
        status_frame.pack(padx=20, pady=(0, 20), fill="x")
        status_frame.pack_propagate(False)  # 固定高度

        self.status_label = ctk.CTkLabel(status_frame, text="状态: 未连接")
        self.status_label.pack(side="left", padx=10, pady=5)

        self.count_label = ctk.CTkLabel(status_frame, text="已完成: 0 次")
        self.count_label.pack(side="right", padx=10, pady=5)

    # ── 线程安全的 GUI 更新 ──

    def log(self, msg):
        """输出日志到界面（线程安全）"""
        self.after(0, self._log_impl, msg)

    def _log_impl(self, msg):
        self.log_text.configure(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_status(self, status):
        self.after(0, self._update_status_impl, status)

    def _update_status_impl(self, status):
        self.status_label.configure(text=f"状态: {status}")

    def update_count(self):
        self.after(0, self._update_count_impl)

    def _update_count_impl(self):
        self.count_label.configure(text=f"已完成: {self.count} 次")

    # ── 控制逻辑 ──

    def start(self):
        """启动挂机"""
        port = self.port_entry.get().strip()
        if not port.isdigit():
            self.log("错误: 端口必须是数字")
            return

        self.running = True
        self.count = 0
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.screenshot_btn.configure(state="normal")
        self.port_entry.configure(state="disabled")
        self.mode_menu.configure(state="disabled")

        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """停止挂机（线程安全）"""
        self.running = False
        self.after(0, self._stop_gui)

    def _stop_gui(self):
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.screenshot_btn.configure(state="disabled")
        self.port_entry.configure(state="normal")
        self.mode_menu.configure(state="normal")
        self.status_label.configure(text="状态: 已停止")

    def screenshot(self):
        """截取模拟器屏幕"""
        if self.device:
            try:
                img = self.device.screenshot(format='opencv')
                path = os.path.join(get_base_dir(), "img", f"shot_{int(time.time())}.png")
                cv2.imwrite(path, img)
                self.log(f"截图已保存: {os.path.basename(path)}")
            except Exception as e:
                self.log(f"截图失败: {e}")

    # ── 模板匹配工具 ──

    def load_templates(self, base_name, img_dir=None):
        """加载模板图片（支持变体，如 boss*.png → boss1.png, boss2.png）"""
        templates = []
        pattern = os.path.splitext(base_name)[0]
        search_dir = img_dir or ""
        search_pattern = os.path.join(search_dir, f"{pattern}*.png") if search_dir else f"{pattern}*.png"
        for f in glob.glob(search_pattern):
            img = cv2.imread(f, cv2.IMREAD_COLOR)
            if img is not None:
                templates.append(img)
                self.log(f"  加载模板: {f}")
            else:
                self.log(f"  ⚠️ 无法读取: {f}")
        return templates

    def click_image(self, templates, threshold=0.8, name="", do_click=True, corner=None):
        """在屏幕中寻找图片并点击。templates 可以是单张图片或列表"""
        if templates is None:
            return False
        if isinstance(templates, list):
            if not templates:
                return False
            template = random.choice(templates)
        else:
            template = templates

        screen = self.device.screenshot(format='opencv')

        res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if max_val >= threshold:
            h, w = template.shape[:2]
            if do_click:
                if corner == "top_right":
                    target_x = max_loc[0] + w + random.randint(-5, 5)
                    target_y = max_loc[1] + random.randint(-5, 5)
                else:
                    target_x = max_loc[0] + w // 2 + random.randint(-5, 5)
                    target_y = max_loc[1] + h // 2 + random.randint(-5, 5)
                self.log(f"[{name}] 匹配成功 (置信度 {max_val:.2f}) -> 点击 ({target_x}, {target_y})")
                self.device.click(target_x, target_y)
            else:
                self.log(f"[{name}] 匹配成功 (置信度 {max_val:.2f}) -> 仅检测")
            return True
        return False

    def click_relative(self, x_ratio, y_ratio):
        """按屏幕比例点击"""
        width, height = self.device.window_size()
        x = int(width * x_ratio) + random.randint(-10, 10)
        y = int(height * y_ratio) + random.randint(-10, 10)
        self.device.click(x, y)

    # ── 主循环 ──

    def _run_loop(self):
        """挂机主循环 — 根据模式分派"""
        port = self.port_entry.get().strip()
        address = f"127.0.0.1:{port}"
        threshold = float(self.threshold_entry.get())
        mode = self.mode_var.get()

        # 解析运行时长
        runtime_map = {"1-2 小时": (1, 2), "2-4 小时": (2, 4), "4-6 小时": (4, 6)}
        min_h, max_h = runtime_map.get(self.runtime_var.get(), (2, 4))
        max_runtime = random.uniform(min_h * 3600, max_h * 3600)

        self.log(f"正在连接模拟器: {address}")
        self.update_status("连接中...")

        try:
            self.device = u2.connect(address)
            self.log(f"已连接到: {self.device.info['productName']}")
            self.update_status("运行中")
        except Exception as e:
            self.log(f"连接失败: {e}")
            self.update_status("连接失败")
            self.stop()
            return

        try:
            if mode == "困28副本":
                self._run_loop_chapter28(threshold, min_h, max_h, max_runtime)
            else:
                self._run_loop_basic(threshold, min_h, max_h, max_runtime)
        except Exception as e:
            self.log(f"运行出错: {e}")
        finally:
            self.log("挂机结束")
            self.stop()

    # ── 普通挂机模式（start/win）──

    def _run_loop_basic(self, threshold, min_h, max_h, max_runtime):
        """普通挂机：检测 start.png / win.png"""
        self.log("加载模板图片...")
        start_templates = self.load_templates("start.png")
        win_templates = self.load_templates("win.png")

        if not start_templates:
            self.log("错误: 找不到 start*.png 模板")
            return
        if not win_templates:
            self.log("错误: 找不到 win*.png 模板")
            return

        self.log(f"模板加载完成: start x{len(start_templates)}, win x{len(win_templates)}")
        self.log("开始普通挂机...")

        count = 0
        rest_threshold = random.randint(200, 250)
        next_pause_battle = random.randint(50, 100)
        last_clicked = None
        consecutive_count = 0
        start_time = time.time()

        while self.running:
            # 运行时间限制
            elapsed = time.time() - start_time
            if elapsed >= max_runtime:
                long_rest = random.uniform(600, 1200)
                self.log(f"已运行 {elapsed / 3600:.1f} 小时，休息 {long_rest / 60:.1f} 分钟")
                time.sleep(long_rest)
                start_time = time.time()
                max_runtime = random.uniform(min_h * 3600, max_h * 3600)

            # 随机打乱检测顺序
            if random.random() < 0.5:
                first, first_t = "start", start_templates
                second, second_t = "win", win_templates
            else:
                first, first_t = "win", win_templates
                second, second_t = "start", start_templates

            clicked = None
            if self.click_image(first_t, threshold, name=first):
                clicked = first
                time.sleep(random.uniform(1.5, 2.5))
                if first == "win":
                    count += 1
                    self.count = count
                    self.update_count()
                    self.log(f"战斗结束，已完成 {count} 次")
                    if count >= next_pause_battle:
                        pause = random.uniform(5, 15)
                        self.log(f"随机暂停 {pause:.1f} 秒")
                        time.sleep(pause)
                        next_pause_battle = count + random.randint(50, 100)

            elif self.click_image(second_t, threshold, name=second):
                clicked = second
                time.sleep(random.uniform(1.5, 2.5))
                if second == "win":
                    count += 1
                    self.count = count
                    self.update_count()
                    self.log(f"战斗结束，已完成 {count} 次")
                    if count >= next_pause_battle:
                        pause = random.uniform(5, 15)
                        self.log(f"随机暂停 {pause:.1f} 秒")
                        time.sleep(pause)
                        next_pause_battle = count + random.randint(50, 100)

            # 连续检测同一个按钮超过 5 次
            if clicked:
                if clicked == last_clicked:
                    consecutive_count += 1
                else:
                    consecutive_count = 1
                    last_clicked = clicked
                if consecutive_count > 5:
                    self.log(f"连续检测到 {clicked} 超过 5 次，可能卡住，自动停止")
                    break
            else:
                consecutive_count = 0

            # 长休息逻辑
            if count >= rest_threshold:
                rest_time = random.uniform(120, 180)
                self.log(f"已连续运行 {count} 次，休息 {rest_time / 60:.1f} 分钟")
                time.sleep(rest_time)
                count = 0
                rest_threshold = random.randint(200, 250)

            time.sleep(random.uniform(1.5, 2.0))

    # ── 困28副本模式（状态机）──

    def _run_loop_chapter28(self, threshold, min_h, max_h, max_runtime):
        """困28副本：优先级驱动的状态机"""
        self.log("加载困28模板图片...")
        IMG_DIR = "img"

        tpl_win = self.load_templates("cctc", IMG_DIR)
        tpl_association = self.load_templates("association", IMG_DIR)
        tpl_chapter = self.load_templates("chapter", IMG_DIR)
        tpl_explore = self.load_templates("explore", IMG_DIR)
        tpl_boss = self.load_templates("boss", IMG_DIR)
        tpl_exp = self.load_templates("exp", IMG_DIR)
        tpl_chest = self.load_templates("chest", IMG_DIR)
        tpl_confirm_exit = self.load_templates("confirm_exit", IMG_DIR)

        # 检查必须的模板
        required = {
            "win(cctc)": tpl_win, "chapter": tpl_chapter,
            "explore": tpl_explore, "boss": tpl_boss, "exp": tpl_exp,
        }
        missing = [name for name, tpls in required.items() if not tpls]
        if missing:
            self.log(f"错误: 缺少模板 {', '.join(missing)}")
            return

        self.log(f"模板加载完成，开始困28挂机（无视宝箱，打完秒退）...")
        self.log("确保游戏已开启：自动准备、自动换狗粮")

        count = 0
        idle_count = 0
        start_time = time.time()

        while self.running:
            # 运行时间限制
            elapsed = time.time() - start_time
            if elapsed >= max_runtime:
                rest = random.uniform(600, 1200)
                self.log(f"已运行 {elapsed / 3600:.1f} 小时，休息 {rest / 60:.0f} 分钟")
                time.sleep(rest)
                start_time = time.time()
                max_runtime = random.uniform(min_h * 3600, max_h * 3600)

            # 优先级驱动的状态机
            if tpl_association and self.click_image(tpl_association, threshold, name="association", corner="top_right"):
                self.log("  -> 关闭意外弹窗")
                idle_count = 0
                time.sleep(1.0)

            elif self.click_image(tpl_win, threshold, name="win"):
                time.sleep(random.uniform(1.5, 2.5))
                self.click_relative(0.86, 0.83)
                count += 1
                self.count = count
                self.update_count()
                self.log(f"------ 已击败 {count} 队怪物 ------")
                idle_count = 0
                time.sleep(1.5)

            elif self.click_image(tpl_chapter, threshold, name="chapter"):
                self.log("  -> 选择章节")
                idle_count = 0
                time.sleep(2.0)

            elif self.click_image(tpl_explore, threshold, name="explore"):
                self.log("  -> 进入副本")
                idle_count = 0
                time.sleep(2.5)

            elif self.click_image(tpl_boss, threshold, name="boss"):
                self.log("  -> 发现首领，出击！")
                idle_count = 0
                time.sleep(10.0)

            elif self.click_image(tpl_exp, threshold, name="exp"):
                self.log("  -> 发现经验怪，出击！")
                idle_count = 0
                time.sleep(5.0)

            elif tpl_chest and self.click_image(tpl_chest, threshold, name="chest", do_click=False):
                self.log("  -> 确认首领已击败，退出副本！")
                self.click_relative(0.05, 0.08)
                time.sleep(1.0)
                if tpl_confirm_exit:
                    self.click_image(tpl_confirm_exit, threshold, name="confirm_exit")
                idle_count = 0
                time.sleep(2.5)

            else:
                idle_count += 1
                if idle_count >= 3:
                    self.log(f"  [发呆 {idle_count} 次] 向右滑动跑图...")
                    width, height = self.device.window_size()
                    sx, sy = int(width * 0.8), int(height * 0.5)
                    ex, ey = int(width * 0.2), int(height * 0.5)
                    self.device.shell(f"input swipe {sx} {sy} {ex} {ey} 500")
                    idle_count = 0
                    time.sleep(1.5)
                else:
                    time.sleep(1.5)


if __name__ == "__main__":
    app = YysAutoApp()
    app.mainloop()
