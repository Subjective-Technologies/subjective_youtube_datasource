import os
import re
import sys
import glob
import tempfile
import time
from datetime import datetime
from yt_dlp import YoutubeDL
import whisper
from transformers import pipeline
import logging
from pydub import AudioSegment  # Used to convert audio format

# ---------------------------- Configuration ---------------------------- #

# Whisper model size: choose among 'tiny', 'base', 'small', 'medium', 'large'
WHISPER_MODEL_SIZE = 'base'  # Adjust based on your system's capabilities

# Summarization models
ENGLISH_SUMMARIZATION_MODEL = "facebook/bart-large-cnn"

# Logging configuration
logging.basicConfig(
    filename='single_video_summary_english.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ------------------------ Helper Functions ----------------------------- #

def sanitize_filename(name):
    """
    Sanitize the video title (or any string) to create a valid filename.
    Removes or replaces characters that are invalid in filenames.
    """
    name = name.replace(' ', '_')  # Replace spaces with underscores
    name = re.sub(r'[^\w\-]', '', name)  # Remove non-alphanumeric/underscore/hyphen
    return name

def download_audio(video_url, download_path, max_retries=3):
    """
    Download the audio stream of a YouTube video using yt-dlp and convert it to mp3.
    Implements a retry mechanism in case of network hiccups.
    After downloading, it searches the download directory for the mp3 file.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_path, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'retries': max_retries,
    }
    
    attempt = 0
    while attempt < max_retries:
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=True)
                logging.info(f"Downloaded video info for {video_url}: {info_dict.get('title', 'Unknown Title')}")
            # After download, find the mp3 file in the download folder
            mp3_files = glob.glob(os.path.join(download_path, "*.mp3"))
            if mp3_files:
                audio_file = mp3_files[0]
                logging.info(f"Found audio file: {audio_file}")
                return audio_file
            else:
                logging.error("No MP3 file was found after download.")
                return None
        except Exception as e:
            attempt += 1
            logging.error(f"Attempt {attempt} - Error downloading {video_url}: {e}")
            if attempt < max_retries:
                time.sleep(3)  # Wait a bit before retrying
            else:
                return None

def convert_to_mono_wav(mp3_path, output_path):
    """
    Convert an MP3 file to a mono WAV file.
    """
    try:
        audio = AudioSegment.from_mp3(mp3_path)
        audio = audio.set_channels(1)  # Convert to mono
        audio.export(output_path, format="wav")
        logging.info(f"Converted {mp3_path} to mono WAV at {output_path}.")
        return output_path
    except Exception as e:
        logging.error(f"Error converting {mp3_path} to WAV: {e}")
        return None

def transcribe_audio(audio_path, model):
    """
    Transcribe audio to text using Whisper.
    Returns both the transcript and the detected language code.
    """
    try:
        # Specify language to improve accuracy
        result = model.transcribe(audio_path, language="en")
        transcript = result.get('text', "")
        language = result.get('language', "en")
        logging.info(f"Transcribed audio file {audio_path} with detected language: {language}.")
        return transcript, language
    except Exception as e:
        logging.error(f"Error transcribing {audio_path}: {e}")
        return "", "en"

def summarize_text(text, summarizer):
    """
    Generate a summary of the provided text using a Hugging Face summarization pipeline.
    If the text is long, break it up into chunks to meet the model's maximum input size.
    """
    try:
        max_chunk = 1024  # Adjust based on the model's max token input size
        text_chunks = [text[i:i + max_chunk] for i in range(0, len(text), max_chunk)]
        summaries = []
        for chunk in text_chunks:
            summary = summarizer(chunk, max_length=150, min_length=40, do_sample=False)[0]['summary_text']
            summaries.append(summary)
        full_summary = ' '.join(summaries)
        logging.info("Generated summary for transcript.")
        return full_summary
    except Exception as e:
        logging.error(f"Error summarizing text: {e}")
        return ""

# --------------------------- Main Script ------------------------------- #

def main():
    if len(sys.argv) != 2:
        print("Usage: python youtube_extractor_english.py <YouTube_Video_URL>")
        print("Example: python youtube_extractor_english.py https://www.youtube.com/watch?v=1234567890A")
        sys.exit(1)
    
    video_url = sys.argv[1]
    logging.info(f"Started processing video URL: '{video_url}'.")
    
    # Fetch video information (e.g., title) using yt-dlp
    try:
        with YoutubeDL({'quiet': True, 'skip_download': True, 'forcejson': True}) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            video_title = info_dict.get('title', 'Unknown_Video')
    except Exception as e:
        print(f"Error fetching video info for {video_url}: {e}")
        logging.error(f"Error fetching video info for {video_url}: {e}")
        sys.exit(1)
    
    print(f"Processing Video: {video_title}")
    print(f"URL: {video_url}")

    # Create a sanitized title for use in filenames
    sanitized_title = sanitize_filename(video_title)
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    summary_filename = f"{sanitized_title}-{timestamp}.txt"
    summary_filepath = os.path.join(os.getcwd(), summary_filename)
    
    # Load the Whisper model for transcription
    print(f"Loading Whisper model ({WHISPER_MODEL_SIZE})...")
    logging.info(f"Loading Whisper model '{WHISPER_MODEL_SIZE}'.")
    whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
    
    # Create a temporary folder to store the downloaded audio
    with tempfile.TemporaryDirectory() as tmpdirname:
        print("Downloading audio...")
        audio_file = download_audio(video_url, tmpdirname)
        if audio_file:
            print(f"Downloaded audio to {audio_file}")
            logging.info(f"Successfully downloaded audio to {audio_file}.")

            # Convert MP3 to mono WAV for better transcription accuracy
            wav_path = os.path.join(tmpdirname, "audio_mono.wav")
            converted_audio = convert_to_mono_wav(audio_file, wav_path)
            if not converted_audio:
                print("Failed to convert audio to WAV. Exiting.")
                logging.error("Audio conversion failed.")
                sys.exit(1)
            
            # Check audio file duration
            try:
                audio = AudioSegment.from_wav(converted_audio)
                duration = audio.duration_seconds
                print(f"Audio duration (s): {duration:.1f}")
                logging.info(f"Audio duration: {duration:.1f} seconds")
            except Exception as e:
                logging.error(f"Could not determine audio duration: {e}")
            
            # Transcribe the downloaded audio using Whisper
            transcript, lang = transcribe_audio(converted_audio, whisper_model)
            if transcript.strip():
                print("Transcription completed.")
                logging.info("Transcription completed successfully.")
                
                # Load the appropriate summarization model based on detected language
                if lang == "es":
                    print("Detected Spanish audio; loading Spanish summarization model...")
                    logging.info("Detected language: Spanish. Using Spanish summarization model.")
                    summarizer = pipeline("summarization", model="mrm8488/bert2bert_shared-spanish-finetuned-summarization")
                else:
                    print("Using English summarization model...")
                    logging.info("Using English summarization model.")
                    summarizer = pipeline("summarization", model=ENGLISH_SUMMARIZATION_MODEL)
                
                # Summarize the transcript text
                print("Generating summary...")
                logging.info("Starting summarization of transcript.")
                summary = summarize_text(transcript, summarizer)
                
                if not summary.strip():
                    print("Summary generation failed or returned empty. Exiting.")
                    logging.warning("Summary was empty after summarization.")
                    summary = "No summary was generated."
                
                print("\n--- Summary ---\n")
                print(summary)
                
                # Prepare the full content to be saved (including transcript and summary)
                file_content = (
                    f"Video URL: {video_url}\n"
                    f"Video Title: {video_title}\n"
                    f"Detected Language: {lang}\n"
                    f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "=== Transcription ===\n\n"
                    f"{transcript}\n\n"
                    "=== Summary ===\n\n"
                    f"{summary}"
                )
                
                # Save the transcription and summary to a text file in the current directory
                try:
                    with open(summary_filepath, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                    print(f"\nSummary saved to '{summary_filename}'.")
                    logging.info(f"Summary saved to '{summary_filepath}'.")
                except Exception as e:
                    print(f"Error saving summary to file: {e}")
                    logging.error(f"Error saving file '{summary_filepath}': {e}")
            else:
                print("No transcript was generated. Exiting.")
                logging.warning("Transcript was empty after audio processing.")
        else:
            print("Failed to download audio. Exiting.")
            logging.error("Audio download failed for the provided video URL.")

if __name__ == "__main__":
    main()
