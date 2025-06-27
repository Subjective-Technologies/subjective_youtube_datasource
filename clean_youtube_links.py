#!/usr/bin/env python3
"""
Clean YouTube links file by removing problematic links
"""

import sys
from yt_dlp import YoutubeDL
import time

def test_youtube_link(url):
    """Test if a YouTube link is accessible."""
    try:
        with YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            return True, info_dict.get('title', 'Unknown')
    except Exception as e:
        error_msg = str(e)
        if "This live event will begin in a few moments" in error_msg:
            return False, "Future live event"
        elif "Private video" in error_msg:
            return False, "Private video"
        elif "Video unavailable" in error_msg:
            return False, "Video unavailable"
        else:
            return False, f"Error: {error_msg[:100]}"

def clean_youtube_links(input_file, output_file):
    """Clean YouTube links file by removing problematic links."""
    
    # Read all links
    with open(input_file, 'r', encoding='utf-8') as f:
        all_links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"🔍 Testing {len(all_links)} YouTube links...")
    print("=" * 60)
    
    valid_links = []
    invalid_links = []
    
    for i, link in enumerate(all_links, 1):
        print(f"[{i}/{len(all_links)}] Testing: {link}")
        
        is_valid, reason = test_youtube_link(link)
        
        if is_valid:
            valid_links.append(link)
            print(f"✅ Valid: {reason}")
        else:
            invalid_links.append((link, reason))
            print(f"❌ Invalid: {reason}")
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS:")
    print(f"✅ Valid links: {len(valid_links)}")
    print(f"❌ Invalid links: {len(invalid_links)}")
    print("=" * 60)
    
    if invalid_links:
        print("\n❌ Invalid links found:")
        for link, reason in invalid_links:
            print(f"  • {link} - {reason}")
    
    if valid_links:
        # Save valid links to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Clean YouTube links (tested and verified)\n")
            f.write(f"# Generated from {input_file}\n")
            f.write(f"# Valid links: {len(valid_links)}/{len(all_links)}\n\n")
            for link in valid_links:
                f.write(f"{link}\n")
        
        print(f"\n✅ Saved {len(valid_links)} valid links to: {output_file}")
        return True
    else:
        print("\n💥 No valid links found!")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 clean_youtube_links.py <input_file> <output_file>")
        print("Example: python3 clean_youtube_links.py youtube_list_of_links.txt youtube_links_clean.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        success = clean_youtube_links(input_file, output_file)
        if success:
            print(f"\n🎉 Use the clean file with:")
            print(f"python3 process_youtube_batch.py {output_file} --interactive")
        else:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 