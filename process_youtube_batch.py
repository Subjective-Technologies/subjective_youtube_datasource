#!/usr/bin/env python3
"""
Batch process YouTube links with error handling and resume capability
"""

import sys
import time
import argparse
from youtube_to_context import YouTubeToContextProcessor

try:
    from alive_progress import alive_bar
    ALIVE_BAR_AVAILABLE = True
except ImportError:
    ALIVE_BAR_AVAILABLE = False

def process_batch_with_progress(unique_links, batch_start, batch_size, processor, progress_bar):
    """Process a batch of links with progress bar updates."""
    batch_end = min(batch_start + batch_size, len(unique_links))
    batch_links = unique_links[batch_start:batch_end]
    
    batch_successful = 0
    batch_failed = 0
    
    for i, link in enumerate(batch_links):
        link_index = batch_start + i + 1
        progress_bar.text(f"Processing {link_index}/{len(unique_links)}: {link[:50]}...")
        
        try:
            if processor.process_youtube_video(link):
                batch_successful += 1
            else:
                batch_failed += 1
        except KeyboardInterrupt:
            raise  # Re-raise to handle in main function
        except Exception as e:
            batch_failed += 1
        
        progress_bar()  # Update progress bar
        
        # Small delay between videos (reduced for progress bar mode)
        if i < len(batch_links) - 1:
            time.sleep(1)
    
    # Longer pause between batches (reduced for progress bar mode)
    if batch_end < len(unique_links):
        time.sleep(3)
    
    return batch_successful, batch_failed

def process_youtube_batch(links_file, start_index=0, batch_size=10, interactive=False):
    """Process YouTube links in batches with resume capability."""
    
    # Read all links
    with open(links_file, 'r', encoding='utf-8') as f:
        all_links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in all_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    print(f"🚀 YOUTUBE BATCH PROCESSOR")
    print(f"=" * 50)
    print(f"📁 Links file: {links_file}")
    print(f"🔗 Total unique links: {len(unique_links)}")
    print(f"📦 Batch size: {batch_size}")
    print(f"🎯 Starting from index: {start_index}")
    if interactive:
        if ALIVE_BAR_AVAILABLE:
            print(f"📊 Interactive mode: Progress bar enabled")
        else:
            print(f"⚠️  Interactive mode: alive_progress not available, install with: pip install alive-progress")
    print(f"=" * 50)
    
    processor = YouTubeToContextProcessor()
    
    total_successful = 0
    total_failed = 0
    
    # Calculate total videos to process
    total_videos = len(unique_links) - start_index
    
    # Process in batches with optional progress bar
    if interactive and ALIVE_BAR_AVAILABLE:
        with alive_bar(total_videos, title="Processing YouTube videos", bar="filling") as bar:
            try:
                for batch_start in range(start_index, len(unique_links), batch_size):
                    batch_successful, batch_failed = process_batch_with_progress(
                        unique_links, batch_start, batch_size, processor, bar
                    )
                    total_successful += batch_successful
                    total_failed += batch_failed
            except KeyboardInterrupt:
                print(f"\n⏹️  Processing interrupted by user")
                current_index = start_index + total_successful + total_failed
                print(f"📊 Resume with: python3 process_youtube_batch.py {links_file} {current_index}")
                return total_successful, total_failed
    else:
        # Original batch processing without progress bar
        for batch_start in range(start_index, len(unique_links), batch_size):
            batch_end = min(batch_start + batch_size, len(unique_links))
            batch_links = unique_links[batch_start:batch_end]
            
            print(f"\n📦 BATCH {(batch_start//batch_size)+1}: Processing links {batch_start+1}-{batch_end}")
            print(f"=" * 40)
            
            batch_successful = 0
            batch_failed = 0
            
            for i, link in enumerate(batch_links):
                link_index = batch_start + i + 1
                print(f"\n[{link_index}/{len(unique_links)}] Processing: {link}")
                
                try:
                    if processor.process_youtube_video(link):
                        batch_successful += 1
                        total_successful += 1
                        print(f"✅ Success!")
                    else:
                        batch_failed += 1
                        total_failed += 1
                        print(f"❌ Failed!")
                except KeyboardInterrupt:
                    print(f"\n⏹️  Processing interrupted by user")
                    print(f"📊 Resume with: python3 process_youtube_batch.py {links_file} {link_index}")
                    return total_successful, total_failed
                except Exception as e:
                    batch_failed += 1
                    total_failed += 1
                    print(f"❌ Error: {e}")
                
                # Small delay between videos
                if i < len(batch_links) - 1:
                    print("⏳ Waiting 3 seconds...")
                    time.sleep(3)
            
            # Batch summary
            print(f"\n📊 Batch {(batch_start//batch_size)+1} Summary:")
            print(f"✅ Successful: {batch_successful}")
            print(f"❌ Failed: {batch_failed}")
            print(f"📈 Batch success rate: {(batch_successful/(batch_successful+batch_failed)*100):.1f}%")
            
            # Longer pause between batches
            if batch_end < len(unique_links):
                print(f"⏳ Pausing 10 seconds before next batch...")
                time.sleep(10)
    
    # Final summary
    print(f"\n" + "=" * 50)
    print(f"🏁 FINAL SUMMARY")
    print(f"=" * 50)
    print(f"✅ Total successful: {total_successful}")
    print(f"❌ Total failed: {total_failed}")
    print(f"📈 Overall success rate: {(total_successful/(total_successful+total_failed)*100):.1f}%")
    
    if total_successful > 0:
        print(f"\n💡 Next steps:")
        print(f"• Check context/ folder for {total_successful} new context files")
        print(f"• context.txt has been automatically updated")
        print(f"• Upload updated context.txt to ChatGPT!")
    
    return total_successful, total_failed

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Batch process YouTube links with error handling and resume capability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 process_youtube_batch.py youtube_list_of_links.txt
  python3 process_youtube_batch.py youtube_list_of_links.txt --start-index 10 --batch-size 5
  python3 process_youtube_batch.py youtube_list_of_links.txt --interactive
  python3 process_youtube_batch.py youtube_list_of_links.txt --start-index 0 --batch-size 20 --interactive
        """
    )
    
    parser.add_argument('links_file', help='YouTube links file to process')
    parser.add_argument('--start-index', type=int, default=0, 
                       help='Index to start processing from (default: 0)')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Number of videos to process in each batch (default: 10)')
    parser.add_argument('--interactive', action='store_true',
                       help='Enable interactive mode with progress bar')
    
    # Support legacy positional arguments for backwards compatibility
    if len(sys.argv) >= 2 and not sys.argv[1].startswith('-'):
        # Check if using old format
        if not any(arg.startswith('--') for arg in sys.argv[1:]):
            # Old format: script.py file [start_index] [batch_size]
            if len(sys.argv) < 2:
                parser.print_help()
                sys.exit(1)
            
            links_file = sys.argv[1]
            start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
            batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            interactive = False
        else:
            args = parser.parse_args()
            links_file = args.links_file
            start_index = args.start_index
            batch_size = args.batch_size
            interactive = args.interactive
    else:
        args = parser.parse_args()
        links_file = args.links_file
        start_index = args.start_index
        batch_size = args.batch_size
        interactive = args.interactive
    
    try:
        successful, failed = process_youtube_batch(links_file, start_index, batch_size, interactive)
        
        if successful > 0:
            print(f"\n🎉 Processing completed with {successful} successful transcriptions!")
        else:
            print(f"\n💥 No successful transcriptions. Check the links and try again.")
            sys.exit(1)
            
    except FileNotFoundError:
        print(f"❌ Error: File '{links_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 