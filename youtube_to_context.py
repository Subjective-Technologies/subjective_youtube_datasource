#!/usr/bin/env python3
"""
YouTube to Context Files Processor
Processes YouTube links and creates context files compatible with the BrainBoost system
"""

import os
import re
import sys
import json
import glob
import tempfile
import time
from datetime import datetime
from yt_dlp import YoutubeDL
import whisper
import logging
from pydub import AudioSegment
from update_context_txt import ContextUpdater

# Configuration
WHISPER_MODEL_SIZE = 'base'  # Adjust based on your system's capabilities

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_to_context.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YouTubeToContextProcessor:
    def __init__(self):
        self.whisper_model = None
        self.context_updater = ContextUpdater()
        
    def load_whisper_model(self):
        """Load the Whisper model for transcription."""
        if self.whisper_model is None:
            print(f"Loading Whisper model ({WHISPER_MODEL_SIZE})...")
            logger.info(f"Loading Whisper model '{WHISPER_MODEL_SIZE}'.")
            self.whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
        return self.whisper_model

    def sanitize_filename(self, name):
        """Sanitize the video title to create a valid filename."""
        name = name.replace(' ', '_')
        name = re.sub(r'[^\w\-]', '', name)
        return name[:50]  # Limit length

    def get_video_info(self, video_url):
        """Get video information using yt-dlp."""
        try:
            with YoutubeDL({'quiet': True, 'skip_download': True, 'forcejson': True}) as ydl:
                info_dict = ydl.extract_info(video_url, download=False)
                
                # Parse upload date from YouTube format (YYYYMMDD) to ISO format
                upload_date_str = info_dict.get('upload_date', '')
                upload_date_iso = None
                if upload_date_str and len(upload_date_str) == 8:
                    try:
                        # Convert YYYYMMDD to YYYY-MM-DDTHH:MM:SS format
                        year = upload_date_str[:4]
                        month = upload_date_str[4:6]
                        day = upload_date_str[6:8]
                        upload_date_iso = f"{year}-{month}-{day}T12:00:00"  # Assume noon UTC
                    except Exception as e:
                        logger.warning(f"Could not parse upload date '{upload_date_str}': {e}")
                
                return {
                    'title': info_dict.get('title', 'Unknown_Video'),
                    'duration': info_dict.get('duration', 0),
                    'upload_date': upload_date_str,
                    'upload_date_iso': upload_date_iso,
                    'uploader': info_dict.get('uploader', 'Unknown'),
                    'view_count': info_dict.get('view_count', 0),
                    'description': info_dict.get('description', '')[:500]  # First 500 chars
                }
        except Exception as e:
            logger.error(f"Error fetching video info for {video_url}: {e}")
            return None

    def download_audio(self, video_url, download_path, max_retries=3):
        """Download the audio stream of a YouTube video using yt-dlp."""
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
                    logger.info(f"Downloaded video: {info_dict.get('title', 'Unknown Title')}")
                
                # Find the mp3 file
                mp3_files = glob.glob(os.path.join(download_path, "*.mp3"))
                if mp3_files:
                    audio_file = mp3_files[0]
                    logger.info(f"Found audio file: {audio_file}")
                    return audio_file
                else:
                    logger.error("No MP3 file was found after download.")
                    return None
            except Exception as e:
                attempt += 1
                logger.error(f"Attempt {attempt} - Error downloading {video_url}: {e}")
                if attempt < max_retries:
                    time.sleep(3)
                else:
                    return None

    def convert_to_mono_wav(self, mp3_path, output_path):
        """Convert an MP3 file to a mono WAV file."""
        try:
            audio = AudioSegment.from_mp3(mp3_path)
            audio = audio.set_channels(1)  # Convert to mono
            audio.export(output_path, format="wav")
            logger.info(f"Converted {mp3_path} to mono WAV at {output_path}.")
            return output_path
        except Exception as e:
            logger.error(f"Error converting {mp3_path} to WAV: {e}")
            return None

    def transcribe_audio(self, audio_path, model):
        """Transcribe audio to text using Whisper."""
        try:
            result = model.transcribe(audio_path)
            transcript = result.get('text', "")
            language = result.get('language', "unknown")
            logger.info(f"Transcribed audio file {audio_path} with detected language: {language}.")
            return transcript, language
        except Exception as e:
            logger.error(f"Error transcribing {audio_path}: {e}")
            return "", "unknown"

    def create_context_file(self, video_url, video_info, transcript, language):
        """Create a context file in the same format as existing ones."""
        try:
            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            context_filename = f"context-{timestamp}.json"
            context_filepath = os.path.join("context", context_filename)
            
            # Ensure context directory exists
            os.makedirs("context", exist_ok=True)
            
            # Create video filename from title (use actual title, not sanitized)
            video_filename = video_info['title']
            
            # Use YouTube upload date as video_recording_time if available
            video_recording_time = video_info.get('upload_date_iso')
            
            # Format transcription with enhanced metadata
            formatted_transcription = (
                f"URL del Video: {video_url}\n"
                f"Título del Video: {video_info['title']}\n"
                f"Canal: {video_info.get('uploader', 'Unknown')}\n"
                f"Fecha de Subida: {video_info.get('upload_date', 'Unknown')}\n"
                f"Duración: {video_info.get('duration', 'Unknown')} segundos\n"
                f"Vistas: {video_info.get('view_count', 'Unknown'):,}\n"
                f"Idioma Detectado: {language}\n"
                f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            
            # Add description if available
            if video_info.get('description'):
                formatted_transcription += (
                    "=== Descripción del Video ===\n\n"
                    f"{video_info['description']}\n\n"
                )
            
            formatted_transcription += (
                "=== Transcripción ===\n\n"
                f"{transcript}\n\n"
                "=== Resumen ===\n\n"
                "Resumen generado automáticamente desde YouTube."
            )
            
            # Create context data structure
            context_data = {
                "video_path": video_url,
                "video_filename": video_filename,
                "video_hash": None,
                "video_size": None,
                "video_mtime": None,
                "video_recording_time": video_recording_time,  # Use YouTube upload date
                "transcription_time": datetime.now().isoformat(),
                "whisper_model": WHISPER_MODEL_SIZE,
                "transcription": formatted_transcription
            }
            
            # Save context file
            with open(context_filepath, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created context file: {context_filepath}")
            print(f"✅ Created context file: {context_filename}")
            
            return context_filepath
            
        except Exception as e:
            logger.error(f"Error creating context file: {e}")
            return None

    def process_youtube_video(self, video_url):
        """Process a single YouTube video and create a context file."""
        print(f"\n🎥 Processing: {video_url}")
        logger.info(f"Started processing video URL: '{video_url}'.")
        
        # Get video information
        video_info = self.get_video_info(video_url)
        if not video_info:
            print(f"❌ Failed to get video info for: {video_url}")
            return False
        
        print(f"📹 Title: {video_info['title']}")
        print(f"👤 Channel: {video_info.get('uploader', 'Unknown')}")
        print(f"📅 Upload Date: {video_info.get('upload_date', 'Unknown')}")
        print(f"⏱️  Duration: {video_info.get('duration', 'Unknown')} seconds")
        print(f"👀 Views: {video_info.get('view_count', 'Unknown'):,}")
        
        # Load Whisper model
        model = self.load_whisper_model()
        
        # Create temporary directory for audio processing
        with tempfile.TemporaryDirectory() as tmpdirname:
            print("📥 Downloading audio...")
            audio_file = self.download_audio(video_url, tmpdirname)
            
            if not audio_file:
                print(f"❌ Failed to download audio for: {video_url}")
                return False
            
            print(f"✅ Downloaded audio: {os.path.basename(audio_file)}")
            
            # Convert to WAV for better transcription
            wav_path = os.path.join(tmpdirname, "audio_mono.wav")
            converted_audio = self.convert_to_mono_wav(audio_file, wav_path)
            
            if not converted_audio:
                print("❌ Failed to convert audio to WAV")
                return False
            
            # Transcribe audio
            print("🎤 Transcribing audio...")
            transcript, language = self.transcribe_audio(converted_audio, model)
            
            if not transcript.strip():
                print("❌ No transcript was generated")
                return False
            
            print(f"✅ Transcription completed (Language: {language})")
            print(f"📝 Transcript length: {len(transcript)} characters")
            
            # Create context file
            context_file = self.create_context_file(video_url, video_info, transcript, language)
            
            if context_file:
                # Update context.txt automatically
                print("📄 Updating context.txt...")
                try:
                    new_count = self.context_updater.check_for_new_files()
                    if new_count > 0:
                        print(f"✅ Added to context.txt (Recording #{new_count})")
                    else:
                        print("ℹ️  Context.txt already up to date")
                except Exception as e:
                    print(f"⚠️  Warning: Could not update context.txt: {e}")
                
                return True
            else:
                print("❌ Failed to create context file")
                return False

    def process_youtube_links_file(self, links_file):
        """Process all YouTube links from a file."""
        try:
            with open(links_file, 'r', encoding='utf-8') as f:
                links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            print(f"🚀 YOUTUBE TO CONTEXT PROCESSOR")
            print(f"=" * 50)
            print(f"📁 Links file: {links_file}")
            print(f"🔗 Found {len(links)} YouTube links")
            print(f"=" * 50)
            
            successful = 0
            failed = 0
            
            for i, link in enumerate(links, 1):
                print(f"\n[{i}/{len(links)}] Processing link...")
                
                if self.process_youtube_video(link):
                    successful += 1
                    print(f"✅ Success! ({successful}/{i})")
                else:
                    failed += 1
                    print(f"❌ Failed! ({failed}/{i})")
                
                # Small delay between videos to avoid rate limiting
                if i < len(links):
                    print("⏳ Waiting 5 seconds before next video...")
                    time.sleep(5)
            
            print(f"\n" + "=" * 50)
            print(f"📊 PROCESSING COMPLETE!")
            print(f"=" * 50)
            print(f"✅ Successful: {successful}")
            print(f"❌ Failed: {failed}")
            print(f"📈 Success rate: {(successful/len(links)*100):.1f}%")
            
            if successful > 0:
                print(f"\n💡 Next steps:")
                print(f"• Check context/ folder for new context files")
                print(f"• context.txt has been automatically updated")
                print(f"• Upload updated context.txt to ChatGPT for enhanced queries!")
            
            return successful > 0
            
        except Exception as e:
            logger.error(f"Error processing links file: {e}")
            print(f"❌ Error reading links file: {e}")
            return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 youtube_to_context.py <youtube_links_file>")
        print("  python3 youtube_to_context.py <single_youtube_url>")
        print()
        print("Examples:")
        print("  python3 youtube_to_context.py youtube_list_of_links.txt")
        print("  python3 youtube_to_context.py https://youtube.com/watch?v=abc123")
        sys.exit(1)
    
    processor = YouTubeToContextProcessor()
    
    input_arg = sys.argv[1]
    
    # Check if it's a file or a URL
    if os.path.isfile(input_arg):
        # Process file with multiple links
        success = processor.process_youtube_links_file(input_arg)
    elif input_arg.startswith(('http://', 'https://')):
        # Process single URL
        print(f"🚀 YOUTUBE TO CONTEXT PROCESSOR")
        print(f"=" * 50)
        success = processor.process_youtube_video(input_arg)
    else:
        print(f"❌ Error: '{input_arg}' is not a valid file or URL")
        sys.exit(1)
    
    if success:
        print(f"\n🎉 Processing completed successfully!")
    else:
        print(f"\n💥 Processing failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 