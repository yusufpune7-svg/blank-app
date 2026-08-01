import os
import subprocess
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
import yt_dlp

# Menggunakan nama folder "templates" sesuai lokasi file kamu
app = Flask(__name__, template_folder="templates")
CORS(app)

# ==========================================
# PASSWORD ADMIN KAMU:
ADMIN_SECRET_KEY = "febrisyan0012"
# ==========================================

OUTPUT_DIR = "clips"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process_video():
    data = request.json or {}
    
    # 1. CEK PASSWORD ADMIN
    user_key = data.get("secret_key", "")
    if user_key != ADMIN_SECRET_KEY:
        return jsonify({
            "status": "error", 
            "message": "Akses Ditolak! Fitur ini khusus Admin / Berbayar."
        }), 403

    # 2. PROSES VIDEO JIKA PASSWORD BENAR
    youtube_url = data.get("url")
    start_time = data.get("start_time", 10)
    end_time = data.get("end_time", 40)

    if not youtube_url:
        return jsonify({"status": "error", "message": "URL tidak valid"}), 400

    duration = end_time - start_time
    output_filename = f"clip_{start_time}_{end_time}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'temp_video.mp4',
            'overwrites': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-i', 'temp_video.mp4',
            '-t', str(duration),
            '-c', 'copy',
            output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        if os.path.exists('temp_video.mp4'):
            os.remove('temp_video.mp4')

        return jsonify({
            "status": "success",
            "message": "Video berhasil dipotong!",
            "download_url": f"/download/{output_filename}"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)