from flask import Flask, render_template, request, send_file
import os, requests
from moviepy.editor import VideoFileClip, AudioFileClip
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file uploaded", 400
    file = request.files["file"]
    file.save("input.mp4")

    # Step 1: Transcribe with Whisper
    with open("input.mp4", "rb") as f:
        transcript = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            files={"file": f},
            data={"model": "whisper-1"}
        ).json()
    text = transcript.get("text", "")

    # Step 2: Generate audio with ElevenLabs
    audio_out = "voice.mp3"
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}",
        headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
        json={"text": text, "voice_settings": {"stability": 0.3, "similarity_boost": 0.8}}
    )
    with open(audio_out, "wb") as f:
        f.write(resp.content)

    # Step 3: Merge
    video = VideoFileClip("input.mp4")
    narration = AudioFileClip(audio_out)
    final = video.set_audio(narration)
    out_file = "output.mp4"
    final.write_videofile(out_file, codec="libx264", audio_codec="aac")

    return send_file(out_file, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
