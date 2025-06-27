# YouTube Data Source for BrainBoost

A comprehensive YouTube content processing system that provides multiple ways to extract, transcribe, and analyze YouTube videos. This project includes both a unified Python class interface and individual processing scripts for different use cases.

## 🚀 Features

### 🎯 **Complete Feature Coverage**
- **Single URL Processing**: 9 different processing modes
- **Batch Processing**: File-based URL lists with resume capability  
- **Search Integration**: Query-based video discovery and processing
- **Hardcoded Lists**: Predefined video collections
- **Utility Functions**: URL cleaning and format conversion

### 🔧 **Input Types Supported**

1. **Single YouTube URL** - Individual video processing
2. **File with YouTube URLs** - Batch processing from text files
3. **YouTube Search Query** - Search-based video discovery
4. **Predefined URL List** - Curated collections

### ⚙️ **Processing Modes Available**

| Mode | Script | Output | Input Types |
|------|---------|---------|-------------|
| **Audio Download Only** | `youtube_download_audio.py` | MP3 files | Single URL |
| **Transcription + Summary (English)** | `youtube_extractor_english.py` | English text + summary | Single URL |
| **Transcription + Summary (Spanish)** | `youtube_extractor_spanish.py` | Spanish text + summary | Single URL |
| **Transcription + Summary (Auto Language)** | `youtube_text_extract.py` | Auto-language text + summary | Single URL |
| **Enhanced Multi-language + Translation** | `youtube_text_extract_improved.py` | Multi-language with translation | Single URL |
| **BrainBoost Context Files** | `youtube_to_context.py` / `process_youtube_batch.py` | JSON context files | Single URL / Batch |
| **Body Language Analysis** | `youtube_bodylanguage_extractor.py` | Video analysis + body language report | Single URL |
| **Real-time Body Language Analysis** | `youtube_bodylanguage_extractor_1.py` | Real-time body language analysis | Single URL |
| **Search Results Summary** | `youtube_summary.py` | Combined summary of search results | Search Query |
| **Dual Language Processing** | `youtube_batch_interviews.py` | Both Spanish and English processing | Hardcoded List |
| **Custom Class Processing** | `SubjectiveYouTubeDataSource.py` | Structured data via Python class | Single URL / Batch |

## 📦 Installation

### Prerequisites
- Python 3.8+
- FFmpeg (for audio processing)

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/Subjective-Technologies/youtube_datasource.git
cd youtube_datasource
```

2. **Create and activate virtual environment:**
```bash
python3 -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Install FFmpeg (if not already installed):**
   - **Ubuntu/Debian:** `sudo apt install ffmpeg`
   - **macOS:** `brew install ffmpeg`
   - **Windows:** Download from [https://ffmpeg.org/](https://ffmpeg.org/)

## 🎯 Quick Start

### Using the Unified Class Interface

```python
from SubjectiveYouTubeDataSource import SubjectiveYouTubeDataSource

# Initialize the data source
config = {
    'whisper_model_size': 'base',
    'max_retries': 3,
    'audio_quality': '192'
}

youtube_source = SubjectiveYouTubeDataSource(config)

# Get the comprehensive connection form
connection_data = youtube_source.get_connection_data()

# Process user form data
form_data = {
    'input_type': 'single_url',
    'processing_mode': 'context_generation',
    'input_data': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'whisper_model': 'base',
    'output_options': {
        'output_format': 'json',
        'include_metadata': True
    }
}

result = youtube_source.process_connection_form_data(form_data)
print(f"Processing result: {result['success']}")

# Cleanup
youtube_source.cleanup()
```

### Using Individual Scripts

#### Single Video Processing
```bash
# Download audio only
python3 youtube_download_audio.py "https://youtube.com/watch?v=VIDEO_ID"

# Transcribe and summarize (English)
python3 youtube_extractor_english.py "https://youtube.com/watch?v=VIDEO_ID"

# Create BrainBoost context files
python3 youtube_to_context.py "https://youtube.com/watch?v=VIDEO_ID"
```

#### Batch Processing
```bash
# Process multiple URLs from file
python3 process_youtube_batch.py youtube_urls.txt

# Create context files from URL list
python3 youtube_to_context.py youtube_urls.txt
```

#### Search-Based Processing
```bash
# Process search results
python3 youtube_summary.py "machine learning tutorials"
```

## 📋 Connection Form Interface

The `SubjectiveYouTubeDataSource` class provides a comprehensive connection form through the `get_connection_data()` method that covers all available YouTube processing features:

```python
# Get the connection form configuration
connection_data = youtube_source.get_connection_data()

# The form includes:
# - Input type selection (single URL, batch file, search query, hardcoded list)
# - Processing mode selection (10+ different modes)
# - Whisper model configuration
# - Batch processing options
# - Search options  
# - Output format options
# - Advanced settings (audio quality, retries, rate limiting)
```

See `CONNECTION_FORM_DOCUMENTATION.md` for complete details.

## 🧪 Examples

### Example 1: Basic Usage
```python
# Run the example script
python3 example_connection_form_usage.py
```

### Example 2: Batch Processing
Create a file `youtube_urls.txt` with one URL per line:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://www.youtube.com/watch?v=9bZkp7q19f0
https://www.youtube.com/watch?v=kJQP7kiw5Fk
```

Then process:
```bash
python3 process_youtube_batch.py youtube_urls.txt
```

### Example 3: URL Cleaning
```bash
# Clean and validate URLs
python3 clean_youtube_links.py youtube_urls.txt

# Convert live URLs to video URLs  
python3 convert_live_to_video_urls.py youtube_urls.txt
```

## 📁 Project Structure

```
youtube_datasource/
├── SubjectiveYouTubeDataSource.py          # Main unified class interface
├── update_context_txt.py                   # Context file management
├── example_connection_form_usage.py        # Usage examples
├── CONNECTION_FORM_DOCUMENTATION.md        # Complete documentation
├── requirements.txt                        # Python dependencies
├── 
├── # Individual processing scripts
├── youtube_download_audio.py               # Audio-only extraction
├── youtube_extractor_english.py            # English transcription
├── youtube_extractor_spanish.py            # Spanish transcription  
├── youtube_text_extract.py                 # Auto-language processing
├── youtube_text_extract_improved.py        # Enhanced multi-language
├── youtube_to_context.py                   # BrainBoost context generation
├── youtube_bodylanguage_extractor.py       # Body language analysis
├── youtube_bodylanguage_extractor_1.py     # Real-time body language
├── youtube_summary.py                      # Search-based summarization
├── youtube_batch_interviews.py             # Hardcoded interview processing
├── 
├── # Batch and utility scripts
├── process_youtube_batch.py                # Advanced batch processing
├── clean_youtube_links.py                  # URL validation
└── convert_live_to_video_urls.py           # URL format conversion
```

## 🔧 Configuration

### Whisper Models
- `tiny`: Fastest, least accurate
- `base`: Balanced (recommended)
- `small`: Good accuracy
- `medium`: Better accuracy  
- `large`: Best accuracy, slowest

### Audio Quality Options
- `128`: Lower quality, faster
- `192`: Balanced (recommended)
- `256`: Higher quality
- `320`: Highest quality

## 📊 Dependencies

### Core Dependencies
- `yt-dlp`: YouTube downloading
- `openai-whisper`: Audio transcription
- `pydub`: Audio processing
- `ffmpeg-python`: Audio conversion

### Optional Dependencies  
- `opencv-python`: Video analysis
- `mediapipe`: Body language analysis
- `transformers`: Enhanced NLP
- `torch`: Machine learning models

### System Dependencies
- `ffmpeg`: Audio/video processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloading capabilities
- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [MediaPipe](https://mediapipe.dev/) for body language analysis
- [FFmpeg](https://ffmpeg.org/) for audio/video processing

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

---

**Made with ❤️ by Subjective Technologies** 