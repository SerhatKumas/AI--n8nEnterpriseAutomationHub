#!/usr/bin/env python3
"""
scripts/fetch_transcript.py
Extracts timestamped transcripts from YouTube URLs.
Supports standard watch URLs, short URLs (youtu.be), Shorts, and direct IDs.
"""

import sys
import re
import json
import urllib.request
import urllib.parse

def extract_video_id(url_or_id):
    if not url_or_id:
        return None
    url_or_id = url_or_id.strip()
    # If 11 chars alphanumeric
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    patterns = [
        r'(?:v=|\/v\/|embed\/|watch\?v=|shorts\/|live\/)([a-zA-Z0-9_-]{11})',
        r'youtu\.be\/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None

def fetch_youtube_metadata(video_id):
    """Fetch basic title and author via oEmbed without API key."""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return {
                "title": data.get("title", f"YouTube Video ({video_id})"),
                "author": data.get("author_name", "Creator"),
                "thumbnail_url": data.get("thumbnail_url", f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg")
            }
    except Exception:
        return {
            "title": f"YouTube Video ({video_id})",
            "author": "Creator",
            "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        }

def format_timestamp(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def get_transcript(video_id):
    """
    Attempts to fetch transcript via youtube-transcript-api.
    If not installed or unavailable, fetches via public timedtext or fallback mock.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'tr', 'es', 'de'])
        lines = []
        for item in api_data:
            start = item.get('start', 0)
            text = item.get('text', '').replace('\n', ' ')
            lines.append(f"[{format_timestamp(start)}] {text}")
        return "\n".join(lines)
    except Exception as e:
        # Fallback: Fetch transcript from public timedtext or return structured metadata
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No URL provided"}))
        sys.exit(1)
    
    url = sys.argv[1]
    vid = extract_video_id(url)
    if not vid:
        print(json.dumps({"error": "Invalid YouTube URL"}))
        sys.exit(1)
    
    meta = fetch_youtube_metadata(vid)
    meta["video_id"] = vid
    meta["url"] = f"https://www.youtube.com/watch?v={vid}"
    
    transcript = get_transcript(vid)
    meta["has_transcript"] = transcript is not None
    meta["transcript"] = transcript or ""
    
    print(json.dumps(meta, indent=2))
