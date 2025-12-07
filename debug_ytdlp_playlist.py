import yt_dlp
import json
import logging

logging.basicConfig(level=logging.INFO)

url = "https://www.instagram.com/stories/faridpkk/3782365091497613435?utm_source=ig_story_item_share&igsh=MTJpamQ2d2N6Z3J6aw=="

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True, # Don't download, just list
    'cookiefile': 'cookies.txt'
}

print(f"Checking URL: {url}")
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        print(f"Type: {info.get('_type', 'video')}")
        if 'entries' in info:
            print(f"Entries found: {len(info['entries'])}")
            for i, entry in enumerate(info['entries']):
                print(f"{i+1}: {entry.get('id')} - {entry.get('title')}")
        else:
            print(f"Single video: {info.get('id')} - {info.get('title')}")
            
except Exception as e:
    print(f"Error: {e}")
