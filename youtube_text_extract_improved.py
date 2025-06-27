import os
import re
import sys
import tempfile
import logging
from datetime import datetime
from yt_dlp import YoutubeDL
import whisper
from transformers import pipeline, MarianMTModel, MarianTokenizer
from langdetect import detect

# ---------------------------- Configuration ---------------------------- #

# Whisper model size: 'tiny', 'base', 'small', 'medium', 'large'
WHISPER_MODEL_SIZE = 'large'  # Use a larger model for better accuracy

# Summarization models
SUMMARIZATION_MODELS = {
    'en': "facebook/bart-large-cnn",
    'es': "PlanTL-GOB-ES/roberta-large-bne-sum-sqac",
    'default': "google/mt5-small"  # Fallback for other languages
}

# Logging configuration
logging.basicConfig(
    filename='video_summary.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ------------------------ Helper Functions ----------------------------- #

def sanitize_filename(name):
    """
    Sanitize the video title to create a valid filename.
    Removes or replaces characters that are invalid in filenames.
    """
    name = name.replace(' ', '_')
    return re.sub(r'[^\w\-]', '', name)

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
            'preferredquality': '256',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(video_url, download=True)
            audio_file = ydl.prepare_filename(info_dict)
            base, ext = os.path.splitext(audio_file)
            return base + '.mp3'
        except Exception as e:
            logging.error(f"Error downloading {video_url}: {e}")
            return None

def transcribe_audio(audio_path, model):
    """
    Transcribe audio to text using Whisper.
    """
    try:
        result = model.transcribe(audio_path, task="transcribe")
        logging.info(f"Transcribed audio file {audio_path}.")
        return result['text'], result['language']
    except Exception as e:
        logging.error(f"Error transcribing {audio_path}: {e}")
        return "", None

def load_summarizer(language):
    """
    Load the appropriate summarizer based on the detected language.
    """
    model_name = SUMMARIZATION_MODELS.get(language, SUMMARIZATION_MODELS['default'])
    return pipeline("summarization", model=model_name)

def summarize_text(text, summarizer):
    """
    Generate a summary of the provided text using a Hugging Face summarization pipeline.
    """
    try:
        max_chunk = 1000  # Adjust based on the model's max input size
        text_chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
        summaries = [summarizer(chunk, max_length=150, min_length=40, do_sample=False)[0]['summary_text'] for chunk in text_chunks]
        return ' '.join(summaries)
    except Exception as e:
        logging.error(f"Error summarizing text: {e}")
        return ""

def translate_text(text, source_lang, target_lang="en"):
    """
    Translate text from source_lang to target_lang using MarianMTModel.
    """
    try:
        model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        inputs = tokenizer(text, return_tensors="pt", truncation=True)
        translated = model.generate(**inputs)
        return tokenizer.decode(translated[0], skip_special_tokens=True)
    except Exception as e:
        logging.error(f"Error translating text: {e}")
        return text

# --------------------------- Main Script ------------------------------- #

def main():
    if len(sys.argv) != 2:
        print("Usage: python single_video_summary.py <YouTube_Video_URL>")
        sys.exit(1)

    video_url = sys.argv[1]
    logging.info(f"Started processing video URL: '{video_url}'.")

    try:
        with YoutubeDL({'quiet': True, 'skip_download': True, 'forcejson': True}) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            video_title = info_dict.get('title', 'Unknown_Video')
    except Exception as e:
        logging.error(f"Error fetching video info for {video_url}: {e}")
        sys.exit(1)

    sanitized_title = sanitize_filename(video_title)
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    summary_filename = f"{sanitized_title}-{timestamp}.txt"
    summary_filepath = os.path.join(os.getcwd(), summary_filename)

    logging.info(f"Loading Whisper model '{WHISPER_MODEL_SIZE}'.")
    whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)

    with tempfile.TemporaryDirectory() as tmpdirname:
        audio_file = download_audio(video_url, tmpdirname)
        if audio_file:
            transcript, detected_language = transcribe_audio(audio_file, whisper_model)
            if transcript:
                detected_language = detected_language or detect(transcript)
                logging.info(f"Detected language: {detected_language}")

                summarizer = load_summarizer(detected_language)
                summary = summarize_text(transcript, summarizer)

                if detected_language != 'en':
                    summary = translate_text(summary, source_lang=detected_language, target_lang="en")

                file_content = (f"Video URL: {video_url}\n"
                                f"Video Title: {video_title}\n"
                                f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                f"=== Transcription ===\n\n{transcript}\n\n"
                                f"=== Summary ===\n\n{summary}")

                try:
                    with open(summary_filepath, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                    logging.info(f"Summary saved to '{summary_filepath}'.")
                except Exception as e:
                    logging.error(f"Error saving summary to file: {e}")
            else:
                logging.warning(f"No transcript available for {audio_file}.")
        else:
            logging.warning(f"Failed to download audio for {video_url}.")

if __name__ == "__main__":
    main()
