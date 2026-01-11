import os, requests, json, threading, time, gc, urllib.parse
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp
from datetime import timedelta

app = Flask(__name__)

# --- 🔑 الإعدادات العامة ---
SITE_PASSWORD = "1234"
UPLOAD_FOLDER_NAME = "/للرفع فقط"

# قاعدة بيانات محركات اليوتيوب
def get_engines():
    return {
        "AK-A": {"id": "84031qa6rhfihqe", "secret": "pyoh81kjttomk7b", "ref": "3rGVqjd0T1IAAAAAAAAAAYsivkeMJpEjqt2jPzNFM_Y3ETQBojCGeXadZIMjyFg8"},
        "AK1": {"id": "9d4qz7zbqursfqv", "secret": "m26mrjxgbf8yk91", "ref": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"}
    }

# كوكيز اليوتيوب
RAW_COOKIES = """GPS=1;VISITOR_INFO1_LIVE=20zT46tInss; ... """ # ضع الكوكيز الخاصة بك هنا

job_stats = {"active": False, "log": "جاهز", "current_file": "-", "total_done": 0, "total_count": 0, "skipped": 0, "start_time": 0, "eta": "00:00:00", "elapsed": "00:00:00"}

# --- 🛠️ دوال المساعدة ---
def get_live_token(engine_name="AK1"):
    e = get_engines().get(engine_name)
    try:
        data = {"grant_type": "refresh_token", "refresh_token": e["ref"], "client_id": e["id"], "client_secret": e["secret"]}
        res = requests.post("https://api.dropboxapi.com/oauth2/token", data=data, timeout=15)
        return res.json().get("access_token")
    except: return None

# --- 🛰️ منطق يوتيوب (الرادار) ---
def create_cookie_file():
    with open("cookies.txt", "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in RAW_COOKIES.split(';'):
            if '=' in cookie:
                parts = cookie.strip().split('=', 1)
                if len(parts) == 2:
                    f.write(f".youtube.com\tTRUE\t/\tTRUE\t2147483647\t{parts[0]}\t{parts[1]}\n")

def check_exists(token, path):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        res = requests.post("https://api.dropboxapi.com/2/files/get_metadata", headers=headers, json={"path": path})
        return res.status_code == 200
    except: return False

def youtube_worker(url, folder_name, mode, quality, sort_by, engine_name):
    global job_stats
    create_cookie_file()
    job_stats.update({"active": True, "log": "🔍 تحليل القناة...", "total_done": 0, "skipped": 0, "start_time": time.time()})
    try:
        ydl_opts = {'cookiefile': 'cookies.txt', 'quiet': True, 'extract_flat': True, 'ignoreerrors': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url, download=False)
            videos = [v for v in res.get('entries', [res]) if v]
            job_stats["total_count"] = len(videos)

        for i, video in enumerate(videos):
            token = get_live_token(engine_name)
            v_url = video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}"
            v_title = "".join([c for c in video.get('title', 'Video') if c.isalnum() or c in " "]).strip()
            
            processed = i + 1
            tasks = []
            if mode in ["Audio Only", "Both"]: tasks.append(("Audio", "bestaudio/best", "mp3"))
            if mode in ["Videos Only", "Both"]: tasks.append(("Videos", f"best[height<={quality}][ext=mp4]/best", "mp4"))

            for sub, fmt, ext in tasks:
                filename = f"{processed:03d} - {v_title}.{ext}"
                full_path = f"/خاص يوتيوب/{folder_name}/{sub}/{filename}"
                if check_exists(token, full_path):
                    job_stats["skipped"] += 1
                    continue
                
                job_stats.update({"current_file": f"[{sub}] {v_title[:20]}", "log": f"📡 ينقل {processed}"})
                with yt_dlp.YoutubeDL({'format': fmt, 'cookiefile': 'cookies.txt', 'quiet': True}) as ydl_s:
                    info = ydl_s.extract_info(v_url, download=False)
                    with requests.get(info['url'], stream=True, timeout=300) as r:
                        requests.post("https://content.dropboxapi.com/2/files/upload", 
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                                              "Dropbox-API-Arg": json.dumps({"path": full_path, "mode": "overwrite"})}, 
                                     data=r.iter_content(chunk_size=1024*1024))
            job_stats["total_done"] = processed
            gc.collect()
        job_stats.update({"log": "✅ اكتمل العمل", "active": False})
    except Exception as e:
        job_stats.update({"log": f"⚠️ خطأ: {str(e)[:30]}", "active": False})

# --- 🎨 القوالب المشتركة (Navbar) ---
NAVBAR_HTML = """
<div style="background: #111; padding: 10px; border-bottom: 2px solid #d4af37; display: flex; justify-content: space-between; align-items: center;">
    <b style="color:#d4af37; font-size:18px;">RADAR PRO</b>
    <div style="position: relative; display: inline-block;">
        <button onclick="document.getElementById('drop').classList.toggle('show')" style="background:#d4af37; color:#000; border:none; padding:8px 15px; border-radius:5px; font-weight:bold; cursor:pointer;">
            القائمة <i class="fas fa-chevron-down"></i>
        </button>
        <div id="drop" style="display:none; position:absolute; left:0; background:#222; min-width:160px; box-shadow:0 8px 16px rgba(0,0,0,0.5); z-index:9999; border-radius:5px; margin-top:5px;">
            <a href="/" style="color:white; padding:12px 16px; text-decoration:none; display:block; border-bottom:1px solid #333;">📂 مستعرض الملفات</a>
            <a href="/youtube" style="color:white; padding:12px 16px; text-decoration:none; display:block;">🎬 محمل اليوتيوب</a>
        </div>
    </div>
</div>
<style>
    .show { display:block !important; }
    body { margin:0; font-family: 'Cairo', sans-serif; background:#000; color:#fff; }
</style>
"""

# --- 🏠 المسارات (Routes) ---

@app.route('/')
def index():
    # كود واجهة تصفح الملفات (Radar Gold)
    # ملاحظة: أضفنا NAVBAR_HTML في بداية UI_HTML الخاصة بك
    return render_template_string(NAVBAR_HTML + UI_HTML)

@app.route('/youtube')
def youtube_page():
    # كود واجهة تحميل اليوتيوب
    YOUTUBE_UI = """
    <div style="padding:20px; max-width:500px; margin:auto;">
        <h2 style="text-align:center; color:#d4af37;">🎬 محمل اليوتيوب إلى Dropbox</h2>
        <input id="u" placeholder="رابط القناة" style="width:100%; padding:10px; margin-bottom:10px; background:#111; color:#fff; border:1px solid #d4af37;">
        <input id="f" placeholder="اسم المجلد" style="width:100%; padding:10px; margin-bottom:10px; background:#111; color:#fff; border:1px solid #d4af37;">
        <button onclick="startYt()" style="width:100%; padding:15px; background:#d4af37; color:#000; font-weight:bold; border:none; cursor:pointer;">ابدأ النقل 🚀</button>
        <div id="status" style="margin-top:20px; text-align:center; border:1px solid #333; padding:10px;">الحالة: جاهز</div>
    </div>
    <script>
        async function startYt(){
            const d = {url:document.getElementById('u').value, folder:document.getElementById('f').value, engine:'AK1', mode:'Both', quality:'360', sort:'Newest'};
            await fetch('/api/yt/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
            setInterval(async () => {
                const r = await fetch('/api/yt/status'); const j = await r.json();
                document.getElementById('status').innerText = j.log + " | " + j.total_done + "/" + j.total_count;
            }, 2000);
        }
    </script>
    """
    return render_template_string(NAVBAR_HTML + YOUTUBE_UI)

# --- APIs المدمجة ---
@app.route('/api/verify')
def verify(): return jsonify({"valid": request.args.get('pass') == SITE_PASSWORD})

@app.route('/api/browse')
def browse():
    p = request.args.get('path', ''); token = get_live_token()
    r = requests.post("https://api.dropboxapi.com/2/files/list_folder", headers={"Authorization": f"Bearer {token}"}, json={"path": "" if p in ["", "/"] else p})
    return jsonify(r.json().get('entries', []))

@app.route('/api/stream')
def stream():
    token = get_live_token(); h = {"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": request.args.get('path')})}
    r = requests.post("https://content.dropboxapi.com/2/files/download", headers=h, stream=True)
    return Response(stream_with_context(r.iter_content(chunk_size=256*1024)), content_type=r.headers.get('Content-Type'))

@app.route('/api/yt/start', methods=['POST'])
def start_yt():
    d = request.json
    threading.Thread(target=youtube_worker, args=(d['url'], d['folder'], d['mode'], d['quality'], d['sort'], d['engine'])).start()
    return jsonify({"ok": True})

@app.route('/api/yt/status')
def get_yt_status(): return jsonify(job_stats)

# (أضف باقي دوال الرفع والتحميل ZIP من كودك الأصلي هنا بنفس النمط)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
