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

def extract_video_id(url):
    """Extract YouTube Video ID from any URL format."""
    if not url:
        return None
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/shorts\/([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    video_url = data.get("url", "").strip()

    if not video_url:
        return jsonify({"error": "Please provide a YouTube URL"}), 400

    video_id = extract_video_id(video_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL format"}), 400

    full_transcript = ""
    try:
        # Attempt to fetch transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_transcript = " ".join([item['text'] for item in transcript_list])[:10000]
    except Exception:
        # Fallback if transcript fails or is disabled/blocked by YouTube IP rate limits
        full_transcript = f"Video ID: {video_id}. (Direct transcript fetching unavailable. Generate a viral Shorts content structure and script strategy based on this video link)."

    try:
        if not GEMINI_API_KEY:
            return jsonify({"error": "Gemini API Key is missing in Vercel settings!"}), 500

        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are an expert YouTube Shorts and TikTok content strategist.
        Analyze or create a strategy for this video content:
        {full_transcript}

        Provide 3 viral Short Clip ideas with:
        1. **Clip Title & Topic**
        2. **Estimated Timestamp Range** (e.g., 01:15 - 02:00)
        3. **Viral Hook** (First 3-5 seconds dialogue to catch attention)
        4. **Short Script / Core Summary**
        5. **TikTok/Reels Caption with Hashtags**

        Format cleanly in Markdown.
        """

        response = model.generate_content(prompt)
        return jsonify({"result": response.text})

    except Exception as e:
        return jsonify({"error": f"AI Processing Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
    
