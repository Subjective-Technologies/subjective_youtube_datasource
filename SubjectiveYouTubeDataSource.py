#!/usr/bin/env python3
"""
SubjectiveYouTubeDataSource - A data source implementation for processing YouTube videos
Extends the SubjectiveDataSource abstract base class to provide YouTube-specific functionality
"""

import os
import re
import json
import glob
import tempfile
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from yt_dlp import YoutubeDL
import whisper
import logging
from pydub import AudioSegment

# Import from the abstract base class package
from subjective_abstract_data_source_package import SubjectiveDataSource
from brainboost_data_source_logger_package import BBLogger
from brainboost_configuration_package import BBConfig

class SubjectiveYouTubeDataSource(SubjectiveDataSource):
    """
    YouTube Data Source implementation that processes YouTube videos for transcription and analysis.
    
    This class extends SubjectiveDataSource to provide YouTube-specific functionality including:
    - Video metadata extraction
    - Audio downloading and transcription
    - Context file generation
    - Batch processing capabilities
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the YouTube data source.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        
        # Initialize logger
        self.logger = BBLogger()
        
        # Configuration
        bb_config = BBConfig()
        self.config = config or bb_config.read_config()
        self.whisper_model_size = self.config.get('whisper_model_size', 'base')
        self.max_retries = self.config.get('max_retries', 3)
        self.audio_quality = self.config.get('audio_quality', '192')
        
        # Internal state
        self.whisper_model = None
        self._stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'total_duration': 0
        }
        
        self._log_info(f"Initialized SubjectiveYouTubeDataSource with Whisper model: {self.whisper_model_size}")
    
    def _log_info(self, message: str):
        """Helper method for info logging."""
        self.logger.log(f"INFO: {message}")
    
    def _log_warning(self, message: str):
        """Helper method for warning logging."""
        self.logger.log(f"WARNING: {message}")
    
    def _log_error(self, message: str):
        """Helper method for error logging."""
        self.logger.log(f"ERROR: {message}")
    
    def get_data_source_type(self) -> str:
        """Return the type identifier for this data source."""
        return "youtube"
    
    def get_supported_formats(self) -> List[str]:
        """Return list of supported URL formats."""
        return [
            "youtube.com/watch?v=",
            "youtu.be/",
            "youtube.com/live/",
            "youtube.com/shorts/"
        ]
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate that the input is a valid YouTube URL.
        
        Args:
            input_data: Input to validate (should be a YouTube URL string)
            
        Returns:
            bool: True if valid YouTube URL, False otherwise
        """
        if not isinstance(input_data, str):
            return False
            
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/live/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+'
        ]
        
        return any(re.match(pattern, input_data.strip()) for pattern in youtube_patterns)
    
    def extract_metadata(self, source_input: str) -> Dict[str, Any]:
        """
        Extract metadata from a YouTube video.
        
        Args:
            source_input: YouTube URL
            
        Returns:
            Dict containing video metadata
        """
        try:
            with YoutubeDL({'quiet': True, 'skip_download': True, 'forcejson': True}) as ydl:
                info_dict = ydl.extract_info(source_input, download=False)
                
                # Parse upload date from YouTube format (YYYYMMDD) to ISO format
                upload_date_str = info_dict.get('upload_date', '')
                upload_date_iso = None
                if upload_date_str and len(upload_date_str) == 8:
                    try:
                        year = upload_date_str[:4]
                        month = upload_date_str[4:6]
                        day = upload_date_str[6:8]
                        upload_date_iso = f"{year}-{month}-{day}T12:00:00"
                    except Exception as e:
                        self._log_warning(f"Could not parse upload date '{upload_date_str}': {e}")
                
                metadata = {
                    'video_id': info_dict.get('id', ''),
                    'title': info_dict.get('title', 'Unknown_Video'),
                    'duration': info_dict.get('duration', 0),
                    'upload_date': upload_date_str,
                    'upload_date_iso': upload_date_iso,
                    'uploader': info_dict.get('uploader', 'Unknown'),
                    'uploader_id': info_dict.get('uploader_id', ''),
                    'view_count': info_dict.get('view_count', 0),
                    'like_count': info_dict.get('like_count', 0),
                    'description': info_dict.get('description', '')[:1000],  # First 1000 chars
                    'tags': info_dict.get('tags', []),
                    'categories': info_dict.get('categories', []),
                    'url': source_input,
                    'thumbnail': info_dict.get('thumbnail', ''),
                    'language': info_dict.get('language', 'unknown')
                }
                
                self._log_info(f"Extracted metadata for video: {metadata['title']}")
                return metadata
                
        except Exception as e:
            self._log_error(f"Error extracting metadata for {source_input}: {e}")
            return {}
    
    def process_source(self, source_input: str) -> Dict[str, Any]:
        """
        Process a YouTube video source to extract audio and generate transcription.
        
        Args:
            source_input: YouTube URL to process
            
        Returns:
            Dict containing processed data including transcription and metadata
        """
        if not self.validate_input(source_input):
            raise ValueError(f"Invalid YouTube URL: {source_input}")
        
        self._log_info(f"Processing YouTube video: {source_input}")
        start_time = time.time()
        
        try:
            # Extract metadata
            metadata = self.extract_metadata(source_input)
            if not metadata:
                raise Exception("Failed to extract video metadata")
            
            # Load Whisper model
            model = self._load_whisper_model()
            
            # Process audio and transcription
            with tempfile.TemporaryDirectory() as temp_dir:
                # Download audio
                audio_file = self._download_audio(source_input, temp_dir)
                if not audio_file:
                    raise Exception("Failed to download audio")
                
                # Convert to WAV for better transcription
                wav_path = os.path.join(temp_dir, "audio_mono.wav")
                converted_audio = self._convert_to_mono_wav(audio_file, wav_path)
                if not converted_audio:
                    raise Exception("Failed to convert audio to WAV")
                
                # Transcribe audio
                transcript, detected_language = self._transcribe_audio(converted_audio, model)
                if not transcript.strip():
                    raise Exception("No transcript was generated")
            
            # Create processed data structure
            processed_data = {
                'source_url': source_input,
                'metadata': metadata,
                'transcription': {
                    'text': transcript,
                    'language': detected_language,
                    'model_used': self.whisper_model_size,
                    'transcription_time': datetime.now().isoformat()
                },
                'processing_info': {
                    'processed_at': datetime.now().isoformat(),
                    'processing_duration': time.time() - start_time,
                    'data_source_type': self.get_data_source_type()
                }
            }
            
            # Update statistics
            self._stats['processed'] += 1
            self._stats['successful'] += 1
            self._stats['total_duration'] += metadata.get('duration', 0)
            
            self._log_info(f"Successfully processed video: {metadata['title']}")
            return processed_data
            
        except Exception as e:
            self._stats['processed'] += 1
            self._stats['failed'] += 1
            self._log_error(f"Error processing {source_input}: {e}")
            raise
    
    def process_batch(self, source_inputs: List[str], **kwargs) -> List[Dict[str, Any]]:
        """
        Process multiple YouTube videos in batch.
        
        Args:
            source_inputs: List of YouTube URLs to process
            **kwargs: Additional processing options
            
        Returns:
            List of processed data dictionaries
        """
        batch_size = kwargs.get('batch_size', 10)
        continue_on_error = kwargs.get('continue_on_error', True)
        
        self._log_info(f"Starting batch processing of {len(source_inputs)} YouTube videos")
        
        results = []
        failed_urls = []
        
        for i, url in enumerate(source_inputs, 1):
            try:
                self._log_info(f"Processing video {i}/{len(source_inputs)}: {url}")
                result = self.process_source(url)
                results.append(result)
                
                # Small delay to avoid rate limiting
                if i < len(source_inputs):
                    time.sleep(2)
                    
            except Exception as e:
                failed_urls.append({'url': url, 'error': str(e)})
                self._log_error(f"Failed to process video {i}: {url} - {e}")
                
                if not continue_on_error:
                    break
        
        # Log batch processing summary
        success_count = len(results)
        failure_count = len(failed_urls)
        success_rate = (success_count / len(source_inputs)) * 100 if source_inputs else 0
        
        self._log_info(f"Batch processing complete: {success_count} successful, {failure_count} failed ({success_rate:.1f}% success rate)")
        
        return results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics for this data source instance.
        
        Returns:
            Dict containing processing statistics
        """
        return {
            'total_processed': self._stats['processed'],
            'successful': self._stats['successful'],
            'failed': self._stats['failed'],
            'success_rate': (self._stats['successful'] / max(self._stats['processed'], 1)) * 100,
            'total_video_duration': self._stats['total_duration'],
            'average_duration': self._stats['total_duration'] / max(self._stats['successful'], 1),
            'data_source_type': self.get_data_source_type()
        }
    
    def cleanup(self):
        """Clean up resources used by the data source."""
        if self.whisper_model is not None:
            # Whisper models don't need explicit cleanup, but we can clear the reference
            self.whisper_model = None
            self._log_info("Cleaned up Whisper model")
    
    # Abstract methods from SubjectiveDataSource that must be implemented
    
    def fetch(self) -> Dict[str, Any]:
        """
        Main fetch method required by the abstract base class.
        
        This method serves as the primary interface for fetching data.
        For YouTube data source, this returns general information about the data source.
        
        Returns:
            Dict containing data source information and capabilities
        """
        return {
            'data_source_type': self.get_data_source_type(),
            'supported_formats': self.get_supported_formats(),
            'capabilities': {
                'metadata_extraction': True,
                'audio_transcription': True,
                'batch_processing': True,
                'multiple_languages': True,
                'quality_options': ['tiny', 'base', 'small', 'medium', 'large']
            },
            'configuration': {
                'whisper_model_size': self.whisper_model_size,
                'max_retries': self.max_retries,
                'audio_quality': self.audio_quality
            },
            'statistics': self.get_processing_stats(),
            'status': 'ready'
        }
    
    def get_connection_data(self) -> Dict[str, Any]:
        """
        Get connection data for the YouTube data source.
        
        Returns a comprehensive connection form that covers all available YouTube processing features.
        This allows users to select the appropriate processing mode based on their input type and needs.
        
        Returns:
            Dict containing connection form configuration with all available features
        """
        # Test YouTube service availability
        test_connection = self._test_youtube_connection()
        
        return {
            'service_name': 'YouTube Data Processor',
            'service_url': 'https://www.youtube.com',
            'connection_status': 'connected' if test_connection else 'disconnected',
            'last_tested': datetime.now().isoformat(),
            'description': 'Comprehensive YouTube content processing with multiple output formats and analysis options',
            
            # Connection form fields for user input
            'connection_form': {
                'input_type': {
                    'type': 'select',
                    'label': 'Input Type',
                    'required': True,
                    'options': [
                        {'value': 'single_url', 'label': 'Single YouTube URL'},
                        {'value': 'url_list_file', 'label': 'File with YouTube URLs (Batch Processing)'},
                        {'value': 'search_query', 'label': 'YouTube Search Query'},
                        {'value': 'hardcoded_list', 'label': 'Predefined URL List'}
                    ],
                    'default': 'single_url',
                    'description': 'Choose how you want to provide YouTube content to process'
                },
                
                'processing_mode': {
                    'type': 'select',
                    'label': 'Processing Mode',
                    'required': True,
                    'options': [
                        {'value': 'audio_only', 'label': 'Audio Download Only', 'script': 'youtube_download_audio.py'},
                        {'value': 'transcription_english', 'label': 'Transcription + Summary (English)', 'script': 'youtube_extractor_english.py'},
                        {'value': 'transcription_spanish', 'label': 'Transcription + Summary (Spanish)', 'script': 'youtube_extractor_spanish.py'},
                        {'value': 'transcription_auto', 'label': 'Transcription + Summary (Auto Language)', 'script': 'youtube_text_extract.py'},
                        {'value': 'transcription_improved', 'label': 'Enhanced Multi-language + Translation', 'script': 'youtube_text_extract_improved.py'},
                        {'value': 'context_generation', 'label': 'BrainBoost Context Files', 'script': 'youtube_to_context.py'},
                        {'value': 'body_language', 'label': 'Body Language Analysis', 'script': 'youtube_bodylanguage_extractor.py'},
                        {'value': 'body_language_live', 'label': 'Real-time Body Language Analysis', 'script': 'youtube_bodylanguage_extractor_1.py'},
                        {'value': 'search_summary', 'label': 'Search Results Summary', 'script': 'youtube_summary.py'},
                        {'value': 'custom_class', 'label': 'Use SubjectiveYouTubeDataSource Class', 'script': 'SubjectiveYouTubeDataSource.py'}
                    ],
                    'default': 'context_generation',
                    'description': 'Select the type of processing you want to perform'
                },
                
                'input_data': {
                    'type': 'textarea',
                    'label': 'Input Data',
                    'required': True,
                    'placeholder': 'Enter YouTube URL, search query, or file path...',
                    'description': 'Provide the input based on your selected input type',
                    'validation': {
                        'single_url': r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/live/|youtube\.com/shorts/)[\w-]+',
                        'search_query': r'.{3,}',  # At least 3 characters
                        'url_list_file': r'.*\.txt$',  # File path ending in .txt
                    }
                },
                
                'whisper_model': {
                    'type': 'select',
                    'label': 'Whisper Model Size',
                    'required': False,
                    'options': [
                        {'value': 'tiny', 'label': 'Tiny (fastest, least accurate)'},
                        {'value': 'base', 'label': 'Base (balanced)'},
                        {'value': 'small', 'label': 'Small (good accuracy)'},
                        {'value': 'medium', 'label': 'Medium (better accuracy)'},
                        {'value': 'large', 'label': 'Large (best accuracy, slowest)'}
                    ],
                    'default': 'base',
                    'description': 'Select Whisper model size for transcription (applicable to transcription modes)',
                    'show_when': ['transcription_english', 'transcription_spanish', 'transcription_auto', 'transcription_improved', 'context_generation', 'custom_class']
                },
                
                'batch_options': {
                    'type': 'group',
                    'label': 'Batch Processing Options',
                    'show_when': ['url_list_file'],
                    'fields': {
                        'batch_size': {
                            'type': 'number',
                            'label': 'Batch Size',
                            'default': 10,
                            'min': 1,
                            'max': 50,
                            'description': 'Number of videos to process in each batch'
                        },
                        'start_index': {
                            'type': 'number',
                            'label': 'Start Index',
                            'default': 0,
                            'min': 0,
                            'description': 'Index to start processing from (for resume capability)'
                        },
                        'interactive_mode': {
                            'type': 'checkbox',
                            'label': 'Interactive Mode',
                            'default': True,
                            'description': 'Enable progress bars and interactive feedback'
                        },
                        'continue_on_error': {
                            'type': 'checkbox',
                            'label': 'Continue on Error',
                            'default': True,
                            'description': 'Continue processing even if some videos fail'
                        }
                    }
                },
                
                'search_options': {
                    'type': 'group',
                    'label': 'Search Options',
                    'show_when': ['search_summary'],
                    'fields': {
                        'max_results': {
                            'type': 'number',
                            'label': 'Maximum Results',
                            'default': 10,
                            'min': 1,
                            'max': 50,
                            'description': 'Maximum number of videos to process from search results'
                        }
                    }
                },
                
                'output_options': {
                    'type': 'group',
                    'label': 'Output Options',
                    'fields': {
                        'output_format': {
                            'type': 'select',
                            'label': 'Output Format',
                            'options': [
                                {'value': 'text', 'label': 'Text Files (.txt)'},
                                {'value': 'json', 'label': 'JSON Files (.json)'},
                                {'value': 'both', 'label': 'Both Text and JSON'}
                            ],
                            'default': 'json',
                            'description': 'Choose output file format'
                        },
                        'include_metadata': {
                            'type': 'checkbox',
                            'label': 'Include Video Metadata',
                            'default': True,
                            'description': 'Include video title, duration, views, etc. in output'
                        },
                        'clean_urls_first': {
                            'type': 'checkbox',
                            'label': 'Clean URLs Before Processing',
                            'default': True,
                            'description': 'Test and filter URLs before processing (recommended for batch)',
                            'show_when': ['url_list_file']
                        },
                        'convert_live_urls': {
                            'type': 'checkbox',
                            'label': 'Convert Live URLs to Video URLs',
                            'default': True,
                            'description': 'Automatically convert live stream URLs to video URLs',
                            'show_when': ['url_list_file']
                        }
                    }
                },
                
                'advanced_options': {
                    'type': 'group',
                    'label': 'Advanced Options',
                    'collapsed': True,
                    'fields': {
                        'audio_quality': {
                            'type': 'select',
                            'label': 'Audio Quality',
                            'options': [
                                {'value': '128', 'label': '128 kbps (lower quality, faster)'},
                                {'value': '192', 'label': '192 kbps (balanced)'},
                                {'value': '256', 'label': '256 kbps (higher quality)'},
                                {'value': '320', 'label': '320 kbps (highest quality)'}
                            ],
                            'default': '192',
                            'description': 'Audio quality for downloaded files'
                        },
                        'max_retries': {
                            'type': 'number',
                            'label': 'Maximum Retries',
                            'default': 3,
                            'min': 1,
                            'max': 10,
                            'description': 'Number of retry attempts for failed downloads'
                        },
                        'rate_limit_delay': {
                            'type': 'number',
                            'label': 'Rate Limit Delay (seconds)',
                            'default': 2,
                            'min': 0,
                            'max': 30,
                            'description': 'Delay between video processing to avoid rate limiting'
                        }
                    }
                }
            },
            
            # Available features mapping
            'features_mapping': {
                'single_url': {
                    'audio_only': {'script': 'youtube_download_audio.py', 'output': 'MP3 file'},
                    'transcription_english': {'script': 'youtube_extractor_english.py', 'output': 'Text file with English transcription + summary'},
                    'transcription_spanish': {'script': 'youtube_extractor_spanish.py', 'output': 'Text file with Spanish transcription + summary'},
                    'transcription_auto': {'script': 'youtube_text_extract.py', 'output': 'Text file with auto-language transcription + summary'},
                    'transcription_improved': {'script': 'youtube_text_extract_improved.py', 'output': 'Text file with enhanced multi-language processing'},
                    'context_generation': {'script': 'youtube_to_context.py', 'output': 'JSON context files for BrainBoost'},
                    'body_language': {'script': 'youtube_bodylanguage_extractor.py', 'output': 'Video analysis + body language report'},
                    'body_language_live': {'script': 'youtube_bodylanguage_extractor_1.py', 'output': 'Real-time body language analysis'},
                    'custom_class': {'script': 'SubjectiveYouTubeDataSource.py', 'output': 'Structured data via Python class'}
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
            },
            
            # Utility scripts information
            'utility_scripts': {
                'clean_youtube_links.py': 'Test and filter YouTube URLs for accessibility',
                'convert_live_to_video_urls.py': 'Convert live stream URLs to video URLs'
            },
            
            # Service capabilities
            'capabilities': {
                'supported_formats': ['youtube.com/watch', 'youtu.be', 'youtube.com/live', 'youtube.com/shorts'],
                'languages_supported': ['Auto-detect', 'English', 'Spanish', 'Multi-language with translation'],
                'output_formats': ['MP3', 'TXT', 'JSON', 'Video frames', 'Analysis reports'],
                'batch_processing': True,
                'real_time_analysis': True,
                'search_integration': True,
                'body_language_analysis': True,
                'brainboost_integration': True
            },
            
            # Status information
            'status': {
                'connection_test': test_connection,
                'scripts_available': self._check_script_availability(),
                'dependencies_status': self._check_dependencies_status()
            }
        }
    
    def get_icon(self) -> str:
        """
        Get an icon representation for the YouTube data source.
        
        Returns:
            String representation of the YouTube icon (SVG code)
        """
        return '''<svg viewBox="0 -146.13 500.612 500.612" xmlns="http://www.w3.org/2000/svg" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M83.743 168.876c-4.007-1.375-6.746-3.24-10.09-6.863-7.024-7.611-7.41-9.883-7.41-43.682 0-32.567.5-35.634 7.044-43.281 9.175-10.718 30.39-10.401 39.45.589 6.017 7.3 6.506 10.55 6.506 43.192 0 25.834-.224 30.14-1.8 34.66-2.416 6.922-9.535 13.619-16.758 15.764-6.812 2.023-10.167 1.949-16.942-.38zm12.455-15.666c4.09-1.57 4.545-5.006 4.545-34.282 0-18.682-.376-28.828-1.13-30.482-2.53-5.554-11.21-5.554-13.74 0-.754 1.654-1.13 11.8-1.13 30.482 0 32.665.417 34.56 7.668 34.825 1.193.043 2.897-.202 3.787-.543zm44.427 15.118c-1.44-.782-3.466-3.128-4.5-5.21-1.745-3.512-1.903-7.104-2.179-49.537l-.297-45.75h19.094v41.877c0 35.843.214 42.057 1.487 43.112 2.216 1.839 5.816.493 9.887-3.697l3.626-3.733V67.832h19v101h-19v-10.17l-4.75 4.217c-2.612 2.319-6.198 4.832-7.968 5.585-4.126 1.753-11.043 1.687-14.4-.136zM24.73 141.08l-.015-27.75-12.357-39.5L.001 34.33l10.04-.287c5.877-.168 10.293.124 10.651.704.337.545 3.524 12.035 7.082 25.533 3.56 13.498 6.698 24.544 6.977 24.546.28.002 2.902-9.108 5.828-20.246 2.927-11.137 5.992-22.612 6.813-25.5l1.493-5.25h10.536c8.584 0 10.438.258 10.003 1.39-.293.764-5.967 18.745-12.607 39.957l-12.073 38.567v55.086h-20l-.014-27.75z" fill="#010101"></path><path d="M284.873 207.783c-48.855-1.631-62.084-5.108-71.078-18.688-3.634-5.486-7.713-17.764-9.012-27.128-4.56-32.866-3.44-101.4 2.041-125.021 4.964-21.391 16.637-31.87 37.931-34.053C265.673.748 320.203-.42 373.243.14c57.262.604 84.221 1.829 93.975 4.27 19.08 4.773 28.336 18.828 31.563 47.92.61 5.5 1.36 24.702 1.666 42.67 1.234 72.535-4.223 95.61-25.02 105.799-7.853 3.848-12.99 4.732-35.185 6.057-24.106 1.438-122.48 2.025-155.369.927zm24.034-39.536c1.686-.873 5.038-3.404 7.45-5.63l4.386-4.04v10.254h19v-100h-19V145.095l-4.368 4.367c-4.688 4.689-6.584 5.274-9.06 2.798-1.378-1.378-1.572-6.626-1.572-42.5V68.83h-19v43.319c0 47.787.393 51.568 5.768 55.58 3.403 2.539 11.964 2.809 16.396.518zm91.45-.323c1.745-1.064 4.163-4.03 5.5-6.746 2.346-4.764 2.393-5.42 2.722-37.828.36-35.532-.212-41.948-4.386-49.15-2.319-4.002-7.849-7.37-12.104-7.37-4.098 0-9.97 2.757-14.447 6.782l-4.898 4.403V34.83h-18v134h18v-9.232l4.105 3.709c2.258 2.039 5.521 4.324 7.25 5.076 4.643 2.022 12.557 1.798 16.258-.46zm-23.864-16.312l-3.75-2.174v-61.33l4.438-2.354c3.601-1.91 4.968-2.167 7.25-1.366 4.931 1.732 5.462 5.552 5.12 36.78l-.308 27.838-2.806 2.412c-3.435 2.954-5.123 2.987-9.944.194zm84.25 16.135c9.664-4.381 14.016-11.79 14.777-25.158l.5-8.758h-19.278v5.936c0 7.27-1.127 10.446-4.487 12.648-3.787 2.48-8.494.904-10.76-3.605-1.369-2.721-1.75-6.037-1.75-15.23l-.003-11.75h36v-14.683c0-18.48-1.445-24.37-7.676-31.3-5.506-6.123-11.405-8.561-20.324-8.397-7.393.135-12.333 1.978-17.522 6.534-8.48 7.447-9.766 14.082-9.259 47.847.33 21.939.693 27.284 2.117 31.057 2.432 6.442 6.825 11.347 12.858 14.354 6.8 3.386 17.95 3.614 24.807.505zm-21-68.45c0-12.438 3.191-16.682 11.221-14.918 4.031.886 5.78 5.398 5.78 14.919v7.532h-17v-7.532zm-172 12.034v-57.5h22v-19h-63v19h21v115h20v-57.5z" fill="#d02726"></path></g></svg>'''
    
    # Private helper methods
    
    def _load_whisper_model(self):
        """Load the Whisper model for transcription."""
        if self.whisper_model is None:
            self._log_info(f"Loading Whisper model ({self.whisper_model_size})...")
            self.whisper_model = whisper.load_model(self.whisper_model_size)
        return self.whisper_model
    
    def _download_audio(self, video_url: str, download_path: str) -> Optional[str]:
        """Download the audio stream of a YouTube video using yt-dlp."""
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(download_path, '%(id)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': self.audio_quality,
            }],
            'quiet': True,
            'no_warnings': True,
            'retries': self.max_retries,
        }
        
        for attempt in range(self.max_retries):
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video_url, download=True)
                    self._log_info(f"Downloaded video: {info_dict.get('title', 'Unknown Title')}")
                
                # Find the mp3 file
                mp3_files = glob.glob(os.path.join(download_path, "*.mp3"))
                if mp3_files:
                    audio_file = mp3_files[0]
                    self._log_info(f"Found audio file: {audio_file}")
                    return audio_file
                else:
                    self._log_error("No MP3 file was found after download.")
                    return None
                    
            except Exception as e:
                self._log_error(f"Attempt {attempt + 1} - Error downloading {video_url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(3)
                else:
                    return None
    
    def _convert_to_mono_wav(self, mp3_path: str, output_path: str) -> Optional[str]:
        """Convert an MP3 file to a mono WAV file."""
        try:
            audio = AudioSegment.from_mp3(mp3_path)
            audio = audio.set_channels(1)  # Convert to mono
            audio.export(output_path, format="wav")
            self._log_info(f"Converted {mp3_path} to mono WAV at {output_path}.")
            return output_path
        except Exception as e:
            self._log_error(f"Error converting {mp3_path} to WAV: {e}")
            return None
    
    def _transcribe_audio(self, audio_path: str, model) -> tuple[str, str]:
        """Transcribe audio to text using Whisper."""
        try:
            result = model.transcribe(audio_path)
            transcript = result.get('text', "")
            language = result.get('language', "unknown")
            self._log_info(f"Transcribed audio file {audio_path} with detected language: {language}.")
            return transcript, language
        except Exception as e:
            self._log_error(f"Error transcribing {audio_path}: {e}")
            return "", "unknown"
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize the video title to create a valid filename."""
        name = name.replace(' ', '_')
        name = re.sub(r'[^\w\-]', '', name)
        return name[:50]  # Limit length
    
    def _test_youtube_connection(self) -> bool:
        """Test if YouTube service is accessible."""
        try:
            # Test with a known, stable YouTube video (Rick Astley - Never Gonna Give You Up)
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            with YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
                info_dict = ydl.extract_info(test_url, download=False)
                # If we can extract basic info, the connection is working
                return info_dict is not None and 'title' in info_dict
        except Exception as e:
            self._log_warning(f"YouTube connection test failed: {e}")
            return False

    def _check_script_availability(self) -> Dict[str, bool]:
        """
        Check which YouTube processing scripts are available in the current directory.
        
        Returns:
            Dict mapping script names to their availability status
        """
        scripts = [
            'youtube_download_audio.py',
            'youtube_extractor_english.py', 
            'youtube_extractor_spanish.py',
            'youtube_text_extract.py',
            'youtube_text_extract_improved.py',
            'youtube_to_context.py',
            'youtube_bodylanguage_extractor.py',
            'youtube_bodylanguage_extractor_1.py',
            'youtube_summary.py',
            'youtube_batch_interviews.py',
            'process_youtube_batch.py',
            'clean_youtube_links.py',
            'convert_live_to_video_urls.py'
        ]
        
        import os
        script_status = {}
        for script in scripts:
            script_status[script] = os.path.exists(script)
        
        return script_status

    def _check_dependencies_status(self) -> Dict[str, bool]:
        """
        Check the availability of key dependencies for YouTube processing.
        
        Returns:
            Dict mapping dependency names to their availability status
        """
        dependencies_status = {}
        
        # Check Python packages
        try:
            import yt_dlp
            dependencies_status['yt-dlp'] = True
        except ImportError:
            dependencies_status['yt-dlp'] = False
            
        try:
            import whisper
            dependencies_status['openai-whisper'] = True
        except ImportError:
            dependencies_status['openai-whisper'] = False
            
        try:
            import cv2
            dependencies_status['opencv-python'] = True
        except ImportError:
            dependencies_status['opencv-python'] = False
            
        try:
            import mediapipe  # type: ignore[import]
            dependencies_status['mediapipe'] = True
        except ImportError:
            dependencies_status['mediapipe'] = False
            
        try:
            from pydub import AudioSegment
            dependencies_status['pydub'] = True
        except ImportError:
            dependencies_status['pydub'] = False
            
        try:
            import ffmpeg
            dependencies_status['ffmpeg-python'] = True
        except ImportError:
            dependencies_status['ffmpeg-python'] = False
            
        # Check system dependencies
        import subprocess
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True, timeout=5)
            dependencies_status['ffmpeg-system'] = True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            dependencies_status['ffmpeg-system'] = False
            
        return dependencies_status

    def process_connection_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the data submitted from the connection form and route to appropriate functionality.
        
        Args:
            form_data: Dictionary containing the user's form selections and input data
            
        Returns:
            Dict containing the processing results and metadata
        """
        try:
            input_type = form_data.get('input_type')
            processing_mode = form_data.get('processing_mode')
            input_data = form_data.get('input_data')
            
            # Validate required fields
            if not all([input_type, processing_mode, input_data]):
                raise ValueError("Missing required form fields: input_type, processing_mode, or input_data")
            
            self._log_info(f"Processing form data - Input Type: {input_type}, Mode: {processing_mode}")
            
            # Route to appropriate processing method based on input type and processing mode
            if input_type == 'single_url':
                return self._process_single_url(input_data, processing_mode, form_data)
            elif input_type == 'url_list_file':
                return self._process_url_list_file(input_data, processing_mode, form_data)
            elif input_type == 'search_query':
                return self._process_search_query(input_data, processing_mode, form_data)
            elif input_type == 'hardcoded_list':
                return self._process_hardcoded_list(processing_mode, form_data)
            else:
                raise ValueError(f"Unsupported input type: {input_type}")
                
        except Exception as e:
            self._log_error(f"Error processing connection form data: {e}")
            return {
                'success': False,
                'error': str(e),
                'form_data': form_data
            }

    def _process_single_url(self, url: str, processing_mode: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single YouTube URL based on the selected processing mode."""
        try:
            # Validate URL first
            if not self.validate_input(url):
                raise ValueError(f"Invalid YouTube URL: {url}")
            
            if processing_mode == 'custom_class':
                # Use the class's built-in processing
                metadata = self.extract_metadata(url)
                processed_data = self.process_source(url)
                return {
                    'success': True,
                    'processing_mode': processing_mode,
                    'script_used': 'SubjectiveYouTubeDataSource.py',
                    'metadata': metadata,
                    'processed_data': processed_data,
                    'output_info': 'Processed using SubjectiveYouTubeDataSource class methods'
                }
            else:
                # Route to external script
                script_mapping = {
                    'audio_only': 'youtube_download_audio.py',
                    'transcription_english': 'youtube_extractor_english.py',
                    'transcription_spanish': 'youtube_extractor_spanish.py',
                    'transcription_auto': 'youtube_text_extract.py',
                    'transcription_improved': 'youtube_text_extract_improved.py',
                    'context_generation': 'youtube_to_context.py',
                    'body_language': 'youtube_bodylanguage_extractor.py',
                    'body_language_live': 'youtube_bodylanguage_extractor_1.py'
                }
                
                script_name = script_mapping.get(processing_mode)
                if not script_name:
                    raise ValueError(f"Unsupported processing mode for single URL: {processing_mode}")
                
                return self._execute_external_script(script_name, url, form_data)
                
        except Exception as e:
            self._log_error(f"Error processing single URL {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'processing_mode': processing_mode
            }

    def _process_url_list_file(self, file_path: str, processing_mode: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a file containing multiple YouTube URLs."""
        try:
            import os
            if not os.path.exists(file_path):
                raise ValueError(f"URL list file not found: {file_path}")
            
            if processing_mode == 'custom_class':
                # Use the class's batch processing
                with open(file_path, 'r') as f:
                    urls = [line.strip() for line in f if line.strip()]
                
                results = self.process_batch(urls, **form_data.get('batch_options', {}))
                return {
                    'success': True,
                    'processing_mode': processing_mode,
                    'script_used': 'SubjectiveYouTubeDataSource.py',
                    'batch_results': results,
                    'total_processed': len(results),
                    'output_info': 'Processed using SubjectiveYouTubeDataSource batch processing'
                }
            elif processing_mode == 'context_generation':
                # Use the batch processing script
                return self._execute_external_script('process_youtube_batch.py', file_path, form_data)
            else:
                raise ValueError(f"Unsupported processing mode for batch processing: {processing_mode}")
                
        except Exception as e:
            self._log_error(f"Error processing URL list file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'processing_mode': processing_mode
            }

    def _process_search_query(self, query: str, processing_mode: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a YouTube search query."""
        try:
            if processing_mode == 'search_summary':
                return self._execute_external_script('youtube_summary.py', query, form_data)
            else:
                raise ValueError(f"Unsupported processing mode for search query: {processing_mode}")
                
        except Exception as e:
            self._log_error(f"Error processing search query '{query}': {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'processing_mode': processing_mode
            }

    def _process_hardcoded_list(self, processing_mode: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a hardcoded list of URLs (typically interviews)."""
        try:
            if processing_mode == 'transcription_dual':
                return self._execute_external_script('youtube_batch_interviews.py', None, form_data)
            else:
                raise ValueError(f"Unsupported processing mode for hardcoded list: {processing_mode}")
                
        except Exception as e:
            self._log_error(f"Error processing hardcoded list: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_mode': processing_mode
            }

    def _execute_external_script(self, script_name: str, input_data: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an external YouTube processing script.
        
        Note: This is a placeholder implementation. In a real system, you would:
        1. Import and execute the script as a module
        2. Use subprocess to run the script
        3. Create a unified interface for all scripts
        """
        import os
        
        if not os.path.exists(script_name):
            return {
                'success': False,
                'error': f"Script not found: {script_name}",
                'script_name': script_name
            }
        
        # For now, return a placeholder response indicating the script would be executed
        return {
            'success': True,
            'processing_mode': form_data.get('processing_mode'),
            'script_used': script_name,
            'input_data': input_data,
            'form_options': form_data,
            'output_info': f"Would execute {script_name} with input: {input_data}",
            'note': 'This is a placeholder - actual script execution would happen here'
        }


# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    config = {
        'whisper_model_size': 'base',
        'max_retries': 3,
        'audio_quality': '192'
    }
    
    # Initialize the data source
    youtube_source = SubjectiveYouTubeDataSource(config)
    
    # Example YouTube URL (replace with actual URL for testing)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        # Validate URL
        if youtube_source.validate_input(test_url):
            print(f"✅ URL is valid: {test_url}")
            
            # Extract metadata only
            metadata = youtube_source.extract_metadata(test_url)
            print(f"📋 Video title: {metadata.get('title', 'Unknown')}")
            print(f"👤 Channel: {metadata.get('uploader', 'Unknown')}")
            print(f"⏱️ Duration: {metadata.get('duration', 0)} seconds")
            
            # For full processing, uncomment the following:
            # processed_data = youtube_source.process_source(test_url)
            # print(f"✅ Successfully processed video")
            
        else:
            print(f"❌ Invalid YouTube URL: {test_url}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up resources
        youtube_source.cleanup()
        
        # Print processing statistics
        stats = youtube_source.get_processing_stats()
        print(f"\n📊 Processing Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
