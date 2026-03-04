#!/usr/bin/env python3
"""
Convert YouTube live URLs to regular video URLs
Many live streams become regular videos after they finish
"""

import sys
import re

def convert_live_to_video_url(live_url):
    """Convert a YouTube live URL to a regular video URL."""
    # Extract video ID from live URL
    # Format: https://youtube.com/live/VIDEO_ID?feature=share
    match = re.search(r'youtube\.com/live/([a-zA-Z0-9_-]+)', live_url)
    
    if match:
        video_id = match.group(1)
        # Convert to regular YouTube URL
        return f"https://www.youtube.com/watch?v={video_id}"
    else:
        return live_url  # Return unchanged if not a live URL

def convert_youtube_links_file(input_file, output_file):
    """Convert all live URLs in a file to regular video URLs."""
    
    print(f"🔄 Converting YouTube live URLs to video URLs...")
    print(f"📁 Input: {input_file}")
    print(f"📁 Output: {output_file}")
    print("=" * 50)
    
    # Read all links
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    converted_lines = []
    conversion_count = 0
    
    for line in lines:
        line = line.strip()
        
        if line and not line.startswith('#'):
            # Check if it's a live URL
            if 'youtube.com/live/' in line:
                converted_url = convert_live_to_video_url(line)
                converted_lines.append(converted_url + '\n')
                conversion_count += 1
                print(f"🔄 Converted: {line}")
                print(f"   ➡️  To: {converted_url}")
            else:
                converted_lines.append(line + '\n')
                print(f"✅ Kept: {line}")
        else:
            # Keep comments and empty lines
            converted_lines.append(line + '\n')
    
    # Write converted URLs
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Converted YouTube URLs (live URLs changed to video URLs)\n")
        f.write(f"# Converted {conversion_count} live URLs to video URLs\n")
        f.write("# Note: Some videos may still be unavailable if the live stream hasn't finished\n\n")
        f.writelines(converted_lines)
    
    print("\n" + "=" * 50)
    print(f"📊 CONVERSION COMPLETE!")
    print(f"🔄 Converted {conversion_count} live URLs to video URLs")
    print(f"✅ Saved to: {output_file}")
    print("\n💡 Next steps:")
    print(f"1. Test the converted URLs:")
    print(f"   python3 clean_youtube_links.py {output_file} {output_file.replace('.txt', '_clean.txt')}")
    print(f"2. Process the clean URLs:")
    print(f"   python3 process_youtube_batch.py {output_file.replace('.txt', '_clean.txt')} --interactive")

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 convert_live_to_video_urls.py <input_file> <output_file>")
        print("Example: python3 convert_live_to_video_urls.py youtube_list_of_links.txt youtube_video_links.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        convert_youtube_links_file(input_file, output_file)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 