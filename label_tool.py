"""
简易图片标注工具（OpenCV 实现）
用法：uv run label_tool.py

操作：
  - 鼠标拖拽画框
  - 按 1 标记为 start，按 2 标记为 win
  - 按 u 撤销上一个标注
  - 按 s 保存并进入下一张
  - 按 n 跳过当前图片
  - 按 q 退出

标注结果保存在 yolo/labels/ 目录，格式为 YOLO 的 .txt 文件。
"""
import os
import glob
import ctypes
import cv2

IMG_DIR = "yolo"
LABEL_DIR = os.path.join(IMG_DIR, "labels")
CLASSES = {ord("1"): "start", ord("2"): "win"}

os.makedirs(LABEL_DIR, exist_ok=True)

# 获取屏幕可用区域（排除任务栏）
user32 = ctypes.windll.user32
SCREEN_W = user32.GetSystemMetrics(0)
SCREEN_H = user32.GetSystemMetrics(1) - 60  # 减去任务栏高度


def fit_to_screen(img):
    """缩放图片以适应屏幕，返回缩放后的图片和缩放比例"""
    h, w = img.shape[:2]
    scale = min(SCREEN_W / w, SCREEN_H / h, 1.0)
    if scale < 1.0:
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA), scale
    return img.copy(), 1.0


# 收集未标注的图片（已有对应 .txt 的跳过）
all_imgs = sorted(glob.glob(os.path.join(IMG_DIR, "*.png")))
images = []
for img_path in all_imgs:
    stem = os.path.splitext(os.path.basename(img_path))[0]
    txt_path = os.path.join(LABEL_DIR, f"{stem}.txt")
    if not os.path.exists(txt_path):
        images.append(img_path)

if not images:
    print("没有需要标注的图片！")
    exit()

print(f"待标注图片: {len(images)} 张")
print("操作: 拖拽画框 → 按1(start)/按2(win) → 按s保存 → 按u撤销 → 按n跳过 → 按q退出")

drawing = False
ix, iy = -1, -1
boxes = []  # [(x1, y1, x2, y2, class_name), ...] 坐标为原图尺寸
current_img = None      # 原图
display_img = None      # 缩放后用于显示的图
scale = 1.0             # 缩放比例


def to_display(x, y):
    """原图坐标 → 显示坐标"""
    return int(x * scale), int(y * scale)


def to_original(x, y):
    """显示坐标 → 原图坐标"""
    return int(x / scale), int(y / scale)


def redraw():
    """重绘显示画面"""
    img_copy = display_img.copy()
    for b in boxes:
        dx1, dy1 = to_display(b[0], b[1])
        dx2, dy2 = to_display(b[2], b[3])
        color = (0, 255, 0) if b[4] != "?" else (0, 165, 255)
        cv2.rectangle(img_copy, (dx1, dy1), (dx2, dy2), color, 2)
        cv2.putText(img_copy, b[4], (dx1, dy1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.imshow("label", img_copy)


def mouse_callback(event, x, y, flags, param):
    global drawing, ix, iy, boxes

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        img_copy = display_img.copy()
        for b in boxes:
            dx1, dy1 = to_display(b[0], b[1])
            dx2, dy2 = to_display(b[2], b[3])
            cv2.rectangle(img_copy, (dx1, dy1), (dx2, dy2), (0, 255, 0), 2)
            cv2.putText(img_copy, b[4], (dx1, dy1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.rectangle(img_copy, (ix, iy), (x, y), (0, 0, 255), 2)
        cv2.imshow("label", img_copy)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        # 转换为原图坐标存储
        ox1, oy1 = to_original(min(ix, x), min(iy, y))
        ox2, oy2 = to_original(max(ix, x), max(iy, y))
        if abs(ox2 - ox1) > 2 and abs(oy2 - oy1) > 2:
            boxes.append((ox1, oy1, ox2, oy2, "?"))
            print(f"  画框 #{len(boxes)} → 按 1(start) 或 2(win) 分类")


def save_yolo(img_path, box_list):
    """保存为 YOLO 格式"""
    h, w = current_img.shape[:2]
    stem = os.path.splitext(os.path.basename(img_path))[0]
    txt_path = os.path.join(LABEL_DIR, f"{stem}.txt")
    with open(txt_path, "w") as f:
        for b in box_list:
            cls_name = b[4]
            if cls_name == "?":
                continue
            cls_id = list(CLASSES.values()).index(cls_name)
            cx = ((b[0] + b[2]) / 2) / w
            cy = ((b[1] + b[3]) / 2) / h
            bw = (b[2] - b[0]) / w
            bh = (b[3] - b[1]) / h
            f.write(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
    print(f"  保存: {txt_path}")


cv2.namedWindow("label")
cv2.setMouseCallback("label", mouse_callback)

for idx, img_path in enumerate(images):
    current_img = cv2.imread(img_path)
    if current_img is None:
        print(f"  跳过无法读取: {img_path}")
        continue

    display_img, scale = fit_to_screen(current_img)
    boxes = []

    print(f"\n[{idx+1}/{len(images)}] {os.path.basename(img_path)} ({current_img.shape[1]}x{current_img.shape[0]} -> 显示 {display_img.shape[1]}x{display_img.shape[0]})")
    redraw()

    while True:
        key = cv2.waitKey(0) & 0xFF

        if key in CLASSES:
            for i in range(len(boxes) - 1, -1, -1):
                if boxes[i][4] == "?":
                    boxes[i] = (*boxes[i][:4], CLASSES[key])
                    print(f"  标记: {CLASSES[key]}")
                    break
            redraw()

        elif key == ord("u"):
            if boxes:
                removed = boxes.pop()
                print(f"  撤销: {removed[4]}")
            redraw()

        elif key == ord("s"):
            unclassified = [b for b in boxes if b[4] == "?"]
            valid = [b for b in boxes if b[4] != "?"]
            if unclassified:
                print(f"  ⚠️ 还有 {len(unclassified)} 个框未分类！先按 1(start) 或 2(win)")
            elif valid:
                save_yolo(img_path, valid)
                break
            else:
                print("  没有标注，跳过")
                break

        elif key == ord("n"):
            print("  跳过")
            break

        elif key == ord("q"):
            cv2.destroyAllWindows()
            print("\n退出标注工具")
            exit()

cv2.destroyAllWindows()
print(f"\n标注完成！标签文件在 {LABEL_DIR}/")
