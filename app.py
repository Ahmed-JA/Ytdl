import os, requests, json, threading, time, gc
from flask import Flask, render_template_string, request, jsonify
import yt_dlp
from datetime import timedelta

app = Flask(__name__)

# --- 🔑 قاعدة بيانات المحركات ---
def get_engines():
    return {
        "AK-A": {"id": "84031qa6rhfihqe", "secret": "pyoh81kjttomk7b", "ref": "3rGVqjd0T1IAAAAAAAAAAYsivkeMJpEjqt2jPzNFM_Y3ETQBojCGeXadZIMjyFg8"},
        "AK1": {"id": "9d4qz7zbqursfqv", "secret": "m26mrjxgbf8yk91", "ref": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"}
    }

RAW_COOKIES = """ضع_الكوكيز_هنا"""

# إحصائيات الجلسة الشاملة
job_stats = {
    "active": False, "log": "جاهز", "current_file": "-",
    "total_done": 0, "total_count": 0, "skipped": 0,
    "start_time": 0, "eta": "00:00:00", "elapsed": "00:00:00"
}

def create_cookie_file():
    with open("cookies.txt", "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in RAW_COOKIES.split(';'):
            if '=' in cookie:
                parts = cookie.strip().split('=', 1)
                if len(parts) == 2:
                    f.write(f".youtube.com\tTRUE\t/\tTRUE\t2147483647\t{parts[0]}\t{parts[1]}\n")

def get_token(engine_name):
    e = get_engines()[engine_name]
    try:
        res = requests.post("https://api.dropboxapi.com/oauth2/token", 
                            data={"grant_type": "refresh_token", "refresh_token": e["ref"], "client_id": e["id"], "client_secret": e["secret"]}, timeout=15)
        return res.json().get("access_token")
    except: return None

def check_exists(token, path):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        res = requests.post("https://api.dropboxapi.com/2/files/get_metadata", headers=headers, json={"path": path})
        return res.status_code == 200
    except: return False

def youtube_worker(url, folder_name, mode, quality, sort_by, engine_name):
    global job_stats
    create_cookie_file()
    job_stats.update({"active": True, "log": "🔍 تحليل البيانات...", "total_done": 0, "skipped": 0, "start_time": time.time()})
    
    try:
        ydl_opts = {'cookiefile': 'cookies.txt', 'quiet': True, 'extract_flat': True, 'ignoreerrors': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url, download=False)
            videos = [v for v in res.get('entries', [res]) if v]

            if sort_by == "Most Viewed": videos.sort(key=lambda x: x.get('view_count') or 0, reverse=True)
            elif sort_by == "Newest": videos.sort(key=lambda x: x.get('upload_date') or '', reverse=True)
            elif sort_by == "Oldest": videos.sort(key=lambda x: x.get('upload_date') or '')
            elif sort_by == "Rating": videos.sort(key=lambda x: x.get('like_count') or 0, reverse=True)

            job_stats["total_count"] = len(videos)

        for i, video in enumerate(videos):
            token = get_token(engine_name)
            v_url = video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}"
            v_title = "".join([c for c in video.get('title', 'Video') if c.isalnum() or c in " "]).strip()
            
            # تحديث الوقت
            processed = i + 1
            elapsed_sec = time.time() - job_stats["start_time"]
            avg_time = elapsed_sec / processed
            rem_sec = avg_time * (len(videos) - processed)
            job_stats["elapsed"] = str(timedelta(seconds=int(elapsed_sec)))
            job_stats["eta"] = str(timedelta(seconds=int(rem_sec)))

            tasks = []
            if mode == "Audio Only": tasks.append(("Audio", "bestaudio/best", "mp3"))
            elif mode == "Videos Only": tasks.append(("Videos", f"bestvideo[height<={quality}]+bestaudio/best", "mp4"))
            elif mode == "Both":
                tasks.append(("Audio", "bestaudio/best", "mp3"))
                tasks.append(("Videos", f"bestvideo[height<={quality}]+bestaudio/best", "mp4"))

            for sub, fmt, ext in tasks:
                filename = f"{processed:03d} - {v_title}.{ext}"
                full_path = f"/{folder_name}/{sub}/{filename}"

                if check_exists(token, full_path):
                    job_stats["skipped"] += 1
                    continue

                job_stats.update({"current_file": f"[{sub}] {v_title[:20]}", "log": f"📡 نقل {processed}"})
                
                with yt_dlp.YoutubeDL({'format': fmt, 'cookiefile': 'cookies.txt', 'quiet': True, 'noplaylist': True}) as ydl_s:
                    info = ydl_s.extract_info(v_url, download=False)
                    if not info: continue
                    with requests.get(info['url'], stream=True, timeout=300) as r:
                        requests.post("https://content.dropboxapi.com/2/files/upload", 
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                                              "Dropbox-API-Arg": json.dumps({"path": full_path, "mode": "overwrite"})}, 
                                     data=r.iter_content(chunk_size=1024*512))
            
            job_stats["total_done"] = processed
            gc.collect()

        job_stats.update({"log": "✅ اكتمل العمل بنجاح", "active": False})
    except Exception as e:
        job_stats.update({"log": f"⚠️ خطأ: {str(e)[:30]}", "active": False})

UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RADAR PRO v34.0</title>
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 15px; }
        .container { max-width: 500px; margin: auto; border: 1px solid #0f0; padding: 20px; border-radius: 15px; box-shadow: 0 0 15px #0f03; }
        .stat-line { display: flex; justify-content: space-between; margin: 10px 0; border-bottom: 1px dashed #050; padding-bottom: 5px; font-size: 14px; }
        input, select, button { width: 100%; padding: 12px; margin: 5px 0; background: #000; color: #0f0; border: 1px solid #0f0; border-radius: 8px; }
        button { background: #0f0; color: #000; font-weight: bold; cursor: pointer; }
        .bar-container { background: #111; height: 12px; border: 1px solid #0f0; margin: 15px 0; border-radius: 6px; overflow: hidden; }
        #bar { background: #0f0; height: 100%; width: 0%; transition: 0.5s; }
        .label { color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="text-align:center">📊 رادار AK PRO v34.0</h2>
        <input id="u" placeholder="رابط يوتيوب">
        <input id="f" placeholder="اسم المجلد في Dropbox">
        <div style="display:flex; gap:5px;">
            <select id="m"><option value="Both">صوت + فيديو</option><option value="Audio Only">صوت فقط</option><option value="Videos Only">فيديو فقط</option></select>
            <select id="q"><option value="360">360p</option><option value="720">720p</option><option value="1080">1080p</option></select>
        </div>
        <select id="s"><option value="Most Viewed">الأكثر مشاهدة</option><option value="Newest">الأحدث</option><option value="Rating">الأعلى تقييماً</option></select>
        <button onclick="start()">بدء التشغيل 🚀</button>

        <div class="bar-container"><div id="bar"></div></div>
        
        <div id="stats_panel">
            <div class="stat-line"><span class="label">الحالة:</span> <span id="log">جاهز</span></div>
            <div class="stat-line"><span class="label">التقدم:</span> <span id="progress">0/0</span></div>
            <div class="stat-line"><span class="label">تخطي (موجود مسبقاً):</span> <span id="skip">0</span></div>
            <div class="stat-line"><span class="label">الوقت المنقضي:</span> <span id="elapsed">00:00:00</span></div>
            <div class="stat-line"><span class="label">الوقت المتبقي (ETA):</span> <span id="eta">00:00:00</span></div>
            <div class="stat-line"><span class="label">الملف الحالي:</span> <span id="curr">-</span></div>
        </div>
    </div>
    <script>
        function start(){
            const d = {url:document.getElementById('u').value, folder:document.getElementById('f').value, engine:'AK-A', sort:document.getElementById('s').value, mode:document.getElementById('m').value, quality:document.getElementById('q').value};
            fetch('/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
            setInterval(async () => {
                const r = await fetch('/status'); const j = await r.json();
                document.getElementById('log').innerText = j.log;
                document.getElementById('progress').innerText = j.total_done + " / " + j.total_count;
                document.getElementById('skip').innerText = j.skipped;
                document.getElementById('elapsed').innerText = j.elapsed;
                document.getElementById('eta').innerText = j.eta;
                document.getElementById('curr').innerText = j.current_file;
                if(j.total_count > 0) document.getElementById('bar').style.width = (j.total_done/j.total_count*100) + "%";
            }, 2000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(UI)

@app.route('/start', methods=['POST'])
def start_job():
    d = request.json
    threading.Thread(target=youtube_worker, args=(d['url'], d['folder'], d['mode'], d['quality'], d['sort'], 'AK-A')).start()
    return jsonify({"ok": True})

@app.route('/status')
def get_status(): return jsonify(job_stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
