import os, requests, json, threading, time, gc
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# --- 🔑 قاعدة بيانات المحركات ---
def get_engines():
    return {
        "AK-A": {"id": "84031qa6rhfihqe", "secret": "pyoh81kjttomk7b", "ref": "3rGVqjd0T1IAAAAAAAAAAYsivkeMJpEjqt2jPzNFM_Y3ETQBojCGeXadZIMjyFg8"},
        "AK1": {"id": "9d4qz7zbqursfqv", "secret": "m26mrjxgbf8yk91", "ref": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"}
    }

RAW_COOKIES = """COOKIES_HERE""" # ضع الكوكيز الخاصة بك هنا

job_status = {"active": False, "current_file": "انتظار", "total_done": 0, "total_count": 0, "log": "جاهز"}

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

def youtube_worker(url, folder_name, mode, quality, sort_by, engine_name):
    global job_status
    create_cookie_file()
    job_status.update({"active": True, "log": "🔍 تحليل القناة...", "total_done": 0})
    
    try:
        ydl_opts = {'cookiefile': 'cookies.txt', 'quiet': True, 'extract_flat': True, 'ignoreerrors': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url, download=False)
            if not res: raise Exception("فشل التحليل")
            videos = [v for v in res.get('entries', [res]) if v]

            # الترتيب المتقدم
            if sort_by == "Most Viewed": videos.sort(key=lambda x: x.get('view_count') or 0, reverse=True)
            elif sort_by == "Newest": videos.sort(key=lambda x: x.get('upload_date') or '', reverse=True)
            elif sort_by == "Oldest": videos.sort(key=lambda x: x.get('upload_date') or '')
            elif sort_by == "Rating": videos.sort(key=lambda x: x.get('like_count') or 0, reverse=True)

            job_status["total_count"] = len(videos)

        for i, video in enumerate(videos):
            try:
                token = get_token(engine_name)
                gc.collect() 
                v_url = video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}"
                v_title = "".join([c for c in video.get('title', 'Video') if c.isalnum() or c in " "]).strip()
                
                # قائمة المهام (صوت، فيديو، أو كلاهما)
                tasks = []
                if mode == "Audio Only": tasks.append(("Audio", "bestaudio/best", "mp3"))
                elif mode == "Videos Only": tasks.append(("Videos", f"bestvideo[height<={quality}]+bestaudio/best", "mp4"))
                elif mode == "Both":
                    tasks.append(("Audio", "bestaudio/best", "mp3"))
                    tasks.append(("Videos", f"bestvideo[height<={quality}]+bestaudio/best", "mp4"))

                for sub_folder, fmt, default_ext in tasks:
                    job_status.update({"current_file": f"[{sub_folder}] {v_title[:30]}", "log": f"📡 معالجة {i+1}"})
                    
                    with yt_dlp.YoutubeDL({'format': fmt, 'cookiefile': 'cookies.txt', 'quiet': True, 'noplaylist': True, 'ignoreerrors': True}) as ydl_s:
                        info = ydl_s.extract_info(v_url, download=False)
                        if not info: continue
                        
                        stream_url = info['url']
                        ext = info.get('ext', default_ext)
                        filename = f"{(i+1):03d} - {v_title}.{ext}"
                        
                        # المسار المطلوب: خاص يوتيوب / اسم المجلد / (Audio أو Videos)
                        full_dropbox_path = f"/خاص يوتيوب/{folder_name}/{sub_folder}/{filename}"

                        with requests.get(stream_url, stream=True, timeout=300) as r:
                            requests.post("https://content.dropboxapi.com/2/files/upload", 
                                         headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                                                  "Dropbox-API-Arg": json.dumps({"path": full_dropbox_path, "mode": "overwrite"})}, 
                                         data=r.iter_content(chunk_size=1024*512))
                
                job_status["total_done"] = i + 1
                time.sleep(2)
            except Exception as e: continue

        job_status.update({"log": "✅ اكتملت المهمة بنجاح", "active": False})
    except Exception as e:
        job_status.update({"log": f"⚠️ خطأ: {str(e)[:40]}", "active": False})

UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RADAR AK PRO v33.8</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: sans-serif; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .box { background: #111; width: 95%; max-width: 500px; padding: 25px; border: 2px solid #00ff41; border-radius: 20px; box-shadow: 0 0 15px #00ff4144; }
        input, select, button { width: 100%; padding: 14px; margin: 8px 0; background: #000; color: #00ff41; border: 1px solid #00ff41; border-radius: 12px; font-size: 15px; }
        button { background: #00ff41; color: #000; font-weight: bold; cursor: pointer; border: none; transition: 0.3s; }
        button:hover { background: #00cc33; }
        .bar-bg { height: 14px; background: #222; border-radius: 7px; overflow: hidden; margin: 15px 0; border: 1px solid #00ff4155; }
        .bar-fill { height: 100%; background: linear-gradient(90deg, #00ff41, #008822); width: 0%; transition: 0.5s; }
        .status-txt { text-align: center; font-size: 14px; margin-top: 10px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="text-align:center;">🛰️ رادار v33.8 برو</h2>
        <input id="u" placeholder="رابط القناة أو القائمة">
        <input id="f" placeholder="اسم المجلد الرئيسي">
        
        <div class="grid">
            <select id="e">
                <option value="AK-A">المحرك AK-A</option>
                <option value="AK1">المحرك AK1</option>
            </select>
            <select id="m">
                <option value="Both">صوت + فيديو (Both)</option>
                <option value="Audio Only">صوت فقط (Audio)</option>
                <option value="Videos Only">فيديو فقط (Video)</option>
            </select>
        </div>

        <div class="grid">
            <select id="q">
                <option value="144">144p</option>
                <option value="360" selected>360p</option>
                <option value="480">480p</option>
                <option value="720">720p HD</option>
                <option value="1080">1080p FHD</option>
                <option value="1440">2K</option>
                <option value="2160">4K</option>
            </select>
            <select id="s">
                <option value="Default">الترتيب الافتراضي</option>
                <option value="Most Viewed">الأكثر مشاهدة 🔥</option>
                <option value="Rating">الأعلى تقييماً ⭐</option>
                <option value="Newest">الأحدث 🆕</option>
                <option value="Oldest">الأقدم 🕰️</option>
            </select>
        </div>

        <button onclick="start()">إطلاق الرادار 🚀</button>
        
        <div class="bar-bg"><div id="fill" class="bar-fill"></div></div>
        <div id="log" class="status-txt">الحالة: جاهز</div>
        <div id="stats" style="text-align:center; font-size:12px; color:#888;">0 / 0</div>
    </div>

    <script>
        function start(){
            const d = {
                url:document.getElementById('u').value, 
                folder:document.getElementById('f').value, 
                engine:document.getElementById('e').value, 
                sort:document.getElementById('s').value, 
                mode:document.getElementById('m').value, 
                quality:document.getElementById('q').value
            };
            fetch('/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
            setInterval(async () => {
                const r = await fetch('/status'); const j = await r.json();
                document.getElementById('log').innerText = j.log + " | " + j.current_file;
                document.getElementById('stats').innerText = j.total_done + " / " + j.total_count;
                if(j.total_count > 0) document.getElementById('fill').style.width = (j.total_done/j.total_count*100) + "%";
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
    threading.Thread(target=youtube_worker, args=(d['url'], d['folder'], d['mode'], d['quality'], d['sort'], d['engine'])).start()
    return jsonify({"ok": True})

@app.route('/status')
def get_status(): return jsonify(job_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
