import os, requests, json, threading, time
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# --- الإعدادات (نفس بيانات دروب بوكس الخاصة بك) ---
DROPBOX_CRED = {
    "id": "9d4qz7zbqursfqv",
    "secret": "m26mrjxgbf8yk91",
    "refresh": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"
}

# الكوكيز الجديدة التي أرسلتها (للقاهرة)
RAW_COOKIES = """GPS=1;YSC=cRPU3pja-SY;VISITOR_INFO1_LIVE=20zT46tInss;VISITOR_PRIVACY_METADATA=CgJFRxIEGgAgQw%3D%3D;PREF=tz=Africa.Cairo&f5=30000&f7=100;__Secure-1PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;__Secure-3PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;HSID=AU_XHwPsXUSGUgZUq;SSID=AUtRaUQzpuXcGFlsb;APISID=GGcg9KjkJelNvooU/AvZNu9CDwwOGpuxn0;SAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-1PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-3PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;SID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_XpfS3nrxc6u1zRA46komJgACgYKAYwSARUSFQHGX2Mim9bkw294mS0juox0SqUHlRoVAUF8yKpxxgQ2GqF2sh645dKyGxGU0076;__Secure-1PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_Prv_jFBo8DGf7MvL3m3YUwACgYKAWASARUSFQHGX2MiB-68MTGXuISLXx-5gLyoNxoVAUF8yKqj5sYlM5mxOCH1yIqQpG3p0076;__Secure-3PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_tmt8C6WACoM_TRnt53rcYgACgYKAZISARUSFQHGX2Milx8SWGqPhNOfk0cfC1hrNxoVAUF8yKoXkn7Q5sDuY655VEVQaFfe0076;SIDCC=AKEyXzVZST_aZ3zfmWm76iXCt5WkVKq9lnm4wmc6XtSaPWSkIgqZgUahd0zWcjJo2X7kL06F;__Secure-1PSIDCC=AKEyXzWxG1jy4IhsbzuwTPJHLE1x0La-UZmvUdZ_PtAVsuCHgR0-jXuOiEUURvwMHdUzZ_Ug;__Secure-3PSIDCC=AKEyXzV4xjKO2m6EFIdi4eYuSRs-iiGiW3nWtahuqEOILqD_ZSph3Gd5-yyY-syAw-1NLEyv;LOGIN_INFO=AFmmF2swRQIhAPjDN9b05Pm08f9dnxS73Hh4-ZyPVQnMWMTdhqvhin-9AiBXsnlmvdi0CXO8n-gKF4DXUxmi6i0YrK1KIgtd9XjAOw:QUQ3MjNmeTlfbGZFdmtlZWdhVHNPWllWcGF0RkQxVjBMLVBxM2Y3ZEhBcTlBRWxuQ2xRX1BhUEo1UzU1WEoyMEtiVGpvN3J4NlZpRUg3QXB2WnJJU3JtTlNwalE1RnIyYzhSMzhMOUNRRGV1cnFRQVp5c0VBbWZoZ2RMd2gtZVVJdFBxajlmbXFFc2hYcjJoMmdEVVotRmRrdHhWVVRnQUdB;"""

job_status = {"active": False, "current_file": "", "total_done": 0, "total_count": 0, "log": "جاهز"}

def create_cookie_file():
    c_path = os.path.join(os.getcwd(), "cookies.txt")
    with open(c_path, "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in RAW_COOKIES.split(';'):
            if '=' in cookie:
                k, v = cookie.strip().split('=', 1)
                f.write(f".youtube.com\tTRUE\t/\tTRUE\t2147483647\t{k}\t{v}\n")
    return c_path

def get_token():
    try:
        res = requests.post("https://api.dropboxapi.com/oauth2/token", data={
            "grant_type": "refresh_token", "refresh_token": DROPBOX_CRED["refresh"],
            "client_id": DROPBOX_CRED["id"], "client_secret": DROPBOX_CRED["secret"]}, timeout=10)
        return res.json().get("access_token")
    except: return None

def youtube_worker(url, folder_name, mode, quality):
    global job_status
    token = get_token()
    c_path = create_cookie_file()
    job_status.update({"active": True, "log": "🔍 جاري تحليل الرابط والقائمة...", "total_done": 0, "total_count": 0})
    
    ydl_opts_info = {
        'cookiefile': c_path,
        'extract_flat': True,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            result = ydl.extract_info(url, download=False)
            if 'entries' in result:
                videos = result['entries']
            else:
                videos = [result]
            
            job_status["total_count"] = len(videos)
            
        for i, video in enumerate(videos):
            video_url = video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}"
            video_title = video.get('title', 'Unknown Title')
            job_status.update({"current_file": video_title, "total_done": i, "log": f"📥 معالجة {i+1} من {len(videos)}"})

            # تحديد الصيغ المطلوبة
            targets = []
            if mode == "Audio Only": targets = ["Audio"]
            elif mode == "Videos Only": targets = ["Videos"]
            else: targets = ["Audio", "Videos"]

            for m in targets:
                job_status["log"] = f"📡 سحب رابط {m}..."
                # إعدادات السحب المباشر (Streaming) لتوفير مساحة Koyeb
                stream_opts = {
                    'format': 'bestaudio/best' if m == "Audio" else f'bestvideo[height<={quality}]+bestaudio/best',
                    'cookiefile': c_path,
                    'user_agent': ydl_opts_info['user_agent'],
                    'quiet': True
                }
                
                with yt_dlp.YoutubeDL(stream_opts) as ydl_stream:
                    info = ydl_stream.extract_info(video_url, download=False)
                    final_url = info['url']
                    ext = info.get('ext', 'mp3' if m == "Audio" else 'mp4')
                    safe_title = "".join([c for c in video_title if c.isalnum() or c in " "]).strip()
                    filename = f"{(i+1):03d} - {safe_title}.{ext}"

                    # النقل المباشر لدروب بوكس
                    with requests.get(final_url, stream=True) as r:
                        r.raise_for_status()
                        db_path = f"/خاص يوتيوب/{folder_name}/{m}/{filename}"
                        requests.post("https://content.dropboxapi.com/2/files/upload", 
                            headers={"Authorization": f"Bearer {token}",
                                     "Dropbox-API-Arg": json.dumps({"path": db_path, "mode": "overwrite"}),
                                     "Content-Type": "application/octet-stream"}, data=r.raw)

        job_status.update({"total_done": len(videos), "log": "✅ اكتملت المهمة بنجاح!", "active": False})
    except Exception as e:
        job_status.update({"log": f"⚠️ خطأ: {str(e)[:50]}", "active": False})

# --- واجهة المستخدم المطورة لـ Koyeb ---
UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Koyeb Radar Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo&display=swap" rel="stylesheet">
    <style>
        body { background: #000; color: #0f0; font-family: 'Cairo'; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .box { width: 90%; max-width: 450px; background: #0a0a0a; padding: 30px; border-radius: 15px; border: 1px solid #0f0; box-shadow: 0 0 20px #0f03; }
        input, select, button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #0f0; background: #000; color: #0f0; }
        button { background: #0f0; color: #000; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background: #0a0; }
        .bar { height: 10px; background: #111; border-radius: 5px; margin: 15px 0; overflow: hidden; border: 1px solid #0f02; }
        .fill { height: 100%; background: #0f0; width: 0%; transition: 0.5s; box-shadow: 0 0 10px #0f0; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="text-align:center;">☢️ KOYEB RADAR PRO</h2>
        <input id="url" placeholder="رابط فيديو أو قائمة تشغيل">
        <input id="folder" placeholder="اسم المجلد في Dropbox">
        <select id="mode"><option>Audio Only</option><option>Videos Only</option><option>Both</option></select>
        <select id="quality"><option value="360">360p</option><option value="480">480p</option><option value="720">720p</option></select>
        <button id="btn" onclick="start()">إطلاق المهمة</button>
        <div id="log" style="font-size:14px; margin-top:15px;">الحالة: جاهز</div>
        <div id="file" style="font-size:11px; color:#888; margin-top:5px; height:15px; overflow:hidden;"></div>
        <div class="bar"><div id="fill" class="fill"></div></div>
    </div>
    <script>
        function start() {
            const data = { url: document.getElementById('url').value, folder: document.getElementById('folder').value, mode: document.getElementById('mode').value, quality: document.getElementById('quality').value };
            fetch('/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
            poll();
        }
        async function poll() {
            const res = await fetch('/status'); const d = await res.json();
            document.getElementById('log').innerText = "الحالة: " + d.log;
            document.getElementById('file').innerText = d.current_file;
            if(d.total_count > 0) document.getElementById('fill').style.width = (d.total_done / d.total_count * 100) + "%";
            if(d.active) setTimeout(poll, 2000);
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
    threading.Thread(target=youtube_worker, args=(d['url'], d['folder'], d['mode'], d['quality'])).start()
    return jsonify({"status": "started"})

@app.route('/status')
def get_status(): return jsonify(job_status)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
