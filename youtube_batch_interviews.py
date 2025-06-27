#!/usr/bin/env python3
import subprocess

def main():
    links = [
        "https://youtube.com/live/R8yzlsqFKvQ?feature=share",
        "https://youtube.com/live/X6R-1NfFcjI?feature=share",
        "https://youtube.com/live/lJpVXdmsZ6A?feature=share",
        "https://youtube.com/live/swk_Fo3HCy8?feature=share",
        "https://youtube.com/live/OR0Leg1D6o0?feature=share",
        "https://youtube.com/live/nmwkawyIgfw?feature=share",
        "https://youtube.com/live/3FVJX5v49lo?feature=share"
    ]

    for link in links:
        # Execute the Spanish extractor script
        print(f"Processing Spanish extraction for: {link}")
        subprocess.run(["python3", "youtube_extractor_spanish.py", link], check=True)
        
        # Execute the English extractor script
        print(f"Processing English extraction for: {link}")
        subprocess.run(["python3", "youtube_extractor_english.py", link], check=True)

if __name__ == "__main__":
    main()
