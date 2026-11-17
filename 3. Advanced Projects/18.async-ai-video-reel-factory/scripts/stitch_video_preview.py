#!/usr/bin/env python3
"""
stitch_video_preview.py - Multi-Track Media Stitching Reference

Builds Shotstack or Creatomate JSON manifests to combine:
1. Video track (AI-generated background clip, cropped to 9:16 vertical)
2. Audio track (ElevenLabs speech synthesis MP3)
3. Subtitle track (Dynamic kinetic subtitles with highlight words)
4. Watermark / Brand Logo overlay
"""

import json
import sys

def build_shotstack_payload(video_url: str, audio_url: str, subtitles_text: str, duration_sec: float = 30.0):
    """
    Generates Shotstack Edit API payload for 9:16 vertical reels.
    """
    payload = {
        "timeline": {
            "soundtrack": {
                "src": audio_url,
                "effect": "fadeInFadeOut"
            },
            "tracks": [
                {
                    # Track 1: Dynamic Subtitles
                    "clips": [
                        {
                            "asset": {
                                "type": "title",
                                "text": subtitles_text,
                                "style": "chunk",
                                "color": "#FFFFFF",
                                "background": "rgba(0, 0, 0, 0.6)",
                                "size": "medium",
                                "position": "middle"
                            },
                            "start": 0,
                            "length": duration_sec
                        }
                    ]
                },
                {
                    # Track 2: Background Video
                    "clips": [
                        {
                            "asset": {
                                "type": "video",
                                "src": video_url,
                                "volume": 0.0 # Mute video native audio
                            },
                            "start": 0,
                            "length": duration_sec,
                            "fit": "cover",
                            "scale": 1.0
                        }
                    ]
                }
            ]
        },
        "output": {
            "format": "mp4",
            "resolution": "1080",
            "aspectRatio": "9:16",
            "fps": 30
        }
    }
    return payload

if __name__ == "__main__":
    v_url = sys.argv[1] if len(sys.argv) > 1 else "https://cdn.example.com/generated_background.mp4"
    a_url = sys.argv[2] if len(sys.argv) > 2 else "https://cdn.example.com/elevenlabs_voiceover.mp3"
    text = sys.argv[3] if len(sys.argv) > 3 else "This AI Agent Works While You Sleep."
    
    manifest = build_shotstack_payload(v_url, a_url, text)
    print(json.dumps(manifest, indent=2))
