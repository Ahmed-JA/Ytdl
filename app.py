import os, requests, json, threading, time, gc, urllib.parse
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp
from datetime import timedelta

app = Flask(__name__)

# --- 🔑 الإعدادات ---
SITE_PASSWORD = "1234" 
UPLOAD_FOLDER_NAME = "/للرفع فقط"

def get_engines():
    return {
        "AK-A": {"id": "84031qa6rhfihqe", "secret": "pyoh81kjttomk7b", "ref": "3rGVqjd0T1IAAAAAAAAAAYsivkeMJpEjqt2jPzNFM_Y3ETQBojCGeXadZIMjyFg8"},
        "AK1": {"id": "9d4qz7zbqursfqv", "secret": "m26mrjxgbf8yk91", "ref": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"}
    }

RAW_COOKIES = """GPS=1;VISITOR_INFO1_LIVE=20zT46tInss;""" # ضع كوكيزك الكاملة هنا

job_stats = {"active": False, "log": "جاهز", "current_file": "-", "total_done": 0, "total_count": 0, "skipped": 0, "start_time": 0, "eta": "00:00:00", "elapsed": "00:00:00"}

# --- 🛠️ الدوال المساعدة ---
def get_live_token(engine_name="AK1"):
    e = get_engines().get(engine_name)
    if not e: return None
    try:
        data = {"grant_type": "refresh_token", "refresh_token": e["ref"], "client_id": e["id"], "client_secret": e["secret"]}
        res = requests.post("https://api.dropboxapi.com/oauth2/token", data=data, timeout=15)
        return res.json().get("access_token")
    except: return None

# --- 🛰️ منطق يوتيوب ---
def youtube_worker(url, folder_name, mode, quality, sort_by, engine_name):
    global job_stats
    job_stats.update({"active": True, "log": "🔍 تحليل القناة...", "total_done": 0, "skipped": 0, "start_time": time.time()})
    try:
        token = get_live_token(engine_name)
        ydl_opts = {'quiet': True, 'extract_flat': True, 'ignoreerrors': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url, download=False)
            videos = [v for v in res.get('entries', [res]) if v]
            job_stats["total_count"] = len(videos)

        for i, video in enumerate(videos):
            v_url = video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}"
            v_title = "".join([c for c in video.get('title', 'Video') if c.isalnum() or c in " "]).strip()
            processed = i + 1
            
            tasks = []
            if mode in ["Audio Only", "Both"]: tasks.append(("Audio", "bestaudio/best", "mp3"))
            if mode in ["Videos Only", "Both"]: tasks.append(("Videos", f"best[height<={quality}][ext=mp4]/best", "mp4"))

            for sub, fmt, ext in tasks:
                filename = f"{processed:03d} - {v_title}.{ext}"
                full_path = f"/خاص يوتيوب/{folder_name}/{sub}/{filename}"
                
                # رفع الملف
                with yt_dlp.YoutubeDL({'format': fmt, 'quiet': True}) as ydl_s:
                    info = ydl_s.extract_info(v_url, download=False)
                    with requests.get(info['url'], stream=True, timeout=300) as r:
                        requests.post("https://content.dropboxapi.com/2/files/upload", 
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                                              "Dropbox-API-Arg": json.dumps({"path": full_path, "mode": "overwrite"})}, 
                                     data=r.iter_content(chunk_size=1024*1024))
            job_stats["total_done"] = processed
        job_stats.update({"log": "✅ اكتمل", "active": False})
    except Exception as e:
        job_stats.update({"log": f"⚠️ خطأ: {str(e)[:20]}", "active": False})

# --- 🎨 واجهة HTML المدمجة ---
COMMON_HEAD = """
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    :root { --gold: #d4af37; --bg: #050505; }
    body { background: var(--bg); color: #fff; font-family: 'Cairo', sans-serif; margin: 0; }
    .nav { background: #111; padding: 10px 20px; border-bottom: 2px solid var(--gold); display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 9999; }
    .menu-btn { background: var(--gold); border: none; padding: 8px 15px; border-radius: 8px; font-weight: bold; cursor: pointer; }
    .dropdown { display: none; position: absolute; top: 50px; left: 20px; background: #222; border: 1px solid var(--gold); border-radius: 8px; overflow: hidden; }
    .dropdown a { display: block; color: #fff; padding: 12px 20px; text-decoration: none; border-bottom: 1px solid #333; }
    .dropdown a:hover { background: #333; }
    .show { display: block; }
    input, select, button { border-radius: 10px; }
</style>
<div class="nav">
    <b style="color:var(--gold); font-size:20px;">RADAR GOLD PRO</b>
    <div style="position:relative;">
        <button class="menu-btn" onclick="document.getElementById('myDrop').classList.toggle('show')">القائمة <i class="fas fa-bars"></i></button>
        <div id="myDrop" class="dropdown">
            <a href="/"><i class="fas fa-folder-open"></i> مستعرض الملفات</a>
            <a href="/youtube"><i class="fab fa-youtube"></i> محمل اليوتيوب</a>
        </div>
    </div>
</div>
"""

# --- 🏠 المسارات ---
@app.route('/')
def file_browser():
    # هنا تضع كود واجهة مستعرض الملفات (Radar Gold) التي أرسلتها أنت سابقاً
    # سأضع لك الهيكل ليعمل فوراً
    return render_template_string(COMMON_HEAD + "")

@app.route('/youtube')
def youtube_ui():
    return render_template_string(COMMON_HEAD + "")

# APIs
@app.route('/api/verify')
def verify(): return jsonify({"valid": request.args.get('pass') == SITE_PASSWORD})

@app.route('/api/yt/start', methods=['POST'])
def start_yt():
    d = request.json
    threading.Thread(target=youtube_worker, args=(d['url'], d['folder'], d['mode'], d['quality'], d['sort'], d['engine'])).start()
    return jsonify({"ok": True})

@app.route('/api/yt/status')
def get_yt_status(): return jsonify(job_stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
