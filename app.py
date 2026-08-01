import os
import re
import json
import streamlit as st
import yt_dlp
from moviepy.editor import VideoFileClip
from google import genai

# --- CONFIG TAMPILAN ---
st.set_page_config(page_title="AI Video Clipper FYP", page_icon="🎬", layout="centered")

st.title("🎬 AI YouTube Clipper to FYP")
st.write("Potong otomatis video YouTube jadi klip FYP siap download!")

# --- SIDEBAR ---
api_key = st.sidebar.text_input("Gemini API Key", type="password")

# --- FUNGSIONALITAS ---
def download_youtube_video(url):
    """Mendownload video YouTube ke server sementara."""
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'input_video.%(ext)s',
        'quiet': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['hls', 'dash']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return info, filename

def time_to_seconds(time_str):
    """Mengubah format MM:SS menjadi detik."""
    parts = list(map(int, time_str.split(':')))
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0

def clip_video(input_path, output_path, start_sec, end_sec):
    """Memotong file video menggunakan MoviePy."""
    with VideoFileClip(input_path) as video:
        new_clip = video.subclip(start_sec, end_sec)
        # Ekspor klip ke MP4
        new_clip.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac", 
            temp_audiofile='temp-audio.m4a', 
            remove_temp=True
        )

# --- FORM UTAMA ---
video_url = st.text_input("🔗 Masukkan Link Video YouTube:")

if st.button("🚀 Potong Video FYP Sekarang"):
    if not api_key:
        st.error("Silakan masukkan Gemini API Key di menu sidebar!")
    elif not video_url:
        st.warning("Masukkan link video YouTube terlebih dahulu!")
    else:
        try:
            client = genai.Client(api_key=api_key)

            # 1. Download Video
            with st.spinner("📥 Memproses & mendownload video..."):
                info, video_file_path = download_youtube_video(video_url)
                title = info.get('title', '')
                description = info.get('description', '')

            # 2. Analisis AI Gemini
            with st.spinner("🧠 Menganalisis momen viral dengan Gemini AI..."):
                prompt = f"""
                Kamu adalah pakar editor konten viral TikTok/Shorts.
                Analisis video ini dan pilih 1 momen paling menarik (durasi 15-60 detik).
                Judul: {title}
                Deskripsi: {description}

                Jawab HANYA dalam format JSON berikut tanpa Markdown lain:
                {{
                  "start_time": "MM:SS",
                  "end_time": "MM:SS",
                  "reason": "Alasan singkat kenapa bakal viral"
                }}
                """
                res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                clean_json = re.sub(r'```json\s*|\s*```', '', res.text).strip()
                data = json.loads(clean_json)

                start_time = data.get("start_time", "00:00")
                end_time = data.get("end_time", "00:30")
                reason = data.get("reason", "Momen terbaik video")

            st.success(f"🎯 Momen Ditemukan! ({start_time} - {end_time})")
            st.info(f"💡 Alasan AI: {reason}")

            # 3. Potong Video Otomatis
            output_clip_path = "output_fyp.mp4"
            with st.spinner("✂️ Memotong video untuk FYP..."):
                start_sec = time_to_seconds(start_time)
                end_sec = time_to_seconds(end_time)

                # Batas aman durasi
                if end_sec <= start_sec or (end_sec - start_sec) > 90:
                    start_sec, end_sec = 0, 30

                clip_video(video_file_path, output_clip_path, start_sec, end_sec)

            # 4. Tampilkan Hasil Video & Tombol Download
            st.write("### 🎬 Hasil Potongan Video FYP:")
            st.video(output_clip_path)

            with open(output_clip_path, "rb") as file:
                st.download_button(
                    label="📥 Download Video FYP (MP4)",
                    data=file,
                    file_name="klip_fyp_viral.mp4",
                    mime="video/mp4"
                )

            # Cleanup file sementara di server
            if os.path.exists(video_file_path):
                os.remove(video_file_path)

        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
