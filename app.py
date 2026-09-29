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
    """Extract YouTube Video ID from various URL formats."""
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    video_url = data.get("url")

    if not video_url:
        return jsonify({"error": "Please provide a valid YouTube URL"}), 400

    video_id = extract_video_id(video_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL format"}), 400

    try:
        # Fetch transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_transcript = " ".join([item['text'] for item in transcript_list])
        
        # Limit transcript length if too long
        full_transcript = full_transcript[:10000]

        # Call Gemini AI
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are an expert YouTube Shorts and TikTok content strategist.
        Analyze the following transcript from a video and extract 3 viral Short Clip ideas.

        Transcript:
        {full_transcript}

        For each of the 3 clips, provide:
        1. **Clip Title & Topic**
        2. **Estimated Timestamp Range** (e.g., 01:15 - 02:00)
        3. **Viral Hook** (First 3-5 seconds dialogue to catch attention)
        4. **Short Script / Core Summary**
        5. **TikTok/Reels Caption with Hashtags**

        Format the output cleanly using Markdown with clear headers and bullet points.
        """

        response = model.generate_content(prompt)
        return jsonify({"result": response.text})

    except Exception as e:
        return jsonify({"error": f"Failed to process video: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
  
