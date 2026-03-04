import os
import re
import sys
import shutil
import tempfile
import time
import random
from datetime import datetime
from yt_dlp import YoutubeDL
import whisper
from transformers import pipeline
import logging

# ---------------------------- Configuration ---------------------------- #

# Whisper model size: 'tiny', 'base', 'small', 'medium', 'large'
WHISPER_MODEL_SIZE = 'base'  # Adjust based on your system's capabilities

# Summarization model
SUMMARIZATION_MODEL = "facebook/bart-large-cnn"  # You can choose other models if desired

# Maximum number of videos to process
MAX_VIDEOS = 10  # Adjust as needed

# Logging configuration
logging.basicConfig(
    filename='youtube_summary.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ------------------------ Helper Functions ----------------------------- #

def sanitize_filename(name):
    """
    Sanitize the search term to create a valid filename.
    Removes or replaces characters that are invalid in filenames.
    """
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Remove any character that is not alphanumeric, underscore, or hyphen
    name = re.sub(r'[^\w\-]', '', name)
    return name

def extract_video_urls(search_query, max_results=10):
    """
    Extract video URLs from YouTube search results using yt-dlp.
    """
    search_url = f"ytsearch{max_results}:{search_query}"
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
        'forcejson': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(search_url, download=False)
            video_entries = result.get('entries', [])
            video_urls = [f"https://www.youtube.com/watch?v={entry['id']}" for entry in video_entries if 'id' in entry]
            logging.info(f"Extracted {len(video_urls)} video URLs for query '{search_query}'.")
            return video_urls
        except Exception as e:
            logging.error(f"Error extracting video URLs: {e}")
            return []

def download_audio(video_url, download_path):
    """
    Download the audio stream of a YouTube video using yt-dlp and convert it to mp3.
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
    }
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(video_url, download=True)
            audio_file = ydl.prepare_filename(info_dict)
            base, ext = os.path.splitext(audio_file)
            new_file = base + '.mp3'
            if os.path.exists(new_file):
                logging.info(f"Downloaded audio for {video_url} to {new_file}.")
                return new_file
            else:
                logging.error(f"Audio file {new_file} does not exist after download.")
                return None
        except Exception as e:
            logging.error(f"Error downloading {video_url}: {e}")
            return None

def transcribe_audio(audio_path, model):
    """
    Transcribe audio to text using Whisper.
    """
    try:
        result = model.transcribe(audio_path)
        logging.info(f"Transcribed audio file {audio_path}.")
        return result['text']
    except Exception as e:
        logging.error(f"Error transcribing {audio_path}: {e}")
        return ""

def summarize_text(text, summarizer):
    """
    Generate a summary of the provided text using a Hugging Face summarization pipeline.
    """
    try:
        # The summarizer has a max token limit; split text if necessary
        max_chunk = 1000  # Adjust based on the model's max input size
        text_chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
        summaries = []
        for chunk in text_chunks:
            summary = summarizer(chunk, max_length=150, min_length=40, do_sample=False)[0]['summary_text']
            summaries.append(summary)
        full_summary = ' '.join(summaries)
        logging.info("Generated summary.")
        return full_summary
    except Exception as e:
        logging.error(f"Error summarizing text: {e}")
        return ""

# --------------------------- Main Script ------------------------------- #

def main():
    if len(sys.argv) != 2:
        print("Usage: python youtube_summary.py <YouTube_Search_Query>")
        print("Example: python youtube_summary.py 'python programming tutorials'")
        sys.exit(1)
    
    search_query = sys.argv[1]
    print(f"Searching YouTube for: {search_query}")
    logging.info(f"Started processing for search query: '{search_query}'.")
    
    # Sanitize search term for filename
    sanitized_search = sanitize_filename(search_query)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    
    # Construct filename
    summary_filename = f"{sanitized_search}-{timestamp}.txt"
    summary_filepath = os.path.join(os.getcwd(), summary_filename)
    
    # Extract video URLs
    video_urls = extract_video_urls(search_query, max_results=MAX_VIDEOS)
    print(f"Found {len(video_urls)} videos.")
    logging.info(f"Found {len(video_urls)} videos for query '{search_query}'.")
    
    if not video_urls:
        print("No videos found. Exiting.")
        logging.warning("No videos found. Exiting.")
        sys.exit(1)
    
    # Initialize Whisper model
    print(f"Loading Whisper model ({WHISPER_MODEL_SIZE})...")
    logging.info(f"Loading Whisper model '{WHISPER_MODEL_SIZE}'.")
    whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
    
    # Initialize summarization pipeline
    print(f"Loading summarization model ({SUMMARIZATION_MODEL})...")
    logging.info(f"Loading summarization model '{SUMMARIZATION_MODEL}'.")
    summarizer = pipeline("summarization", model=SUMMARIZATION_MODEL)
    
    all_transcripts = ""
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        for idx, video_url in enumerate(video_urls, 1):
            try:
                # Extract video title using yt-dlp
                ydl_opts = {
                    'quiet': True,
                    'skip_download': True,
                    'forcejson': True,
                }
                with YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video_url, download=False)
                    video_title = info_dict.get('title', f"Video {idx}")
            except Exception as e:
                print(f"Error fetching video title for {video_url}: {e}")
                logging.error(f"Error fetching video title for {video_url}: {e}")
                video_title = f"Video {idx}"
            
            print(f"\nProcessing Video {idx}: {video_title}")
            print(f"URL: {video_url}")
            logging.info(f"Processing Video {idx}: '{video_title}' - {video_url}")
            
            audio_file = download_audio(video_url, tmpdirname)
            if audio_file:
                print(f"Downloaded audio to {audio_file}")
                logging.info(f"Downloaded audio to {audio_file}.")
                transcript = transcribe_audio(audio_file, whisper_model)
                if transcript:
                    print("Transcription completed.")
                    logging.info(f"Transcription completed for {audio_file}.")
                    # Append transcript with proper section title
                    all_transcripts += f"--- Video {idx}: {video_title} ---\n{transcript}\n\n"
                else:
                    print("No transcript available.")
                    logging.warning(f"No transcript available for {audio_file}.")
            else:
                print("Skipping transcription due to download failure.")
                logging.warning(f"Skipping transcription for {video_url} due to download failure.")
            
            # Introduce a short random delay to mimic human behavior
            time.sleep(random.uniform(1, 3))
    
    if all_transcripts:
        print("\nGenerating summary...")
        logging.info("Starting summarization of transcripts.")
        summary = summarize_text(all_transcripts, summarizer)
        print("\n--- Summary ---\n")
        print(summary)
        
        # Prepare the content to write to the file
        file_content = f"Search Query: {search_query}\nGenerated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        file_content += "=== Transcriptions ===\n\n"
        file_content += all_transcripts
        file_content += "=== Summary ===\n\n"
        file_content += summary
        
        try:
            with open(summary_filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
            print(f"\nSummary saved to '{summary_filename}'.")
            logging.info(f"Summary saved to '{summary_filepath}'.")
        except Exception as e:
            print(f"Error saving summary to file: {e}")
            logging.error(f"Error saving summary to file '{summary_filepath}': {e}")
    else:
        print("No transcripts to summarize.")
        logging.warning("No transcripts to summarize.")

if __name__ == "__main__":
    main()
