import os, requests, json, threading, time, subprocess
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# --- 🔑 قاعدة بيانات المحركات (Dropbox & WebDAV) ---
ENGINES = {
    "AK1": {"id": "9d4qz7zbqursfqv", "secret": "m26mrjxgbf8yk91", "refresh": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"},
    "AK-A": {"id": "84031qa6rhfihqe", "secret": "pyoh81kjttomk7b", "refresh": "3rGVqjd0T1IAAAAAAAAAAYsivkeMJpEjqt2jPzNFM_Y3ETQBojCGeXadZIMjyFg8"},
    "WebDAV_Server": {"url": "https://obedientsupporters.co/remote.php/dav/files/Kabil1", "user": "kabil1", "pass": "42891356111"}
}

RAW_COOKIES = """GPS=1;YSC=cRPU3pja-SY;VISITOR_INFO1_LIVE=20zT46tInss;VISITOR_PRIVACY_METADATA=CgJFRxIEGgAgQw%3D%3D;PREF=tz=Africa.Cairo&f5=30000&f7=100;__Secure-1PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;__Secure-3PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;HSID=AU_XHwPsXUSGUgZUq;SSID=AUtRaUQzpuXcGFlsb;APISID=GGcg9KjkJelNvooU/AvZNu9CDwwOGpuxn0;SAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-1PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-3PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;SID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_XpfS3nrxc6u1zRA46komJgACgYKAYwSARUSFQHGX2Mim9bkw294mS0juox0SqUHlRoVAUF8yKpxxgQ2GqF2sh645dKyGxGU0076;__Secure-1PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_Prv_jFBo8DGf7MvL3m3YUwACgYKAWASARUSFQHGX2MiB-68MTGXuISLXx-5gLyoNxoVAUF8yKqj5sYlM5mxOCH1yIqQpG3p0076;__Secure-3PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_tmt8C6WACoM_TRnt53rcYgACgYKAZISARUSFQHGX2Milx8SWGqPhNOfk0cfC1hrNxoVAUF8yKoXkn7Q5sDuY655VEVQaFfe0076;SIDCC=AKEyXzVZST_aZ3zfmWm76iXCt5WkVKq9lnm4wmc6XtSaPWSkIgqZgUahd0zWcjJo2X7kL06F;__Secure-1PSIDCC=AKEyXzWxG1jy4IhsbzuwTPJHLE1x0La-UZmvUdZ_PtAVsuCHgR0-jXuOiEUURvwMHdUzZ_Ug;__Secure-3PSIDCC=AKEyXzV4xjKO2m6EFIdi4eYuSRs-iiGiW3nWtahuqEOILqD_ZSph3Gd5-yyY-syAw-1NLEyv;LOGIN_INFO=AFmmF2swRQIhAPjDN9b05Pm08f9dnxS73Hh4-ZyPVQnMWMTdhqvhin-9AiBXsnlmvdi0CXO8n-gKF4DXUxmi6i0YrK1KIgtd9XjAOw:QUQ3MjNmeTlfbGZFdmtlZWdhVHNPWllWcGF0RkQxVjBMLVBxM2Y3ZEhBcTlBRWxuQ2xRX1BhUEo1UzU1WEoyMEtiVGpvN3J4NlZpRUg3QXB2WnJJU3JtTlNwalE1RnIyYzhSMzhMOUNRRGV1cnFRQVp5c0VBbWZoZ2RMd2gtZVVJdFBxajlmbXFFc2hYcjJoMmdEVVotRmRrdHhWVVRnQUdB;"""

job_status = {"active": False, "current_file": "لا يوجد", "total_done": 0, "total_count": 0, "log": "جاهز"}

def create_cookie_file():
    with open("cookies.txt", "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in RAW_COOKIES.split(';'):
            if '=' in cookie:
                k, v = cookie.strip().split('=', 1)
                f.write(f".youtube.com\tTRUE\t/\tTRUE\t2147483647\t{k}\t{v}\n")

def get_token(engine_name):
    e = ENGINES[engine_name]
    try:
        res = requests.post("https://api.dropboxapi.com/oauth2/token", data={"grant_type": "refresh_token", "refresh_token": e["refresh"], "client_id": e["id"], "client_secret": e["secret"]}, timeout=15)
        return res.json().get("access_token")
    except: return None

def youtube_worker(url, folder_name, mode, quality, sort_by, engine_name):
    global job_status
    create_cookie_file()
    job_status.update({"active": True, "log": "🔍 تحليل وبحث...", "total_done": 0})
    
    try:
        ydl_opts = {'cookiefile': 'cookies.txt', 'quiet': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url, download=False)
            videos = [v for v in res.get('entries', [res]) if v]

            # --- 🛠️ تفعيل الفرز الذكي ---
            if sort_by == "Most Viewed": videos.sort(key=lambda x: x.get('view_count') or 0, reverse=True)
            elif sort_by == "Newest": videos.sort(key=lambda x: x.get('upload_date') or '', reverse=True)
            elif sort_by == "Oldest": videos.sort(key=lambda x: x.get('upload_date') or '')

            job_status["total_count"] = len(videos)

        for i, video in enumerate(videos):
            v_url = video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}"
            v_title = "".join([c for c in video.get('title', 'Video') if c.isalnum() or c in " "]).strip()
            job_status.update({"current_file": v_title, "log": f"📡 معالجة {i+1} من {len(videos)}"})

            # صيغة التحميل (فيديو مدمج لتوفير الرام)
            fmt = 'bestaudio/best' if mode == "Audio Only" else f'best[height<={quality}][ext=mp4]/best'
            
            with yt_dlp.YoutubeDL({'format': fmt, 'cookiefile': 'cookies.txt', 'quiet': True, 'noplaylist': True}) as ydl_s:
                info = ydl_s.extract_info(v_url, download=False)
                stream_url = info['url']
                filename = f"{(i+1):03d} - {v_title}.{info.get('ext', 'mp4')}"

                # --- 🔀 توجيه الملف (WebDAV أو Dropbox) ---
                if engine_name == "WebDAV_Server":
                    e = ENGINES["WebDAV_Server"]
                    target_url = f"{e['url']}/{folder_name}/{filename}".replace(" ", "%20")
                    with requests.get(stream_url, stream=True) as r:
                        requests.put(target_url, auth=(e['user'], e['pass']), data=r.raw)
                else:
                    token = get_token(engine_name)
                    db_path = f"/{folder_name}/{filename}"
                    with requests.get(stream_url, stream=True) as r:
                        requests.post("https://content.dropboxapi.com/2/files/upload", 
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                                              "Dropbox-API-Arg": json.dumps({"path": db_path, "mode": "overwrite"})}, data=r.raw)
            
            job_status["total_done"] = i + 1
            time.sleep(3) # استراحة للسيرفر

        job_status.update({"log": "✅ اكتملت المهمة بنجاح", "active": False})
    except Exception as e:
        job_status.update({"log": f"⚠️ خطأ: {str(e)[:40]}", "active": False})

# --- 🎨 الواجهة المتكاملة ---
UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>Radar Pro v31</title>
    <style>
        body { background: #050505; color: #00ff00; font-family: 'Courier New', monospace; display: flex; align-items: center; justify-content: center; height: 100vh; margin:0; }
        .box { background: #111; padding: 25px; border: 1px solid #00ff00; width: 420px; box-shadow: 0 0 20px #00ff0022; border-radius: 10px; }
        input, select, button { width: 100%; padding: 12px; margin: 6px 0; background: #000; color: #00ff00; border: 1px solid #00ff00; border-radius: 5px; font-weight: bold; }
        button { cursor: pointer; transition: 0.3s; }
        button:hover { background: #00ff00; color: #000; }
        .bar { height: 15px; background: #222; border-radius: 8px; margin: 15px 0; overflow: hidden; border: 1px solid #333; }
        .fill { height: 100%; background: #00ff00; width: 0%; transition: 0.5s; box-shadow: 0 0 10px #00ff00; }
        #log { font-size: 13px; text-align: center; color: #00ff00; }
        #st { font-size: 14px; text-align: center; margin-top: 5px; color: #fff; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="text-align:center; margin-bottom:15px;">🛰️ رادار KOYEB v31</h2>
        <input id="u" placeholder="أدخل رابط يوتيوب هنا">
        <input id="f" placeholder="اسم مجلد الوجهة">
        <select id="e">
            <option value="AK-A">محرك Dropbox: AK-A</option>
            <option value="AK1">محرك Dropbox: AK1</option>
            <option value="WebDAV_Server">سيرفر WebDAV: الأرشيف الجامع</option>
        </select>
        <select id="s">
            <option value="Default">الترتيب: الافتراضي</option>
            <option value="Most Viewed">الترتيب: الأكثر مشاهدة</option>
            <option value="Newest">الترتيب: الأحدث أولاً</option>
            <option value="Oldest">الترتيب: الأقدم أولاً</option>
        </select>
        <select id="m"><option>Videos Only</option><option>Audio Only</option></select>
        <select id="q"><option value="360">الدقة: 360p (مستقر)</option><option value="720">الدقة: 720p (عالي)</option></select>
        <button onclick="start()">إطلاق الرادار الآن</button>
        <div class="bar"><div id="fill" class="fill"></div></div>
        <div id="log">الحالة: جاهز للعمل</div>
        <div id="st">المعالجة: 0 / 0</div>
    </div>
    <script>
        function start(){
            const d = {url:document.getElementById('u').value, folder:document.getElementById('f').value, engine:document.getElementById('e').value, sort:document.getElementById('s').value, mode:document.getElementById('m').value, quality:document.getElementById('q').value};
            fetch('/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
            setInterval(async () => {
                const r = await fetch('/status'); const j = await r.json();
                document.getElementById('log').innerText = j.log + " | " + j.current_file;
                document.getElementById('st').innerText = "اكتمل: " + j.total_done + " من " + j.total_count;
                if(j.total_count > 0) document.getElementById('fill').style.width = (j.total_done / j.total_count * 100) + "%";
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
