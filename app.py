import os, requests, json, threading, time, gc
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# --- 🔑 قاعدة بيانات المحركات (AK1 & AK-A فقط) ---
def get_engines():
    return {
        "AK-A": {"id": "84031qa6rhfihqe", "secret": "pyoh81kjttomk7b", "ref": "3rGVqjd0T1IAAAAAAAAAAYsivkeMJpEjqt2jPzNFM_Y3ETQBojCGeXadZIMjyFg8"},
        "AK1": {"id": "9d4qz7zbqursfqv", "secret": "m26mrjxgbf8yk91", "ref": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"}
    }

RAW_COOKIES = """GPS=1;YSC=cRPU3pja-SY;VISITOR_INFO1_LIVE=20zT46tInss;VISITOR_PRIVACY_METADATA=CgJFRxIEGgAgQw%3D%3D;PREF=tz=Africa.Cairo&f5=30000&f7=100;__Secure-1PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;__Secure-3PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;HSID=AU_XHwPsXUSGUgZUq;SSID=AUtRaUQzpuXcGFlsb;APISID=GGcg9KjkJelNvooU/AvZNu9CDwwOGpuxn0;SAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-1PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-3PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;SID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_XpfS3nrxc6u1zRA46komJgACgYKAYwSARUSFQHGX2Mim9bkw294mS0juox0SqUHlRoVAUF8yKpxxgQ2GqF2sh645dKyGxGU0076;__Secure-1PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_Prv_jFBo8DGf7MvL3m3YUwACgYKAWASARUSFQHGX2MiB-68MTGXuISLXx-5gLyoNxoVAUF8yKqj5sYlM5mxOCH1yIqQpG3p0076;__Secure-3PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_tmt8C6WACoM_TRnt53rcYgACgYKAZISARUSFQHGX2Milx8SWGqPhNOfk0cfC1hrNxoVAUF8yKoXkn7Q5sDuY655VEVQaFfe0076;SIDCC=AKEyXzVZST_aZ3zfmWm76iXCt5WkVKq9lnm4wmc6XtSaPWSkIgqZgUahd0zWcjJo2X7kL06F;__Secure-1PSIDCC=AKEyXzWxG1jy4IhsbzuwTPJHLE1x0La-UZmvUdZ_PtAVsuCHgR0-jXuOiEUURvwMHdUzZ_Ug;__Secure-3PSIDCC=AKEyXzV4xjKO2m6EFIdi4eYuSRs-iiGiW3nWtahuqEOILqD_ZSph3Gd5-yyY-syAw-1NLEyv;LOGIN_INFO=AFmmF2swRQIhAPjDN9b05Pm08f9dnxS73Hh4-ZyPVQnMWMTdhqvhin-9AiBXsnlmvdi0CXO8n-gKF4DXUxmi6i0YrK1KIgtd9XjAOw:QUQ3MjNmeTlfbGZFdmtlZWdhVHNPWllWcGF0RkQxVjBMLVBxM2Y3ZEhBcTlBRWxuQ2xRX1BhUEo1UzU1WEoyMEtiVGpvN3J4NlZpRUg3QXB2WnJJU3JtTlNwalE1RnIyYzhSMzhMOUNRRGV1cnFRQVp5c0VBbWZoZ2RMd2gtZVVJdFBxajlmbXFFc2hYcjJoMmdEVVotRmRrdHhWVVRnQUdB;"""

job_status = {"active": False, "current_file": "انتظار", "total_done": 0, "total_count": 0, "log": "جاهز"}

def create_cookie_file():
    with open("cookies.txt", "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in RAW_COOKIES.split(';'):
            if '=' in cookie:
                k, v = cookie.strip().split('=', 1)
                f.write(f".youtube.com\tTRUE\t/\tTRUE\t2147483647\t{k}\t{v}\n")

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
    job_status.update({"active": True, "log": "🔍 جاري تحليل الرابط...", "total_done": 0})
    
    try:
        ydl_opts = {'cookiefile': 'cookies.txt', 'quiet': True, 'extract_flat': True, 'ignoreerrors': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url, download=False)
            videos = [v for v in res.get('entries', [res]) if v]

            if sort_by == "Most Viewed": videos.sort(key=lambda x: x.get('view_count') or 0, reverse=True)
            elif sort_by == "Newest": videos.sort(key=lambda x: x.get('upload_date') or '', reverse=True)
            elif sort_by == "Oldest": videos.sort(key=lambda x: x.get('upload_date') or '')

            job_status["total_count"] = len(videos)

        for i, video in enumerate(videos):
            token = get_token(engine_name)
            gc.collect() # تفريغ الرام لضمان استمرار الفيديوهات الأخيرة
            
            v_url = video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}"
            v_title = "".join([c for c in video.get('title', 'Video') if c.isalnum() or c in " "]).strip()
            job_status.update({"current_file": v_title[:40], "log": f"📡 نقل ملف {i+1}"})

            fmt = 'bestaudio/best' if mode == "Audio Only" else f'best[height<={quality}][ext=mp4]/best'
            
            with yt_dlp.YoutubeDL({'format': fmt, 'cookiefile': 'cookies.txt', 'quiet': True, 'noplaylist': True}) as ydl_s:
                info = ydl_s.extract_info(v_url, download=False)
                stream_url = info['url']
                filename_actual = f"{(i+1):03d} - {v_title}.{info.get('ext', 'mp4')}"

                with requests.get(stream_url, stream=True, timeout=600) as r:
                    requests.post("https://content.dropboxapi.com/2/files/upload", 
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                                          "Dropbox-API-Arg": json.dumps({"path": f"/{folder_name}/{filename_actual}", "mode": "overwrite"})}, 
                                 data=r.iter_content(chunk_size=512*1024))
            
            job_status["total_done"] = i + 1
            time.sleep(5) 

        job_status.update({"log": "✅ اكتملت القائمة بنجاح", "active": False})
    except Exception as e:
        job_status.update({"log": f"⚠️ خطأ: {str(e)[:40]}", "active": False})

UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RADAR AK Lite</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: sans-serif; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .box { background: #111; width: 94%; max-width: 450px; padding: 25px; border: 2px solid #00ff41; border-radius: 20px; box-shadow: 0 0 30px rgba(0,255,65,0.2); }
        h2 { text-align: center; margin: 0 0 20px 0; text-shadow: 0 0 10px #00ff41; }
        input, select, button { width: 100%; padding: 16px; margin: 10px 0; background: #000; color: #00ff41; border: 1px solid #00ff41; border-radius: 12px; font-size: 16px; -webkit-appearance: none; }
        button { background: #00ff41; color: #000; font-weight: bold; font-size: 18px; border: none; cursor: pointer; }
        .progress-area { margin-top: 25px; background: #000; padding: 15px; border-radius: 15px; border: 1px dashed #444; }
        .bar-bg { height: 14px; background: #222; border-radius: 7px; overflow: hidden; margin: 12px 0; }
        .bar-fill { height: 100%; background: #00ff41; width: 0%; transition: 0.6s ease; box-shadow: 0 0 15px #00ff41; }
        #log { font-size: 14px; text-align: center; margin-bottom: 5px; }
        #stats { display: flex; justify-content: space-between; font-size: 13px; color: #fff; }
    </style>
</head>
<body>
    <div class="box">
        <h2>🛰️ رادار AK Lite</h2>
        <input id="u" placeholder="رابط يوتيوب">
        <input id="f" placeholder="المجلد في Dropbox">
        <select id="e">
            <option value="AK-A">المحرك AK-A</option>
            <option value="AK1">المحرك AK1</option>
        </select>
        <div style="display: flex; gap: 10px;">
            <select id="m"><option>Videos Only</option><option>Audio Only</option></select>
            <select id="q"><option value="360">360p</option><option value="720">720p</option></select>
        </div>
        <select id="s">
            <option value="Default">الترتيب الافتراضي</option>
            <option value="Newest">الأحدث أولاً</option>
        </select>
        <button onclick="start()">إطلاق الرادار 🚀</button>
        <div class="progress-area">
            <div id="log">في انتظار الأوامر...</div>
            <div class="bar-bg"><div id="fill" class="bar-fill"></div></div>
            <div id="stats">
                <span>تم: <b id="done">0</b> / <b id="total">0</b></span>
                <span id="perc">0%</span>
            </div>
        </div>
    </div>
    <script>
        function start(){
            const d = {url:document.getElementById('u').value, folder:document.getElementById('f').value, engine:document.getElementById('e').value, sort:document.getElementById('s').value, mode:document.getElementById('m').value, quality:document.getElementById('q').value};
            fetch('/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
            setInterval(async () => {
                const r = await fetch('/status'); const j = await r.json();
                document.getElementById('log').innerText = j.log;
                document.getElementById('done').innerText = j.total_done;
                document.getElementById('total').innerText = j.total_count;
                if(j.total_count > 0) {
                    let p = (j.total_done / j.total_count * 100).toFixed(0);
                    document.getElementById('fill').style.width = p + "%";
                    document.getElementById('perc').innerText = p + "%";
                }
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
