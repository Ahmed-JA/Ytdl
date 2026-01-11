import os, requests, json, threading, time
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

ENGINES = {
    "AK0": {"id": "9d4qz7zbqursfqv", "secret": "m26mrjxgbf8yk91", "refresh": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"},
    "AK-A": {"id": "04rtujs2ltsahxl", "secret": "xp07pg3mfffcwfv", "refresh": "MwbtuF28tIwAAAAAAAAAASK6Zg5B9FM49_7U2yMP7upJMRH_OpvTyQQOCx2cA8mV"}
}

RAW_COOKIES = """GPS=1;YSC=cRPU3pja-SY;VISITOR_INFO1_LIVE=20zT46tInss;VISITOR_PRIVACY_METADATA=CgJFRxIEGgAgQw%3D%3D;PREF=tz=Africa.Cairo&f5=30000&f7=100;__Secure-1PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;__Secure-3PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;HSID=AU_XHwPsXUSGUgZUq;SSID=AUtRaUQzpuXcGFlsb;APISID=GGcg9KjkJelNvooU/AvZNu9CDwwOGpuxn0;SAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-1PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-3PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;SID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_XpfS3nrxc6u1zRA46komJgACgYKAYwSARUSFQHGX2Mim9bkw294mS0juox0SqUHlRoVAUF8yKpxxgQ2GqF2sh645dKyGxGU0076;__Secure-1PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_Prv_jFBo8DGf7MvL3m3YUwACgYKAWASARUSFQHGX2MiB-68MTGXuISLXx-5gLyoNxoVAUF8yKqj5sYlM5mxOCH1yIqQpG3p0076;__Secure-3PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_tmt8C6WACoM_TRnt53rcYgACgYKAZISARUSFQHGX2Milx8SWGqPhNOfk0cfC1hrNxoVAUF8yKoXkn7Q5sDuY655VEVQaFfe0076;SIDCC=AKEyXzVZST_aZ3zfmWm76iXCt5WkVKq9lnm4wmc6XtSaPWSkIgqZgUahd0zWcjJo2X7kL06F;__Secure-1PSIDCC=AKEyXzWxG1jy4IhsbzuwTPJHLE1x0La-UZmvUdZ_PtAVsuCHgR0-jXuOiEUURvwMHdUzZ_Ug;__Secure-3PSIDCC=AKEyXzV4xjKO2m6EFIdi4eYuSRs-iiGiW3nWtahuqEOILqD_ZSph3Gd5-yyY-syAw-1NLEyv;LOGIN_INFO=AFmmF2swRQIhAPjDN9b05Pm08f9dnxS73Hh4-ZyPVQnMWMTdhqvhin-9AiBXsnlmvdi0CXO8n-gKF4DXUxmi6i0YrK1KIgtd9XjAOw:QUQ3MjNmeTlfbGZFdmtlZWdhVHNPWllWcGF0RkQxVjBMLVBxM2Y3ZEhBcTlBRWxuQ2xRX1BhUEo1UzU1WEoyMEtiVGpvN3J4NlZpRUg3QXB2WnJJU3JtTlNwalE1RnIyYzhSMzhMOUNRRGV1cnFRQVp5c0VBbWZoZ2RMd2gtZVVJdFBxajlmbXFFc2hYcjJoMmdEVVotRmRrdHhWVVRnQUdB;"""

# إحصائيات دقيقة
job_status = {"active": False, "current_file": "لا يوجد", "total_done": 0, "total_count": 0, "log": "في انتظار المهمة"}

def get_token(engine_name):
    try:
        e = ENGINES[engine_name]
        res = requests.post("https://api.dropboxapi.com/oauth2/token", data={"grant_type": "refresh_token", "refresh_token": e["refresh"], "client_id": e["id"], "client_secret": e["secret"]}, timeout=15)
        return res.json().get("access_token")
    except: return None

def youtube_worker(url, folder_name, mode, quality, sort_by, engine_name):
    global job_status
    token = get_token(engine_name)
    job_status.update({"active": True, "log": "🔍 جاري سحب بيانات القائمة...", "total_done": 0})
    
    # كتابة الكوكيز
    with open("cookies.txt", "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in RAW_COOKIES.split(';'):
            if '=' in cookie:
                k, v = cookie.strip().split('=', 1)
                f.write(f".youtube.com\tTRUE\t/\tTRUE\t2147483647\t{k}\t{v}\n")

    try:
        ydl_opts = {'cookiefile': 'cookies.txt', 'quiet': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url, download=False)
            videos = res.get('entries', [res])
            videos = [v for v in videos if v]

            if sort_by == "Most Viewed": videos.sort(key=lambda x: x.get('view_count') or 0, reverse=True)
            elif sort_by == "Newest": videos.sort(key=lambda x: x.get('upload_date') or '', reverse=True)
            elif sort_by == "Oldest": videos.sort(key=lambda x: x.get('upload_date') or '')

            job_status["total_count"] = len(videos)
            
        for i, video in enumerate(videos):
            v_url = video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}"
            v_title = video.get('title', 'Video')
            
            # تحديث الواجهة قبل البدء
            job_status.update({"current_file": v_title, "log": f"📡 جاري معالجة الملف رقم {i+1}"})

            targets = ["Audio"] if mode == "Audio Only" else (["Videos"] if mode == "Videos Only" else ["Audio", "Videos"])

            for m in targets:
                fmt = 'bestaudio/best' if m == "Audio" else f'best[height<={quality}][ext=mp4]/best'
                try:
                    with yt_dlp.YoutubeDL({'format': fmt, 'cookiefile': 'cookies.txt', 'quiet': True, 'noplaylist': True}) as ydl_s:
                        info = ydl_s.extract_info(v_url, download=False)
                        stream_url = info['url']
                        safe_title = "".join([c for c in v_title if c.isalnum() or c in " "]).strip()
                        filename = f"{(i+1):03d} - {safe_title}.{info.get('ext', 'mp4')}"

                        with requests.get(stream_url, stream=True, timeout=120) as r:
                            db_path = f"/خاص يوتيوب/{folder_name}/{m}/{filename}"
                            requests.post("https://content.dropboxapi.com/2/files/upload", 
                                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                                         "Dropbox-API-Arg": json.dumps({"path": db_path, "mode": "overwrite"})}, data=r.raw)
                except: continue
            
            # التحديث الفعلي فقط بعد اكتمال الرفع
            job_status["total_done"] = i + 1

        job_status.update({"log": "✅ اكتملت المهمة بالكامل", "active": False})
    except Exception as e:
        job_status.update({"log": f"⚠️ خطأ: {str(e)[:50]}", "active": False})

UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Koyeb Radar Pro v27</title>
    <style>
        body { background: #000; color: #0f0; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin:0; }
        .box { background: #111; padding: 30px; border-radius: 15px; border: 1px solid #0f0; width: 400px; text-align: center; }
        .bar { height: 15px; background: #222; border-radius: 10px; margin: 20px 0; overflow: hidden; }
        .fill { height: 100%; background: #0f0; width: 0%; transition: 0.3s; box-shadow: 0 0 10px #0f0; }
        input, select, button { width: 100%; padding: 10px; margin: 5px 0; border-radius: 5px; border: 1px solid #0f0; background: #000; color: #0f0; }
        #stats { font-size: 14px; margin-top: 10px; color: #fff; }
    </style>
</head>
<body>
    <div class="box">
        <h3>🛰️ رادار KOYEB v27</h3>
        <input id="u" placeholder="رابط يوتيوب">
        <input id="f" placeholder="اسم المجلد">
        <select id="e"><option value="AK0">محرك AK0</option><option value="AK-A">محرك AK-A</option></select>
        <select id="s"><option value="Default">الافتراضي</option><option value="Most Viewed">الأكثر مشاهدة</option><option value="Newest">الأحدث</option></select>
        <select id="m"><option>Audio Only</option><option>Videos Only</option><option>Both</option></select>
        <select id="q"><option value="360">360p</option><option value="720">720p</option></select>
        <button onclick="start()">إطلاق الرادار</button>
        <div class="bar"><div id="fill" class="fill"></div></div>
        <div id="log">الحالة: جاهز</div>
        <div id="stats">التقدم: 0 / 0</div>
        <div id="curr" style="font-size:11px; color:#888; margin-top:5px;"></div>
    </div>
    <script>
        function start(){
            const d = {url:document.getElementById('u').value, folder:document.getElementById('f').value, mode:document.getElementById('m').value, quality:document.getElementById('q').value, sort:document.getElementById('s').value, engine:document.getElementById('e').value};
            fetch('/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
            setInterval(async () => {
                const r = await fetch('/status'); const j = await r.json();
                document.getElementById('log').innerText = j.log;
                document.getElementById('stats').innerText = "تم إكمال: " + j.total_done + " من أصل " + j.total_count;
                document.getElementById('curr').innerText = "الحالي: " + j.current_file;
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
    threading.Thread(target=youtube_worker, args=(request.json['url'], request.json['folder'], request.json['mode'], request.json['quality'], request.json['sort'], request.json['engine'])).start()
    return jsonify({"ok": True})

@app.route('/status')
def get_status(): return jsonify(job_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
