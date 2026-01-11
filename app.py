import os, requests, json, urllib.parse, threading, time, gc
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp
from datetime import timedelta

app = Flask(__name__)

# --- 🔑 الإعدادات الأساسية ---
SITE_PASSWORD = "1234" 
UPLOAD_FOLDER_NAME = "/للرفع فقط"

def get_engines():
    return {
        "AK-A": {"id": "84031qa6rhfihqe", "secret": "pyoh81kjttomk7b", "ref": "3rGVqjd0T1IAAAAAAAAAAYsivkeMJpEjqt2jPzNFM_Y3ETQBojCGeXadZIMjyFg8"},
        "AK1": {"id": "9d4qz7zbqursfqv", "secret": "m26mrjxgbf8yk91", "ref": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"}
    }

job_stats = {"active": False, "log": "جاهز", "current_file": "-", "total_done": 0, "total_count": 0, "skipped": 0, "start_time": 0, "eta": "00:00:00", "elapsed": "00:00:00"}

# --- 🛠️ دوال المساعدة ---
def get_live_token(engine_name="AK1"):
    e = get_engines().get(engine_name)
    if not e: return None
    try:
        data = {"grant_type": "refresh_token", "refresh_token": e["ref"], "client_id": e["id"], "client_secret": e["secret"]}
        res = requests.post("https://api.dropboxapi.com/oauth2/token", data=data, timeout=15)
        return res.json().get("access_token")
    except: return None

# --- 🎬 منطق يوتيوب ---
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

# --- 🎨 الواجهة المدمجة ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Radar Pro Gold</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
    <style>
        :root { --gold: #d4af37; --bg: #050505; }
        body { background: var(--bg); color: #fff; font-family: 'Cairo', sans-serif; margin: 0; }
        .navbar { background: #111; padding: 12px 20px; border-bottom: 2px solid var(--gold); display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; }
        .drop-content { display: none; position: absolute; left: 20px; top: 55px; background: #1a1a1a; border: 1px solid var(--gold); border-radius: 8px; min-width: 180px; z-index: 2000; }
        .drop-content a { color: white; padding: 12px; text-decoration: none; display: block; border-bottom: 1px solid #333; }
        .show { display: block !important; }
        
        #login-overlay { position: fixed; inset: 0; background: #000; z-index: 10000; display: flex; align-items: center; justify-content: center; }
        .login-box { border: 1px solid var(--gold); padding: 40px; border-radius: 20px; background: #111; width: 90%; max-width: 350px; text-align: center; }
        
        .content-area { padding: 15px; min-height: 80vh; }
        .hidden { display: none !important; }
        input, select, button { width: 100%; background: #222; border: 1px solid #444; padding: 12px; border-radius: 8px; color: #fff; margin-bottom: 15px; }
        button { background: var(--gold); color: #000; font-weight: bold; cursor: pointer; border: none; }
        
        .file-card { background: rgba(255,255,255,0.05); margin-bottom: 8px; padding: 12px; border-radius: 10px; border: 1px solid #222; cursor: pointer; }
        #video-player-container { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 5000; display: none; }
    </style>
</head>
<body>
    <div id="login-overlay">
        <div class="login-box">
            <h2 style="color:var(--gold)">🛰️ دخول الرادار</h2>
            <input type="password" id="pass-input" placeholder="كلمة المرور">
            <button onclick="checkPass()">دخول</button>
        </div>
    </div>

    <div class="navbar">
        <b style="color:var(--gold)">RADAR PRO GOLD</b>
        <div style="position:relative;">
            <button onclick="toggleDrop()" style="background:var(--gold); border:none; padding:5px 15px; border-radius:5px;">القائمة <i class="fas fa-bars"></i></button>
            <div id="myDrop" class="drop-content">
                <a href="#" onclick="showSection('files')">📂 الأرشيف</a>
                <a href="#" onclick="showSection('yt')">🎬 اليوتيوب</a>
            </div>
        </div>
    </div>

    <div class="content-area">
        <div id="section-files">
            <input type="text" placeholder="بحث..." onkeyup="filterFiles(this.value)">
            <div id="file-list"></div>
        </div>

        <div id="section-yt" class="hidden">
            <div style="max-width:400px; margin:auto; background:#111; padding:20px; border-radius:15px; border:1px solid #333;">
                <h3 style="color:var(--gold)">🎬 نقل من يوتيوب</h3>
                <input id="yt-url" placeholder="رابط القناة">
                <input id="yt-folder" placeholder="اسم المجلد">
                <button onclick="startYt()">ابدأ الآن</button>
                <div id="yt-log" style="text-align:center; margin-top:15px; color:var(--gold);">جاهز</div>
            </div>
        </div>
    </div>

    <div id="video-player-container">
        <button onclick="closeVideo()" style="position:absolute; right:10px; top:10px; z-index:6000; background:red; width:40px; color:#fff;">X</button>
        <video id="v-player" class="video-js vjs-default-skin" controls preload="auto" width="100%" height="100%"></video>
    </div>

    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script>
        function toggleDrop() { document.getElementById('myDrop').classList.toggle('show'); }
        function showSection(s) {
            document.getElementById('section-files').classList.toggle('hidden', s !== 'files');
            document.getElementById('section-yt').classList.toggle('hidden', s !== 'yt');
            if(s === 'files') loadFiles("");
            toggleDrop();
        }

        async function checkPass() {
            if(document.getElementById('pass-input').value === "1234") {
                sessionStorage.setItem('loggedIn', 'true');
                document.getElementById('login-overlay').style.display = 'none';
                loadFiles("");
            } else alert("خطأ");
        }

        async function loadFiles(path) {
            const res = await fetch('/api/browse?path=' + encodeURIComponent(path));
            const data = await res.json();
            let h = "";
            data.forEach(f => {
                const isF = f['.tag'] === 'folder';
                h += `<div class="file-card" onclick="${isF ? `loadFiles('${f.path_display}')` : `playVideo('${f.path_display}')`}">
                    <b>${isF ? '📁' : '📄'} ${f.name}</b>
                </div>`;
            });
            document.getElementById('file-list').innerHTML = h || "مجلد فارغ";
        }

        function playVideo(path) {
            const url = `/api/stream?path=${encodeURIComponent(path)}`;
            document.getElementById('video-player-container').style.display = 'block';
            const player = videojs('v-player');
            player.src({type: 'video/mp4', src: url});
            player.play();
        }

        function closeVideo() {
            videojs('v-player').pause();
            document.getElementById('video-player-container').style.display = 'none';
        }

        async function startYt() {
            const d = {url: document.getElementById('yt-url').value, folder: document.getElementById('yt-folder').value, engine:'AK1', mode:'Both', quality:'360', sort:'Newest'};
            await fetch('/api/yt/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
            setInterval(async () => {
                const r = await fetch('/api/yt/status'); const j = await r.json();
                document.getElementById('yt-log').innerText = j.log + " (" + j.total_done + "/" + j.total_count + ")";
            }, 2000);
        }

        window.onload = () => { if(sessionStorage.getItem('loggedIn')) document.getElementById('login-overlay').style.display='none'; loadFiles(""); }
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(LAYOUT)

@app.route('/api/browse')
def browse():
    p = request.args.get('path', ''); token = get_live_token()
    r = requests.post("https://api.dropboxapi.com/2/files/list_folder", headers={"Authorization": f"Bearer {token}"}, json={"path": "" if p in ["", "/"] else p})
    return jsonify(r.json().get('entries', []))

@app.route('/api/stream')
def stream():
    token = get_live_token(); path = request.args.get('path')
    h = {"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": path})}
    r = requests.post("https://content.dropboxapi.com/2/files/download", headers=h, stream=True)
    return Response(stream_with_context(r.iter_content(chunk_size=512*1024)), content_type=r.headers.get('Content-Type'))

@app.route('/api/yt/start', methods=['POST'])
def start_yt():
    d = request.json
    threading.Thread(target=youtube_worker, args=(d['url'], d['folder'], d['mode'], d['quality'], d['sort'], d['engine'])).start()
    return jsonify({"ok": True})

@app.route('/api/yt/status')
def get_yt_status(): return jsonify(job_stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
