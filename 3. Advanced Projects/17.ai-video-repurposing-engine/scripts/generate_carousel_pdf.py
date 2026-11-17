#!/usr/bin/env python3
"""
scripts/generate_carousel_pdf.py
Converts a 10-slide JSON carousel into a clean, modern HTML slide deck.
"""

import sys
import json
import os

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>__TITLE__</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { background: #0f172a; color: #f8fafc; padding: 40px; display: flex; flex-direction: column; align-items: center; gap: 40px; }
  .carousel-header { text-align: center; max-width: 800px; margin-bottom: 20px; }
  .carousel-header h1 { font-size: 28px; color: #38bdf8; margin-bottom: 10px; }
  .carousel-header p { font-size: 16px; color: #94a3b8; }
  .slide-container { display: flex; flex-direction: column; gap: 30px; width: 100%; max-width: 540px; }
  .slide {
    width: 540px;
    height: 675px;
    background: linear-gradient(145deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 40px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    position: relative;
    overflow: hidden;
  }
  .slide-badge { font-size: 14px; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 1.5px; }
  .slide-content { margin: auto 0; }
  .slide-icon { font-size: 48px; margin-bottom: 16px; }
  .slide-headline { font-size: 32px; font-weight: 800; line-height: 1.25; margin-bottom: 16px; color: #ffffff; }
  .slide-sub { font-size: 18px; color: #94a3b8; line-height: 1.5; margin-bottom: 20px; }
  .slide-key { font-size: 16px; color: #38bdf8; background: rgba(56, 189, 248, 0.1); padding: 12px 16px; border-left: 4px solid #38bdf8; border-radius: 4px; }
  .slide-footer { display: flex; justify-content: space-between; align-items: center; font-size: 14px; color: #64748b; border-top: 1px solid #334155; padding-top: 16px; }
  .slide-number { font-weight: 700; color: #94a3b8; }
</style>
</head>
<body>
<div class="carousel-header">
  <h1>__TITLE__</h1>
  <p>10-Slide High-Engagement LinkedIn PDF Carousel</p>
</div>
<div class="slide-container">
__SLIDES_HTML__
</div>
</body>
</html>
"""

def render_slides(carousel_data: dict) -> str:
    title = carousel_data.get("carousel_title", "LinkedIn Carousel Deck")
    slides = carousel_data.get("slides", [])
    total_slides = len(slides)
    
    slides_html = []
    icons = ["💡", "⚠️", "🔍", "⚡", "⚙️", "🛠️", "📈", "🎯", "✨", "🚀"]
    
    for idx, slide in enumerate(slides):
        num = slide.get("slide_number", idx + 1)
        headline = slide.get("headline", "")
        body = slide.get("body", "")
        visual = slide.get("visual_cue", "")
        icon = icons[idx % len(icons)]
        
        slide_block = f"""
  <div class="slide">
    <div class="slide-badge">SLIDE {num:02d} / {total_slides:02d}</div>
    <div class="slide-content">
      <div class="slide-icon">{icon}</div>
      <div class="slide-headline">{headline}</div>
      <div class="slide-sub">{body}</div>
      {f'<div class="slide-key">💡 {visual}</div>' if visual else ''}
    </div>
    <div class="slide-footer">
      <span>AI Engineering & Automation</span>
      <span class="slide-number">Slide {num} of {total_slides}</span>
    </div>
  </div>"""
        slides_html.append(slide_block)
        
    return HTML_TEMPLATE.replace("__TITLE__", title).replace("__SLIDES_HTML__", "\n".join(slides_html))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_carousel_pdf.py <path_to_carousel.json> [output.html]")
        sys.exit(1)
        
    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "carousel_preview.html"
    
    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    html = render_slides(data)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"✅ Generated carousel HTML deck at: {out_path}")
