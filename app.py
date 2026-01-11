import os, requests, json, threading, time, gc
from flask import Flask, render_template_string, request, jsonify
import yt_dlp
from datetime import timedelta

app = Flask(__name__)

# --- قاعدة بيانات المحركات ---
def get_engines():
    return {
        "AK-A": {"id": "84031qa6rhfihqe", "secret": "pyoh81kjttomk7b", "ref": "3rGVqjd0T1IAAAAAAAAAAYsivkeMJpEjqt2jPzNFM_Y3ETQBojCGeXadZIMjyFg8"},
        "AK1": {"id": "9d4qz7zbqursfqv", "secret": "m26mrjxgbf8yk91", "ref": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"},
        "AK-C": {"id": "04rtujs2ltsahxl", "secret": "xp07pg3mfffcwfv", "ref": "MwbtuF28tIwAAAAAAAAAASK6Zg5B9FM49_7U2yMP7upJMRH_OpvTyQQOCx2cA8mV"},
        "AK-D": {"id": "qa1up01sxbr2tv2", "secret": "icohwsmum1j72dp", "ref": "SOKxQedqSeAAAAAAAAAAAajcvKhRjCRLOZpuyIRq7drbR0YFmRRBCvgStcKXjwY_"}
    }

RAW_COOKIES = """GPS=1;YSC=cRPU3pja-SY;VISITOR_INFO1_LIVE=20zT46tInss;VISITOR_PRIVACY_METADATA=CgJFRxIEGgAgQw%3D%3D;PREF=tz=Africa.Cairo&f5=30000&f7=100;__Secure-1PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;__Secure-3PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;HSID=AU_XHwPsXUSGUgZUq;SSID=AUtRaUQzpuXcGFlsb;APISID=GGcg9KjkJelNvooU/AvZNu9CDwwOGpuxn0;SAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-1PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-3PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;SID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_XpfS3nrxc6u1zRA46komJgACgYKAYwSARUSFQHGX2Mim9bkw294mS0juox0SqUHlRoVAUF8yKpxxgQ2GqF2sh645dKyGxGU0076;__Secure-1PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_Prv_jFBo8DGf7MvL3m3YUwACgYKAWASARUSFQHGX2MiB-68MTGXuISLXx-5gLyoNxoVAUF8yKqj5sYlM5mxOCH1yIqQpG3p0076;__Secure-3PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_tmt8C6WACoM_TRnt53rcYgACgYKAZISARUSFQHGX2Milx8SWGqPhNOfk0cfC1hrNxoVAUF8yKoXkn7Q5sDuY655VEVQaFfe0076;SIDCC=AKEyXzUytYQ4DZanBp0RRaZ0NAgAOLJ50yHIcFEz2MXoOv_LzBTxyZMvWLXt-M35vvAA4N-A;__Secure-1PSIDCC=AKEyXzXhU6LJKAri3dBWZkcCx2M3_HUntS_OHUwUkLBQYwIH2RA1EpNCGOjbtntbYqBTA4ur;__Secure-3PSIDCC=AKEyXzWzk43GaNloeUEZil5xX3tkNIOIaBS1ant_Be_hyHOhBcLincSU1ZSFMoqbkGY-XLZj;LOGIN_INFO=AFmmF2swRQIhAPjDN9b05Pm08f9dnxS73Hh4-ZyPVQnMWMTdhqvhin-9AiBXsnlmvdi0CXO8n-gKF4DXUxmi6i0YrK1KIgtd9XjAOw:QUQ3MjNmeTlfbGZFdmtlZWdhVHNPWllWcGF0RkQxVjBMLVBxM2Y3ZEhBcTlBRWxuQ2xRX1BhUEo1UzU1WEoyMEtiVGpvN3J4NlZpRUg3QXB2WnJJU3JtTlNwalE1RnIyYzhSMzhMOUNRRGV1cnFRQVp5c0VBbWZoZ2RMd2gtZVVJdFBxajlmbXFFc2hYcjJoMmdEVVotRmRrdHhWVVRnQUdB;ST-1533lks=csn=ks2V-ETXGiDneZd4&itct=CFgQ_FoYACITCOWSwOC6gpIDFZ0gBgAdnlUyZVoPRkVzdWJzY3JpcHRpb25zmgEHCLcBEPDwBcoBBNiFiEc%3D;"""

# إحصائيات الجلسة
job_stats = {
    "active": False, "log": "جاهز", "current_file": "-",
    "total_done": 0, "total_count": 0, "skipped": 0,
    "start_time": 0, "eta": "00:00:00", "elapsed": "00:00:00"
}

def get_token(engine_name):
    e = get_engines()[engine_name]
    try:
        res = requests.post("https://api.dropboxapi.com/oauth2/token", 
                            data={"grant_type": "refresh_token", "refresh_token": e["ref"], "client_id": e["id"], "client_secret": e["secret"]}, timeout=15)
        return res.json().get("access_token")
    except: return None

def check_exists_on_cloud(token, remote, folder, sub, filename):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    full_path = f"/{remote}/{folder}/{sub}/{filename}".replace("//", "/")
    try:
        res = requests.post("https://api.dropboxapi.com/2/files/get_metadata", headers=headers, json={"path": full_path})
        return res.status_code == 200
    except: return False

def youtube_worker(url, remote, folder, mode, quality, sort, engine):
    global job_stats
    job_stats.update({"active": True, "log": "🔍 تحليل البيانات...", "total_done": 0, "skipped": 0, "start_time": time.time()})
    
    try:
        ydl_opts = {'cookiefile': 'cookies.txt', 'quiet': True, 'extract_flat': True, 'ignoreerrors': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url, download=False)
            videos = [v for v in res.get('entries', [res]) if v]
            
            if "Most Viewed" in sort: videos.sort(key=lambda x: x.get('view_count') or 0, reverse=True)
            elif "Newest" in sort: videos.sort(key=lambda x: x.get('upload_date') or '', reverse=True)
            elif "Oldest" in sort: videos.sort(key=lambda x: x.get('upload_date') or '')
            
            job_stats["total_count"] = len(videos)

        for i, video in enumerate(videos):
            token = get_token(engine)
            
            # تحديث الوقت والإحصاءات
            processed = i + 1
            elapsed = time.time() - job_stats["start_time"]
            avg_time = elapsed / processed if processed > 0 else 0
            remaining = avg_time * (len(videos) - processed)
            
            job_stats["elapsed"] = str(timedelta(seconds=int(elapsed)))
            job_stats["eta"] = str(timedelta(seconds=int(remaining)))

            v_title = "".join([c for c in video.get('title', 'Video') if c.isalnum() or c in " "]).strip()
            
            if mode == "Audio Only": sub, fmt, ext = "Audio", 'bestaudio/best', 'mp3'
            else: sub, fmt, ext = "Videos", f'bestvideo[height<={quality}]+bestaudio/best' if mode == "Both" else f'best[height<={quality}][ext=mp4]/best', 'mp4'

            filename = f"{processed:03d} - {v_title}.{ext}"

            if check_exists_on_cloud(token, remote, folder, sub, filename):
                job_stats["skipped"] += 1
                job_stats["total_done"] = processed
                continue

            job_stats.update({"current_file": v_title[:35], "log": f"📡 معالجة {processed}"})

            with yt_dlp.YoutubeDL({'format': fmt, 'cookiefile': 'cookies.txt', 'quiet': True, 'noplaylist': True}) as ydl_s:
                info = ydl_s.extract_info(video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}", download=False)
                upload_path = f"/{remote}/{folder}/{sub}/{filename}".replace("//", "/")
                with requests.get(info['url'], stream=True, timeout=600) as r:
                    requests.post("https://content.dropboxapi.com/2/files/upload", 
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                                          "Dropbox-API-Arg": json.dumps({"path": upload_path, "mode": "overwrite"})}, 
                                 data=r.iter_content(chunk_size=1024*512))
            
            job_stats["total_done"] = processed
            time.sleep(3)

        job_stats.update({"log": "✅ اكتمل العمل", "active": False})
    except Exception as e:
        job_stats.update({"log": f"⚠️ خطأ: {str(e)[:20]}", "active": False})

UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RADAR LIVE STATS</title>
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 15px; }
        .container { max-width: 500px; margin: auto; border: 1px solid #0f0; padding: 20px; border-radius: 10px; }
        .stat-line { display: flex; justify-content: space-between; margin: 10px 0; border-bottom: 1px dashed #050; padding-bottom: 5px; }
        .bar-container { background: #111; height: 15px; border: 1px solid #0f0; margin: 15px 0; border-radius: 5px; overflow: hidden; }
        #bar { background: #0f0; height: 100%; width: 0%; transition: 0.5s; }
        input, select, button { width: 100%; padding: 12px; margin: 5px 0; background: #000; color: #0f0; border: 1px solid #0f0; }
        button { background: #0f0; color: #000; font-weight: bold; cursor: pointer; }
        .live-label { color: #fff; font-size: 13px; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="text-align:center">📊 لوحة التحكم والإحصاءات</h2>
        <input id="rd" placeholder="المسار (خاص يوتيوب)" value="خاص يوتيوب">
        <input id="mf" placeholder="المجلد الرئيسي">
        <input id="u" placeholder="رابط يوتيوب">
        <select id="e"><option value="AK-A">AK-A</option><option value="AK1">AK1</option></select>
        <select id="m"><option value="Audio Only">صوت</option><option value="Both">فيديو+صوت</option></select>
        <button onclick="start()">بدء التشغيل 🚀</button>

        <div class="bar-container"><div id="bar"></div></div>
        
        <div id="stats_panel">
            <div class="stat-line"><span class="live-label">الحالة:</span> <span id="log">انتظار...</span></div>
            <div class="stat-line"><span class="live-label">التقدم:</span> <span id="progress">0/0</span></div>
            <div class="stat-line"><span class="live-label">تخطي (موجود):</span> <span id="skip">0</span></div>
            <div class="stat-line"><span class="live-label">الوقت المنقضي:</span> <span id="elapsed">00:00:00</span></div>
            <div class="stat-line"><span class="live-label">الوقت المتبقي (ETA):</span> <span id="eta">00:00:00</span></div>
            <div class="stat-line"><span class="live-label">الملف الحالي:</span> <span id="curr">-</span></div>
        </div>
    </div>
    <script>
        function start(){
            const d = {url:document.getElementById('u').value, remote:document.getElementById('rd').value, folder:document.getElementById('mf').value, engine:document.getElementById('e').value, sort:'Most Viewed', mode:document.getElementById('m').value, quality:'360'};
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
    threading.Thread(target=youtube_worker, args=(d['url'], d['remote'], d['folder'], d['mode'], d['quality'], d['sort'], d['engine'])).start()
    return jsonify({"ok": True})

@app.route('/status')
def get_status(): return jsonify(job_stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
