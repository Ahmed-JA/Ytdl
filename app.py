import os, requests, json, urllib.parse, threading, time, gc
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

job_stats = {"active": False, "log": "جاهز", "current_file": "-", "total_done": 0, "total_count": 0, "skipped": 0, "start_time": 0, "eta": "00:00:00", "elapsed": "00:00:00"}

# --- 🛠️ دوال المساعدة ---
def get_live_token(engine_name="AK1"):
    e = get_engines().get(engine_name)
    try:
        data = {"grant_type": "refresh_token", "refresh_token": e["ref"], "client_id": e["id"], "client_secret": e["secret"]}
        res = requests.post("https://api.dropboxapi.com/oauth2/token", data=data, timeout=15)
        return res.json().get("access_token")
    except: return None

# --- 🎬 محرك اليوتيوب ---
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
        job_stats.update({"log": "✅ اكتمل العمل", "active": False})
    except Exception as e:
        job_stats.update({"log": f"⚠️ خطأ: {str(e)[:20]}", "active": False})

# --- 🎨 الواجهة المدمجة (تجمع بين Radar Gold واليوتيوب) ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Radar Gold Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root { --gold: #d4af37; --bg: #050505; --glass: rgba(255, 255, 255, 0.05); }
        body { background: var(--bg); color: #fff; font-family: 'Cairo', sans-serif; margin: 0; }
        
        /* الهيدر الذهبي المدمج */
        .navbar { background: #111; padding: 10px 20px; border-bottom: 2px solid var(--gold); display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; }
        .nav-link { color: var(--gold); text-decoration: none; font-weight: bold; padding: 5px 10px; border: 1px solid var(--gold); border-radius: 8px; font-size: 13px; cursor: pointer; }

        /* واجهة الدخول */
        #login-overlay { position: fixed; inset: 0; background: #000; z-index: 10000; display: flex; align-items: center; justify-content: center; }
        .login-box { border: 1px solid var(--gold); padding: 30px; border-radius: 20px; background: #111; width: 90%; max-width: 350px; text-align: center; }
        
        /* الأقسام */
        .section { padding: 15px; display: none; }
        .active-section { display: block; }
        
        input { width: 100%; background: #222; border: 1px solid #444; padding: 12px; border-radius: 10px; color: #fff; margin-bottom: 10px; box-sizing: border-box; }
        button { width: 100%; background: var(--gold); border: none; padding: 12px; border-radius: 10px; font-weight: bold; cursor: pointer; color: #000; }
        
        .file-row { background: var(--glass); border: 1px solid #222; padding: 12px; border-radius: 12px; margin-bottom: 8px; cursor: pointer; }
        .file-row:hover { border-color: var(--gold); }
    </style>
</head>
<body>
    <div id="login-overlay">
        <div class="login-box">
            <h2 style="color:var(--gold)">🛰️ RADAR GOLD</h2>
            <input type="password" id="pass-input" placeholder="كلمة المرور">
            <button onclick="checkPass()">تأكيد الدخول</button>
        </div>
    </div>

    <div id="main-ui" style="display:none;">
        <div class="navbar">
            <b style="color:var(--gold); font-size:18px;">RADAR PRO</b>
            <div style="display:flex; gap:10px;">
                <div class="nav-link" onclick="switchSection('files')">📁 الأرشيف</div>
                <div class="nav-link" onclick="switchSection('yt')">🎬 اليوتيوب</div>
            </div>
        </div>

        <div id="files-sec" class="section active-section">
            <input type="text" placeholder="ابحث في الأرشيف..." onkeyup="filterFiles(this.value)">
            <div id="file-list"></div>
        </div>

        <div id="yt-sec" class="section">
            <div style="max-width:400px; margin:auto; background:#111; padding:20px; border-radius:15px; border:1px solid #333;">
                <h3 style="color:var(--gold); text-align:center;">🎬 محمل اليوتيوب</h3>
                <input id="yt-url" placeholder="رابط القناة أو القائمة">
                <input id="yt-folder" placeholder="اسم المجلد (داخل خاص يوتيوب)">
                <button onclick="startYt()">ابدأ النقل 🚀</button>
                <div id="yt-log" style="margin-top:20px; text-align:center; color:var(--gold);">الحالة: جاهز</div>
            </div>
        </div>
    </div>

    <script>
        async function checkPass() {
            const p = document.getElementById('pass-input').value;
            const res = await fetch('/api/verify?pass=' + encodeURIComponent(p));
            const d = await res.json();
            if(d.valid) {
                document.getElementById('login-overlay').style.display = 'none';
                document.getElementById('main-ui').style.display = 'block';
                loadFiles("");
            } else alert("❌ كلمة المرور خطأ");
        }

        function switchSection(s) {
            document.getElementById('files-sec').classList.toggle('active-section', s === 'files');
            document.getElementById('yt-sec').classList.toggle('active-section', s === 'yt');
        }

        async function loadFiles(path) {
            const res = await fetch('/api/browse?path=' + encodeURIComponent(path));
            const files = await res.json();
            let h = "";
            files.forEach(f => {
                const isF = f['.tag'] === 'folder';
                h += `<div class="file-row" onclick="${isF ? `loadFiles('${f.path_display}')` : `alert('جاري التشغيل...')`}">
                    <b>${isF ? '📁' : '📄'} ${f.name}</b>
                </div>`;
            });
            document.getElementById('file-list').innerHTML = h || "المجلد فارغ";
        }

        async function startYt() {
            const d = {url: document.getElementById('yt-url').value, folder: document.getElementById('yt-folder').value, engine:'AK1', mode:'Both', quality:'360', sort:'Newest'};
            document.getElementById('yt-log').innerText = "📡 جاري التحليل...";
            await fetch('/api/yt/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
            setInterval(async () => {
                const r = await fetch('/api/yt/status'); const j = await r.json();
                document.getElementById('yt-log').innerText = j.log + " (" + j.total_done + "/" + j.total_count + ")";
            }, 2000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(LAYOUT)

@app.route('/api/verify')
def verify(): return jsonify({"valid": request.args.get('pass') == SITE_PASSWORD})

@app.route('/api/browse')
def browse():
    p = request.args.get('path', ''); token = get_live_token()
    r = requests.post("https://api.dropboxapi.com/2/files/list_folder", headers={"Authorization": f"Bearer {token}"}, json={"path": "" if p in ["", "/"] else p})
    return jsonify(r.json().get('entries', []))

@app.route('/api/yt/start', methods=['POST'])
def start_yt():
    d = request.json
    threading.Thread(target=youtube_worker, args=(d['url'], d['folder'], d['mode'], d['quality'], d['sort'], d['engine'])).start()
    return jsonify({"ok": True})

@app.route('/api/yt/status')
def get_yt_status(): return jsonify(job_stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
