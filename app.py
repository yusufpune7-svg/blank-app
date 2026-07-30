import os
import subprocess
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

OUTPUT_DIR = "clips"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process_video():
    data = request.json
    youtube_url = data.get("url")
    start_time = data.get("start_time", 10)
    end_time = data.get("end_time", 40)

    if not youtube_url:
        return jsonify({"status": "error", "message": "URL tidak valid"}), 400

    duration = end_time - start_time
    if duration <= 0:
        return jsonify({"status": "error", "message": "Waktu selesai harus lebih besar dari waktu mulai"}), 400

    temp_file = "temp_input.mp4"
    output_filename = "klip_viral.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    try:
        # 1. Download Video dari YouTube
        ydl_opts = {
            "format": "mp4[height<=720]",
            "outtmpl": temp_file,
            "overwrites": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # 2. Potong Video menggunakan FFmpeg
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-i", temp_file,
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        if os.path.exists(temp_file):
            os.remove(temp_file)

        return jsonify({
            "status": "success",
            "message": "Video berhasil dipotong!",
            "file_url": f"/download/{output_filename}"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
