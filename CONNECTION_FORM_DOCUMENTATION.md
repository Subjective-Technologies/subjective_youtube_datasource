# SubjectiveYouTubeDataSource Enhanced Connection Form

## Overview

The `SubjectiveYouTubeDataSource` class now provides a comprehensive connection form through the `get_connection_data()` method that covers all available YouTube processing features. This allows users to select the appropriate processing mode based on their input type and needs.

## Key Features

### 🎯 **Complete Feature Coverage**
- **Single URL Processing**: 9 different processing modes
- **Batch Processing**: File-based URL lists with resume capability
- **Search Integration**: Query-based video discovery and processing
- **Hardcoded Lists**: Predefined video collections
- **Utility Functions**: URL cleaning and format conversion

### 🔧 **Input Types Supported**

1. **Single YouTube URL** (`single_url`)
   - Individual video processing
   - Support for all URL formats (youtube.com/watch, youtu.be, live, shorts)

2. **File with YouTube URLs** (`url_list_file`)
   - Batch processing from text files
   - Resume capability with start index
   - Error handling and continuation options

3. **YouTube Search Query** (`search_query`)
   - Search-based video discovery
   - Configurable result limits
   - Automated processing of search results

4. **Predefined URL List** (`hardcoded_list`)
   - Curated collections (e.g., interview series)
   - Dual-language processing support

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

## Connection Form Structure

### Main Configuration Fields

```python
{
    'input_type': {
        'type': 'select',
        'required': True,
        'options': [
            {'value': 'single_url', 'label': 'Single YouTube URL'},
            {'value': 'url_list_file', 'label': 'File with YouTube URLs (Batch Processing)'},
            {'value': 'search_query', 'label': 'YouTube Search Query'},
            {'value': 'hardcoded_list', 'label': 'Predefined URL List'}
        ]
    },
    'processing_mode': {
        'type': 'select',
        'required': True,
        'options': [/* 10 processing options with scripts */]
    },
    'input_data': {
        'type': 'textarea',
        'required': True,
        'validation': {
            'single_url': 'YouTube URL regex pattern',
            'search_query': 'Minimum 3 characters',
            'url_list_file': 'File path ending in .txt'
        }
    }
}
```

### Advanced Configuration Groups

#### **Whisper Model Selection**
```python
'whisper_model': {
    'type': 'select',
    'options': ['tiny', 'base', 'small', 'medium', 'large'],
    'show_when': ['transcription_*', 'context_generation', 'custom_class']
}
```

#### **Batch Processing Options**
```python
'batch_options': {
    'type': 'group',
    'show_when': ['url_list_file'],
    'fields': {
        'batch_size': {'type': 'number', 'default': 10, 'min': 1, 'max': 50},
        'start_index': {'type': 'number', 'default': 0, 'min': 0},
        'interactive_mode': {'type': 'checkbox', 'default': True},
        'continue_on_error': {'type': 'checkbox', 'default': True}
    }
}
```

#### **Search Options**
```python
'search_options': {
    'type': 'group',
    'show_when': ['search_summary'],
    'fields': {
        'max_results': {'type': 'number', 'default': 10, 'min': 1, 'max': 50}
    }
}
```

#### **Output Options**
```python
'output_options': {
    'type': 'group',
    'fields': {
        'output_format': {'type': 'select', 'options': ['text', 'json', 'both']},
        'include_metadata': {'type': 'checkbox', 'default': True},
        'clean_urls_first': {'type': 'checkbox', 'show_when': ['url_list_file']},
        'convert_live_urls': {'type': 'checkbox', 'show_when': ['url_list_file']}
    }
}
```

#### **Advanced Options**
```python
'advanced_options': {
    'type': 'group',
    'collapsed': True,
    'fields': {
        'audio_quality': {'type': 'select', 'options': ['128', '192', '256', '320']},
        'max_retries': {'type': 'number', 'default': 3, 'min': 1, 'max': 10},
        'rate_limit_delay': {'type': 'number', 'default': 2, 'min': 0, 'max': 30}
    }
}
```

## Usage Examples

### Basic Usage

```python
from SubjectiveYouTubeDataSource import SubjectiveYouTubeDataSource

# Initialize the data source
youtube_source = SubjectiveYouTubeDataSource({
    'whisper_model_size': 'base',
    'max_retries': 3,
    'audio_quality': '192'
})

# Get the connection form
connection_data = youtube_source.get_connection_data()

# Process user form data
form_data = {
    'input_type': 'single_url',
    'processing_mode': 'custom_class',
    'input_data': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'whisper_model': 'base',
    'output_options': {
        'output_format': 'json',
        'include_metadata': True
    }
}

result = youtube_source.process_connection_form_data(form_data)
```

### Batch Processing Example

```python
form_data = {
    'input_type': 'url_list_file',
    'processing_mode': 'context_generation',
    'input_data': 'youtube_urls.txt',
    'batch_options': {
        'batch_size': 5,
        'start_index': 0,
        'interactive_mode': True,
        'continue_on_error': True
    },
    'output_options': {
        'clean_urls_first': True,
        'convert_live_urls': True
    }
}

result = youtube_source.process_connection_form_data(form_data)
```

### Search Query Example

```python
form_data = {
    'input_type': 'search_query',
    'processing_mode': 'search_summary',
    'input_data': 'machine learning tutorials',
    'search_options': {
        'max_results': 10
    }
}

result = youtube_source.process_connection_form_data(form_data)
```

## System Status Information

The connection form also provides comprehensive status information:

### **Service Status**
- Connection test results
- Service availability
- Last tested timestamp

### **Script Availability**
- All 13 YouTube processing scripts checked
- Individual availability status for each script

### **Dependencies Status**
- Python packages (yt-dlp, openai-whisper, opencv-python, etc.)
- System dependencies (ffmpeg)
- Real-time availability checking

### **Capabilities Matrix**
- Supported URL formats
- Language support
- Output formats available
- Feature flags (batch processing, real-time analysis, etc.)

## Features Mapping

The form provides a complete mapping of input types to available processing modes:

```python
'features_mapping': {
    'single_url': {
        'audio_only': {'script': 'youtube_download_audio.py', 'output': 'MP3 file'},
        'transcription_english': {'script': 'youtube_extractor_english.py', 'output': 'Text file with English transcription + summary'},
        # ... 9 total options
    },
    'url_list_file': {
        'context_generation': {'script': 'process_youtube_batch.py + youtube_to_context.py', 'output': 'Multiple JSON context files'},
        'custom_class': {'script': 'SubjectiveYouTubeDataSource.py', 'output': 'Batch processing via Python class'}
    },
    'search_query': {
        'search_summary': {'script': 'youtube_summary.py', 'output': 'Combined summary of search results'}
    },
    'hardcoded_list': {
        'transcription_dual': {'script': 'youtube_batch_interviews.py', 'output': 'Both Spanish and English processing'}
    }
}
```

## Utility Scripts Integration

The form also provides access to utility scripts:

- **`clean_youtube_links.py`**: Test and filter YouTube URLs for accessibility
- **`convert_live_to_video_urls.py`**: Convert live stream URLs to video URLs

## Implementation Benefits

### 🎯 **Unified Interface**
- Single entry point for all YouTube processing features
- Consistent API across all processing modes
- Standardized configuration options

### 🔄 **Flexible Routing**
- Automatic routing to appropriate scripts based on selections
- Built-in validation and error handling
- Support for both class methods and external scripts

### 📊 **Comprehensive Monitoring**
- Real-time dependency checking
- Script availability verification
- Processing statistics and logging

### 🚀 **Scalable Architecture**
- Easy to add new processing modes
- Modular design for different input types
- Extensible configuration system

## Integration Examples

### Web UI Integration
The form structure is designed to be easily integrated with web frameworks:

```javascript
// Example React component structure
const YouTubeProcessorForm = () => {
  const [inputType, setInputType] = useState('single_url');
  const [processingMode, setProcessingMode] = useState('context_generation');
  
  // Form fields automatically shown/hidden based on selections
  // Validation rules applied based on input type
  // Options filtered based on input type compatibility
};
```

### API Integration
The form can be used to generate REST API endpoints:

```python
@app.post("/api/youtube/process")
async def process_youtube(form_data: dict):
    youtube_source = SubjectiveYouTubeDataSource()
    result = youtube_source.process_connection_form_data(form_data)
    return result
```

## Testing and Validation

Run the example script to see the full functionality:

```bash
python3 example_connection_form_usage.py
```

This will demonstrate:
- ✅ All processing modes
- ✅ Form validation
- ✅ Status checking
- ✅ Error handling
- ✅ Feature mapping display

## Conclusion

The enhanced `get_connection_data()` method provides a complete, production-ready interface for all YouTube processing capabilities. It successfully bridges the gap between individual scripts and a unified user experience, making all features accessible through a single, comprehensive form interface. 