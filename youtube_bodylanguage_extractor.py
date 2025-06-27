import os
import cv2
import numpy as np
import yt_dlp
import mediapipe as mp
from collections import defaultdict
import argparse
from tqdm import tqdm
import sys

# Initialize MediaPipe Pose with enhanced sensitivity
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(static_image_mode=False,
                    model_complexity=2,  # Increased model complexity
                    smooth_landmarks=True,
                    enable_segmentation=False,
                    min_detection_confidence=0.6,  # Adjusted detection confidence
                    min_tracking_confidence=0.6)    # Adjusted tracking confidence

def download_hook(d):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        if total_bytes is not None:
            if not hasattr(download_hook, 'bar'):
                download_hook.bar = tqdm(total=total_bytes, unit='B', unit_scale=True, desc='Downloading', ascii=True)
        if hasattr(download_hook, 'bar'):
            downloaded = d.get('downloaded_bytes', 0)
            download_hook.bar.update(downloaded - download_hook.bar.n)
    elif d['status'] == 'finished':
        if hasattr(download_hook, 'bar'):
            download_hook.bar.close()
            del download_hook.bar

def download_youtube_video(url, download_path='videos'):
    """
    Downloads a YouTube video using yt-dlp and returns the file path.
    Includes a progress bar to show download progress using tqdm.
    """
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'progress_hooks': [download_hook],
        'quiet': True,  # Suppress yt-dlp's own output
        'no_warnings': True,
    }

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        print(f"Error downloading video: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")
        sys.exit(1)

    # Retrieve video information to construct the filepath
    try:
        info_dict = ydl.extract_info(url, download=False)
        video_title = info_dict.get('title', None)
        video_ext = info_dict.get('ext', None)
        # Sanitize filename
        safe_title = "".join([c if c.isalnum() or c in " -_." else "_" for c in video_title])
        filepath = os.path.join(download_path, f"{safe_title}.{video_ext}")
        if not os.path.isfile(filepath):
            # Sometimes yt-dlp might save with a different extension or naming
            # Attempt to find the file
            for file in os.listdir(download_path):
                if file.startswith(safe_title) and file.endswith(video_ext):
                    filepath = os.path.join(download_path, file)
                    break
        print(f"\nVideo downloaded to {filepath}")
        return filepath
    except Exception as e:
        print(f"Error retrieving video information: {e}")
        sys.exit(1)

def extract_frames(video_path, max_frames=None, frame_interval=5):
    """
    Extract frames from the video with a progress bar, sampling every 'frame_interval' frames.
    Saves all extracted frames for manual inspection.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Unable to open video file {video_path}")
        sys.exit(1)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps
    
    print(f"Frame Rate (FPS): {fps}")
    print(f"Total Frames: {total_frames}")
    print(f"Duration (seconds): {duration_sec}")
    
    frames = []
    
    # Directory to save all extracted frames
    extracted_dir = 'extracted_frames'
    if not os.path.exists(extracted_dir):
        os.makedirs(extracted_dir)
    
    # Initialize the tqdm progress bar
    frames_to_extract = total_frames // frame_interval if not max_frames else min(max_frames, total_frames // frame_interval)
    with tqdm(total=frames_to_extract, desc='Extracting Frames', unit='frame', ascii=True) as bar:
        count = 0
        extracted = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if count % frame_interval == 0:
                frames.append(frame)
                # Save the frame for manual inspection
                frame_filename = f"frame_{count}.jpg"
                cv2.imwrite(os.path.join(extracted_dir, frame_filename), frame)
                extracted += 1
                bar.update(1)
                if max_frames and extracted >= max_frames:
                    break
            count += 1
    cap.release()
    print(f"Extracted and saved {len(frames)} frames to the '{extracted_dir}' directory.")
    return frames

def analyze_body_language(frames, save_annotated=True):
    """
    Analyze body language using pose landmarks with a progress bar.
    Returns a summary of detected gestures/postures.
    Saves annotated frames if 'save_annotated' is True.
    """
    analysis = defaultdict(int)
    total_frames = len(frames)
    
    # Directory to save all annotated frames
    annotated_dir = 'annotated_frames'
    if not os.path.exists(annotated_dir):
        os.makedirs(annotated_dir)
    
    with tqdm(total=total_frames, desc='Analyzing Frames', unit='frame', ascii=True) as bar:
        for idx, frame in enumerate(frames):
            # Convert the BGR image to RGB before processing.
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)

            annotated_frame = frame.copy()

            if results.pose_landmarks:
                print(f"Frame {idx}: Pose detected.")
                landmarks = results.pose_landmarks.landmark

                # Draw pose landmarks on the frame for visualization
                mp_drawing.draw_landmarks(
                    annotated_frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )

                # Example Analysis 1: Arms Crossed
                left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
                left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
                right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]

                # Simple heuristic: If left elbow is near right shoulder and vice versa
                distance_lr = np.sqrt((left_elbow.x - right_shoulder.x)**2 + (left_elbow.y - right_shoulder.y)**2)
                distance_rl = np.sqrt((right_elbow.x - left_shoulder.x)**2 + (right_elbow.y - left_shoulder.y)**2)
                if distance_lr < 0.25 and distance_rl < 0.25:  # Further increased threshold
                    analysis['Arms Crossed'] += 1
                    print(f"Frame {idx}: Arms Crossed detected.")

                # Example Analysis 2: Hands on Hips
                left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
                right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
                left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
                right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]

                distance_lw = np.sqrt((left_wrist.x - left_hip.x)**2 + (left_wrist.y - left_hip.y)**2)
                distance_rw = np.sqrt((right_wrist.x - right_hip.x)**2 + (right_wrist.y - right_hip.y)**2)
                if distance_lw < 0.3 and distance_rw < 0.3:  # Further increased threshold
                    analysis['Hands on Hips'] += 1
                    print(f"Frame {idx}: Hands on Hips detected.")

                # Example Analysis 3: Upright Posture
                nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
                left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
                right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]

                # Calculate the average y-coordinate of hips
                average_hip_y = (left_hip.y + right_hip.y) / 2
                if nose.y < average_hip_y - 0.1:  # Adjust threshold as needed
                    analysis['Upright Posture'] += 1
                    print(f"Frame {idx}: Upright Posture detected.")
            else:
                print(f"Frame {idx}: No pose detected.")

            # Save the annotated frame
            if save_annotated:
                annotated_frame_path = os.path.join(annotated_dir, f"frame_{idx}.jpg")
                cv2.imwrite(annotated_frame_path, annotated_frame)

            bar.update(1)

    # Convert counts to percentages
    summary = {k: f"{(v / total_frames) * 100:.2f}%" for k, v in analysis.items()}
    print(f"Analysis Summary: {summary}")
    return summary

def generate_report(analysis, report_path='body_language_report.txt'):
    """
    Generates a text report from the analysis.
    """
    try:
        with open(report_path, 'w') as f:
            f.write("Body Language Analysis Report\n")
            f.write("=============================\n\n")
            for k, v in analysis.items():
                f.write(f"{k}: {v}\n")
        print(f"Report generated at {report_path}")
    except Exception as e:
        print(f"Error writing report: {e}")
        sys.exit(1)

def main(youtube_url):
    video_path = download_youtube_video(youtube_url)
    frames = extract_frames(video_path, frame_interval=5)  # Adjust 'frame_interval' as needed
    if not frames:
        print("No frames were extracted. Exiting.")
        sys.exit(1)
    analysis = analyze_body_language(frames)
    generate_report(analysis)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='YouTube Body Language Analyzer')
    parser.add_argument('url', type=str, help='YouTube video URL to analyze')
    args = parser.parse_args()
    main(args.url)
