#!/usr/bin/env python3
"""
Context Updater Module

This module provides functionality to update context.txt files
with new context JSON files from the context directory.
"""

import os
import json
import glob
from datetime import datetime
from typing import List, Dict, Any


class ContextUpdater:
    """
    Class to handle updating context.txt files with new context data.
    """
    
    def __init__(self, context_dir: str = "context", context_txt_path: str = "context.txt"):
        """
        Initialize the ContextUpdater.
        
        Args:
            context_dir: Directory containing context JSON files
            context_txt_path: Path to the context.txt file to update
        """
        self.context_dir = context_dir
        self.context_txt_path = context_txt_path
        self.processed_files = set()
        
        # Load already processed files if context.txt exists
        self._load_processed_files()
    
    def _load_processed_files(self):
        """Load the list of already processed files from context.txt."""
        if os.path.exists(self.context_txt_path):
            try:
                with open(self.context_txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract context filenames that are already in context.txt
                    # This is a simple implementation - you might want to make it more robust
                    for line in content.split('\n'):
                        if line.startswith('# Context from:'):
                            filename = line.split(':', 1)[1].strip()
                            self.processed_files.add(filename)
            except Exception as e:
                print(f"Warning: Could not read existing context.txt: {e}")
    
    def get_new_context_files(self) -> List[str]:
        """
        Get list of new context JSON files that haven't been processed yet.
        
        Returns:
            List of context JSON file paths
        """
        if not os.path.exists(self.context_dir):
            return []
        
        all_context_files = glob.glob(os.path.join(self.context_dir, "context-*.json"))
        new_files = []
        
        for file_path in all_context_files:
            filename = os.path.basename(file_path)
            if filename not in self.processed_files:
                new_files.append(file_path)
        
        # Sort by modification time (newest first)
        new_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return new_files
    
    def load_context_data(self, context_file_path: str) -> Dict[str, Any]:
        """
        Load context data from a JSON file.
        
        Args:
            context_file_path: Path to the context JSON file
            
        Returns:
            Dictionary containing context data
        """
        try:
            with open(context_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading context file {context_file_path}: {e}")
            return {}
    
    def format_context_entry(self, context_data: Dict[str, Any], context_filename: str) -> str:
        """
        Format a context entry for inclusion in context.txt.
        
        Args:
            context_data: Context data dictionary
            context_filename: Name of the context file
            
        Returns:
            Formatted string for context.txt
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"\n# Context from: {context_filename}\n"
        entry += f"# Added: {timestamp}\n"
        entry += f"# Video: {context_data.get('video_filename', 'Unknown')}\n"
        entry += f"# Source: {context_data.get('video_path', 'Unknown')}\n"
        entry += "-" * 80 + "\n\n"
        
        # Add the transcription content
        transcription = context_data.get('transcription', '')
        if transcription:
            entry += transcription + "\n\n"
        else:
            entry += "No transcription available.\n\n"
        
        entry += "=" * 80 + "\n"
        
        return entry
    
    def update_context_txt(self, new_context_files: List[str]) -> int:
        """
        Update context.txt with new context files.
        
        Args:
            new_context_files: List of new context file paths
            
        Returns:
            Number of files successfully added
        """
        if not new_context_files:
            return 0
        
        added_count = 0
        
        try:
            # Open context.txt in append mode
            with open(self.context_txt_path, 'a', encoding='utf-8') as f:
                for context_file_path in new_context_files:
                    try:
                        context_data = self.load_context_data(context_file_path)
                        if context_data:
                            filename = os.path.basename(context_file_path)
                            formatted_entry = self.format_context_entry(context_data, filename)
                            f.write(formatted_entry)
                            
                            # Mark as processed
                            self.processed_files.add(filename)
                            added_count += 1
                            
                            print(f"✅ Added {filename} to context.txt")
                        else:
                            print(f"⚠️  Skipped {context_file_path} (no data)")
                    except Exception as e:
                        print(f"❌ Error processing {context_file_path}: {e}")
            
            if added_count > 0:
                print(f"📄 Updated context.txt with {added_count} new entries")
            
        except Exception as e:
            print(f"❌ Error updating context.txt: {e}")
            return 0
        
        return added_count
    
    def check_for_new_files(self) -> int:
        """
        Check for new context files and update context.txt if needed.
        
        Returns:
            Number of new files processed
        """
        new_files = self.get_new_context_files()
        if new_files:
            print(f"📁 Found {len(new_files)} new context files")
            return self.update_context_txt(new_files)
        else:
            print("📁 No new context files found")
            return 0
    
    def create_initial_context_txt(self):
        """Create an initial context.txt file with header."""
        if not os.path.exists(self.context_txt_path):
            try:
                with open(self.context_txt_path, 'w', encoding='utf-8') as f:
                    f.write("# BrainBoost Context File\n")
                    f.write("# Generated from YouTube video transcriptions\n")
                    f.write(f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("# This file contains transcriptions and metadata from processed videos\n")
                    f.write("=" * 80 + "\n\n")
                print(f"✅ Created initial context.txt file")
            except Exception as e:
                print(f"❌ Error creating context.txt: {e}")


def main():
    """Main function for standalone usage."""
    updater = ContextUpdater()
    updater.create_initial_context_txt()
    new_count = updater.check_for_new_files()
    
    if new_count > 0:
        print(f"🎉 Successfully processed {new_count} new context files!")
    else:
        print("ℹ️  No new files to process.")


if __name__ == "__main__":
    main() 