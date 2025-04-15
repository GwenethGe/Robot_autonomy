import pyrealsense2 as rs
import numpy as np
import cv2
import os
import time
from datetime import datetime

# =========================
# Configurable parameters
# =========================
sample_rate = 1.0  # in Hz
interval = 1.0 / sample_rate  # seconds

# Replace these with your actual device serial numbers
camera_serials = {
    "wrist1": "xxxxxxxxxxxx",
    "wrist2": "yyyyyyyyyyyy",
    "world":  "zzzzzzzzzzzz"
}

# =========================
# Initialize pipelines
# =========================
pipelines = {}
configs = {}

for name, serial in camera_serials.items():
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_device(serial)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    pipeline.start(config)

    pipelines[name] = pipeline
    configs[name] = config

print("All pipelines started. Sampling every", interval, "seconds.")

try:
    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        save_dir = os.path.join("data", timestamp)
        os.makedirs(save_dir, exist_ok=True)

        for name, pipeline in pipelines.items():
            # Wait for frames
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()

            if not depth_frame or not color_frame:
                print(f"[WARNING] {name}: Missing frames.")
                continue

            # Convert to numpy arrays
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            # Save images
            color_path = os.path.join(save_dir, f"{name}_color.png")
            depth_path = os.path.join(save_dir, f"{name}_depth.png")

            cv2.imwrite(color_path, color_image)
            # Normalize depth to 0-255 for saving as image
            depth_normalized = cv2.convertScaleAbs(depth_image, alpha=0.03)
            cv2.imwrite(depth_path, depth_normalized)

        print(f"[INFO] Saved sample at {timestamp}")
        time.sleep(interval)

except KeyboardInterrupt:
    print("Sampling stopped by user.")

finally:
    for name, pipeline in pipelines.items():
        pipeline.stop()
    print("All pipelines stopped.")
