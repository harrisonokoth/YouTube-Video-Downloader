from yt_dlp import YoutubeDL
import os
import shutil
from typing import Optional
from urllib.parse import urlparse, parse_qs

def is_playlist_url(url: str) -> bool:
    """Check if the provided URL is a playlist or a single video."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return 'list' in query_params

def clean_filename(filename: str) -> str:
    """Remove invalid characters from filenames."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def download_youtube_content(
    url: str,
    output_path: Optional[str] = None,
    cookie_file: Optional[str] = None,
    max_retries: int = 3
) -> None:
    """
    Enhanced YouTube downloader with better error handling and file management.
    
    Args:
        url: YouTube video or playlist URL
        output_path: Directory to save downloads (default: ./downloads)
        cookie_file: Path to cookies.txt (optional)
        max_retries: Number of retry attempts (default: 3)
    """
    # Set default output path
    if output_path is None:
        output_path = os.path.join(os.getcwd(), 'downloads')
    os.makedirs(output_path, exist_ok=True)

    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'retries': max_retries,
        'fragment_retries': max_retries,
        'ignoreerrors': True,
        'no_warnings': True,
        'writethumbnail': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'postprocessors': [
            {
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            },
            {
                'key': 'FFmpegMetadata',
            }
        ],
        'cookiefile': cookie_file,
        'windowsfilenames': True,  # Automatically sanitize filenames
        'restrictfilenames': True,
        'fixup': 'warn',  # Automatically fix common issues
    }

    # Handle playlists differently
    if is_playlist_url(url):
        ydl_opts['outtmpl'] = os.path.join(output_path, '%(playlist_title)s', '%(playlist_index)s - %(title)s.%(ext)s')
        print("📂 Detected playlist URL. Downloading full playlist...")
    else:
        print("📺 Detected single video URL. Downloading video...")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Extract info first to handle filename conflicts
            info_dict = ydl.extract_info(url, download=False)
            if not info_dict:
                raise ValueError("Could not extract video information")
                
            # Clean and verify the final filename
            if not is_playlist_url(url):
                base_filename = clean_filename(info_dict.get('title', 'video'))
                final_path = os.path.join(output_path, f"{base_filename}.mp4")
                
                # Remove existing files to prevent conflicts
                temp_files = [
                    final_path,
                    final_path.replace('.mp4', '.temp.mp4'),
                    final_path.replace('.mp4', '.f*.mp4'),
                    final_path.replace('.mp4', '.f*.webm'),
                ]
                
                for file_pattern in temp_files:
                    for existing_file in glob.glob(file_pattern):
                        try:
                            os.remove(existing_file)
                        except OSError:
                            pass

            # Start download
            ydl.download([url])
            print(f"\n✅ Download successful! Saved to: {output_path}")

    except Exception as e:
        print(f"\n❌ Download failed: {str(e)}")
        # Clean up potentially corrupted files
        if 'final_path' in locals():
            for file_pattern in [final_path, final_path.replace('.mp4', '.*')]:
                for f in glob.glob(file_pattern):
                    try:
                        os.remove(f)
                    except OSError:
                        pass

if __name__ == "__main__":
    import glob
    
    print("=== YouTube Downloader ===")
    url = input("🔗 Enter YouTube URL (video/playlist): ").strip()
    output_dir = input("📁 Output directory (Enter for default): ").strip() or None
    cookie_path = input("🍪 Cookies file path (Enter to skip): ").strip() or None
    
    download_youtube_content(
        url=url,
        output_path=output_dir,
        cookie_file=cookie_path
    )