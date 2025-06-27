import os
import sys
import yt_dlp
import cv2
import mediapipe as mp
import numpy as np
from rich.progress import Progress, BarColumn, TimeRemainingColumn

# Suppress logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose()

# YouTube Download Progress Hook
def progress_hook(d):
    """Display progress for YouTube video download using Rich."""
    if d["status"] == "downloading":
        downloaded = d["downloaded_bytes"]
        total = d.get("total_bytes", d.get("total_bytes_estimate", 1))
        percent = (downloaded / total) * 100
        progress.update(task, completed=percent)
    elif d["status"] == "finished":
        progress.stop()
        print("\nDownload completed!")

def download_video(url, save_path="video.mp4"):
    """Download YouTube video with a progress bar."""
    ydl_opts = {
        "format": "301+140/best",
        "outtmpl": save_path,
        "progress_hooks": [progress_hook],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        global progress, task
        with Progress("[cyan]Downloading...", BarColumn(), "[bold yellow]{task.percentage:>3.1f}%", TimeRemainingColumn()) as progress:
            task = progress.add_task("Downloading", total=100)
            ydl.download([url])

def analyze_video(video_path):
    """Process video and analyze body language."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    with Progress("[green]Processing Video...", BarColumn(), "[bold yellow]{task.percentage:>3.1f}%", TimeRemainingColumn()) as progress:
        task = progress.add_task("Processing", total=total_frames)

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("\nProcessing complete!")
                break

            progress.update(task, advance=1)

            if frame_count % 5 == 0:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb_frame)

                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            cv2.imshow("Body Language Analysis", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            frame_count += 1

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    youtube_url = input("Enter YouTube URL: ")
    video_file = "video.mp4"

    download_video(youtube_url, video_file)
    analyze_video(video_file)
