import os
import re
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

app = Flask(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def detect_platform_and_id(url):
    """Detect platform (YouTube, TikTok, Instagram) and extract content ID/link."""
    if not url:
        return None, None
    
    yt_patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/shorts\/([0-9A-Za-z_-]{11})"
    ]
    for pattern in yt_patterns:
        match = re.search(pattern, url)
        if match:
            return "YouTube", match.group(1)
            
    if "tiktok.com" in url.lower():
        return "TikTok", url
        
    if "instagram.com" in url.lower():
        return "Instagram", url

    return "General Video Link", url

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    video_url = data.get("url", "").strip()
    language = data.get("language", "English")

    if not video_url:
        return jsonify({"error": "Please provide a valid video URL"}), 400

    platform, identifier = detect_platform_and_id(video_url)

    full_transcript = f"Platform: {platform} | Content Source: {identifier}"

    if platform == "YouTube":
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(identifier)
            fetched_text = " ".join([item['text'] for item in transcript_list])[:10000]
            if fetched_text:
                full_transcript += f"\nVideo Transcript: {fetched_text}"
        except Exception:
            full_transcript += "\n(Direct transcript unavailable, analyzing video context based on link structure)."

    try:
        if not GEMINI_API_KEY:
            return jsonify({"error": "Gemini API Key is missing in Vercel settings!"}), 500

        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are a top-tier viral content strategist specializing in YouTube Shorts, TikTok, and Instagram Reels.
        Analyze or construct a viral content blueprint for this link/content:
        {full_transcript}

        IMPORTANT: Output ALL the content, scripts, hooks, summaries, and captions in **{language}** language.
        If language is Urdu, write in clean Urdu (Roman Urdu or Urdu script).

        Provide 3 viral Short Clip ideas with:
        1. **Clip Title & Topic**
        2. **Estimated Timestamp / Duration**
        3. **Viral Hook** (First 3-5 seconds dialogue/visual to stop the scroll)
        4. **Short Script / Core Summary**
        5. **Viral Captions with Trending Hashtags** (For TikTok, Reels, & Shorts)

        Format cleanly in Markdown with emojis.
        """

        response = model.generate_content(prompt)
        return jsonify({"result": response.text})

    except Exception as e:
        return jsonify({"error": f"AI Processing Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
    
