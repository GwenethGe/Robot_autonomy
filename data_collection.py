import os
import time
from datetime import datetime
import json
import numpy as np
import cv2
import pyrealsense2 as rs
from device_manager import DeviceManager
from pymycobot import MyArmM

myarmm = MyArmM("COM3") # TODO: Change to your COM port

sample_rate = 1.0  # TODO: Change to your desired sample rate in Hz
interval = 1.0 / sample_rate
save_root = "data"

c = rs.config()
c.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
c.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

device_manager = DeviceManager(rs.context(), c)
device_manager.enable_all_devices(enable_ir_emitter=True)


try:
    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        save_dir = os.path.join(save_root, timestamp)
        os.makedirs(save_dir, exist_ok=True)

        frames = device_manager.poll_frames()
        for (serial, product_line), stream_dict in frames.items():
            color_frame = stream_dict[rs.stream.color]
            depth_frame = stream_dict[rs.stream.depth]

            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())

            cv2.imwrite(os.path.join(save_dir, f"{serial}_color.png"), color_image)
            depth_8bit = cv2.convertScaleAbs(depth_image, alpha=0.03)
            cv2.imwrite(os.path.join(save_dir, f"{serial}_depth.png"), depth_8bit)

        angles = myarmm.get_joints_angle()
        json_path = os.path.join(save_dir, "joints.json")
        with open(json_path, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "joints": angles
            }, f, indent=2)

        print(f"[INFO] Sampled at {timestamp}")
        time.sleep(interval)

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    device_manager.disable_streams()
