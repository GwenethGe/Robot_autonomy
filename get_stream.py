# ... existing code ...

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

# ... existing code ...

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
                f.write(f"Devices: {[serial for (serial, _) in frames.items()]}\n")

# ... existing code ...

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

# ... existing code ...