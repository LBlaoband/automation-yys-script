"""
YOLO 训练脚本
用法：uv run train.py

需要先安装 ultralytics：uv add ultralytics
"""
from ultralytics import YOLO

# 使用 yolov8n（nano 版本，体积小速度快）
model = YOLO("yolov8n.pt")

# 训练
model.train(
    data="yolo/data.yaml",
    epochs=100,
    imgsz=640,
    batch=8,
    name="yys_model",
)

print("训练完成！模型保存在 runs/detect/yys_model/weights/best.pt")
