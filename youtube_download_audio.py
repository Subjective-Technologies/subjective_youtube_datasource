import sys
import os
import logging
from yt_dlp import YoutubeDL

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")

def download_audio(url: str, output_dir: str = ".") -> str | None:
    """
    Download the best audio stream from a YouTube URL and convert to MP3.
    Returns the path to the saved .mp3 file, or None on failure.
    """
    # ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    # template: use video id as filename
    outtmpl = os.path.join(output_dir, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get("id")
            mp3_path = os.path.join(output_dir, f"{video_id}.mp3")
            if os.path.isfile(mp3_path):
                logging.info(f"Downloaded audio to '{mp3_path}'")
                return mp3_path
            else:
                logging.error(f"Expected output file not found: '{mp3_path}'")
    except Exception as e:
        logging.error(f"Failed to download audio: {e}")
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python youtube_download_audio.py <YouTube_URL>")
        sys.exit(1)

    url = sys.argv[1]
    mp3_file = download_audio(url)
    if mp3_file is None:
        sys.exit(1)

if __name__ == "__main__":
    main()