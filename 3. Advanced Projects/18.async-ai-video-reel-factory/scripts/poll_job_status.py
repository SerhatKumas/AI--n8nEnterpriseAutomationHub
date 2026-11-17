#!/usr/bin/env python3
"""
poll_job_status.py - Reference Asynchronous Polling Implementation

Demonstrates the resilient polling pattern used by the n8n Asynchronous Video Reel Factory.
Prevents infinite execution loops by enforcing:
- Maximum retry limits (MAX_RETRIES)
- Exponential or fixed sleep intervals (POLL_INTERVAL)
- Explicit terminal state recognition ('succeeded', 'failed', 'canceled')
"""

import sys
import time
import json
import os
import requests

def poll_replicate_prediction(prediction_id: str, api_token: str, max_retries: int = 20, interval_sec: int = 15):
    """
    Polls Replicate / Kling / Luma job status until terminal state or timeout.
    """
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
    
    print(f"🔄 Starting polling for Job ID: {prediction_id}")
    print(f"⚙️ Config: Interval={interval_sec}s, Max Retries={max_retries}")
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ [Attempt {attempt}/{max_retries}] Non-200 HTTP response: {response.status_code}")
                time.sleep(interval_sec)
                continue
                
            data = response.json()
            status = data.get("status")
            print(f"⏳ [Attempt {attempt}/{max_retries}] Current status: {status}")
            
            if status == "succeeded":
                output = data.get("output")
                print(f"✅ Video generation SUCCEEDED!")
                print(f"🎬 Video URL: {output}")
                return {"status": "succeeded", "video_url": output, "attempts": attempt}
                
            elif status in ("failed", "canceled"):
                error_msg = data.get("error", "Unknown failure")
                print(f"❌ Video generation {status.upper()}: {error_msg}")
                return {"status": status, "error": error_msg, "attempts": attempt}
                
            # If still starting or processing, sleep and loop
            time.sleep(interval_sec)
            
        except Exception as e:
            print(f"⚠️ Error during poll attempt {attempt}: {str(e)}")
            time.sleep(interval_sec)
            
    print(f"🚨 Polling timed out after {max_retries * interval_sec} seconds.")
    return {"status": "timeout", "error": "Maximum polling retries exceeded", "attempts": max_retries}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 poll_job_status.py <PREDICTION_ID> [API_TOKEN]")
        print("Running in simulation mode with mock states...")
        
        # Simulated run
        mock_states = ["starting", "processing", "processing", "succeeded"]
        for i, s in enumerate(mock_states):
            print(f"⏳ [Attempt {i+1}/10] Simulated status: {s}")
            time.sleep(1)
            if s == "succeeded":
                print("✅ [Simulation] Job completed successfully! Output: https://cdn.replicate.delivery/mock_video.mp4")
                sys.exit(0)
    else:
        pid = sys.argv[1]
        token = sys.argv[2] if len(sys.argv) > 2 else os.getenv("REPLICATE_API_TOKEN", "")
        result = poll_replicate_prediction(pid, token)
        print(json.dumps(result, indent=2))
