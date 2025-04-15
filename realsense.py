import os
import time
from datetime import datetime
import numpy as np
import cv2
import pyrealsense2 as rs
from device_manager import DeviceManager

save_root = "data"

# Configuration settings
RECORD_VIDEO = True        # Set to True to record video
VIDEO_DURATION = 60        # Duration of each video in seconds (increased to 60 seconds)
SAVE_IMAGES = False        # Set to False to stop saving individual frames as images

# RealSense pipeline
c = rs.config()
c.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
c.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

device_manager = DeviceManager(rs.context(), c)
device_manager.enable_all_devices(enable_ir_emitter=True)

def create_video_writers(save_dir, serial, frame_width, frame_height, fps=30):
    """Create video writers for color and depth streams"""
    # Using H.264 codec for better compression and quality
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # You can also use 'mp4v' for MP4
    color_video_path = os.path.join(save_dir, f"{serial}_color.avi")
    depth_video_path = os.path.join(save_dir, f"{serial}_depth.avi")
    
    # Create writers with the specified parameters
    color_writer = cv2.VideoWriter(color_video_path, fourcc, fps, (frame_width, frame_height))
    depth_writer = cv2.VideoWriter(depth_video_path, fourcc, fps, (frame_width, frame_height))
    
    if not color_writer.isOpened() or not depth_writer.isOpened():
        print(f"[ERROR] Failed to open video writers for device {serial}")
    else:
        print(f"[INFO] Created video writers for device {serial} in {save_dir}")
    
    return color_writer, depth_writer

try:
    # Variables to calculate FPS
    frame_count = 0
    start_time = time.time()
    fps = 0
    display_interval = 1.0  # Update FPS display every second
    
    # Video recording variables
    video_writers = {}
    video_start_time = None
    current_video_dir = None
    recording_fps = 30  # Explicitly set the recording frame rate

    # Create a base directory with date to organize recordings better
    base_dir = os.path.join(save_root, datetime.now().strftime("%Y%m%d"))
    os.makedirs(base_dir, exist_ok=True)

    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Check if we need to start a new video
        if RECORD_VIDEO and (video_start_time is None or time.time() - video_start_time >= VIDEO_DURATION):
            # Close previous video writers if they exist
            for serial, (color_writer, depth_writer) in video_writers.items():
                color_writer.release()
                depth_writer.release()
            
            # Create new directory for this recording session
            current_video_dir = os.path.join(base_dir, timestamp)
            os.makedirs(current_video_dir, exist_ok=True)
            video_writers = {}
            video_start_time = time.time()
            print(f"[INFO] Started new video recording at {timestamp}")
            
            # Write a metadata file with recording information
            with open(os.path.join(current_video_dir, "metadata.txt"), "w") as f:
                f.write(f"Recording started: {timestamp}\n")
                f.write(f"Duration: {VIDEO_DURATION} seconds\n")
                f.write(f"FPS: {recording_fps}\n")
                f.write(f"Devices: Recording devices will be logged after first frame capture\n")

        # Remove the image saving code block since SAVE_IMAGES is now False
        # This entire block can be skipped if SAVE_IMAGES is False
        if SAVE_IMAGES:
            image_dir = os.path.join(save_root, timestamp)
            os.makedirs(image_dir, exist_ok=True)
        
        frames = device_manager.poll_frames()
        
        # On first frame capture, update the metadata with device information
        if RECORD_VIDEO and current_video_dir and frames and os.path.exists(os.path.join(current_video_dir, "metadata.txt")):
            device_serials = [serial for (serial, _) in frames.keys()]
            # Only append device information once
            metadata_path = os.path.join(current_video_dir, "metadata.txt")
            with open(metadata_path, "r") as f:
                content = f.read()
            if "Detected devices" not in content:
                with open(metadata_path, "a") as f:
                    f.write(f"Detected devices: {device_serials}\n")

        for (serial, product_line), stream_dict in frames.items():
            color_frame = stream_dict[rs.stream.color]
            depth_frame = stream_dict[rs.stream.depth]

            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())
            
            # Convert depth to 8-bit for visualization and video recording
            depth_8bit = cv2.convertScaleAbs(depth_image, alpha=0.03)
            
            # Save individual images if enabled (now disabled by default)
            if SAVE_IMAGES:
                cv2.imwrite(os.path.join(image_dir, f"{serial}_color.png"), color_image)
                cv2.imwrite(os.path.join(image_dir, f"{serial}_depth.png"), depth_8bit)
            
            # Record video if enabled
            if RECORD_VIDEO:
                # Create video writers for this device if they don't exist
                if serial not in video_writers:
                    height, width = color_image.shape[:2]
                    color_writer, depth_writer = create_video_writers(
                        current_video_dir, serial, width, height, fps=recording_fps)
                    video_writers[serial] = (color_writer, depth_writer)
                
                # Write frames to video
                color_writer, depth_writer = video_writers[serial]
                
                # Check if writers are valid before writing
                if color_writer.isOpened() and depth_writer.isOpened():
                    color_writer.write(color_image)
                    depth_writer.write(depth_8bit)
                else:
                    print(f"[WARNING] Video writer for device {serial} is not open")

        # Increment frame count
        frame_count += 1
        
        # Calculate and display FPS every display_interval seconds
        elapsed_time = time.time() - start_time
        if elapsed_time >= display_interval:
            fps = frame_count / elapsed_time
            print(f"[INFO] Current FPS: {fps:.2f}")
            # Reset counters
            frame_count = 0
            start_time = time.time()
            
            # Display recording information if video is being recorded
            if RECORD_VIDEO and video_start_time is not None:
                video_elapsed = time.time() - video_start_time
                video_remaining = max(0, VIDEO_DURATION - video_elapsed)
                print(f"[INFO] Recording video: {video_elapsed:.1f}s elapsed, {video_remaining:.1f}s remaining")

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    # Close all video writers
    if RECORD_VIDEO:
        for serial, (color_writer, depth_writer) in video_writers.items():
            color_writer.release()
            depth_writer.release()
        print("[INFO] Video files saved.")
    
    device_manager.disable_streams()
    print(f"[INFO] Final FPS: {fps:.2f}")
