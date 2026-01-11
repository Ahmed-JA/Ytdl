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

# 🍪 الكوكيز المحدثة
RAW_COOKIES = """GPS=1;VISITOR_INFO1_LIVE=20zT46tInss;VISITOR_PRIVACY_METADATA=CgJFRxIEGgAgQw%3D%3D;PREF=tz=Africa.Cairo&f5=30000&f7=100;__Secure-1PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;__Secure-3PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;HSID=AU_XHwPsXUSGUgZUq;SSID=AUtRaUQzpuXcGFlsb;APISID=GGcg9KjkJelNvooU/AvZNu9CDwwOGpuxn0;SAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-1PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-3PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;SID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_XpfS3nrxc6u1zRA46komJgACgYKAYwSARUSFQHGX2Mim9bkw294mS0juox0SqUHlRoVAUF8yKpxxgQ2GqF2sh645dKyGxGU0076;__Secure-1PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_Prv_jFBo8DGf7MvL3m3YUwACgYKAWASARUSFQHGX2MiB-68MTGXuISLXx-5gLyoNxoVAUF8yKqj5sYlM5mxOCH1yIqQpG3p0076;__Secure-3PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_tmt8C6WACoM_TRnt53rcYgACgYKAZISARUSFQHGX2Milx8SWGqPhNOfk0cfC1hrNxoVAUF8yKoXkn7Q5sDuY655VEVQaFfe0076;SIDCC=AKEyXzUSQceCk1CdS598w7mWtZwyyWWZbC4xBRcd5_RS2iwZOiRzWUUopSmyXV0hLKmSQib_;__Secure-1PSIDCC=AKEyXzV8JWRqC3pzgLj8S-FJ8k4pwLGH_r8Vh_1qAbHlgZsnyjdDV6g98WjdrVXSHBhHu_05;__Secure-3PSIDCC=AKEyXzWF6u_Z2BYYZJ60kfR1VgBw876AgTKX_xWwLU8HyxWx3avbdJr2lCZDB3ekqfLh2scD;LOGIN_INFO=AFmmF2swRQIhAPjDN9b05Pm08f9dnxS73Hh4-ZyPVQnMWMTdhqvhin-9AiBXsnlmvdi0CXO8n-gKF4DXUxmi6i0YrK1KIgtd9XjAOw:QUQ3MjNmeTlfbGZFdmtlZWdhVHNPWllWcGF0RkQxVjBMLVBxM2Y3ZEhBcTlBRWxuQ2xRX1BhUEo1UzU1WEoyMEtiVGpvN3J4NlZpRUg3QXB2WnJJU3JtTlNwalE1RnIyYzhSMzhMOUNRRGV1cnFRQVp5c0VBbWZoZ2RMd2gtZVVJdFBxajlmbXFFc2hYcjJoMmdEVVotRmRrdHhWVVRnQUdB;ST-1533lks=csn=ks2V-ETXGiDneZd4&itct=CFgQ_FoYACITCOWSwOC6gpIDFZ0gBgAdnlUyZVoPRkVzdWJzY3JpcHRpb25zmgEHCLcBEPDwBcoBBNiFiEc%3D;YSC=p7yhbIibUcs;ST-bo17fp=csn=PfplkiWdhTkluk3Y&itct=CB4Q_FoYACITCO2x7JTHgpIDFRQzBgAdxTMmvloPRkVzdWJzY3JpcHRpb25zmgEHCLcBEPDwBcoBBNiFiEc%3D;ST-1vnw0la=csn=PfplkiWdhTkluk3Y&itct=CFgQh_YEGAEiEwjtseyUx4KSAxUUMwYAHcUzJr5aD0ZFc3Vic2NyaXB0aW9uc5oBBggkEPDwBcoBBNiFiEc%3D;CONSISTENCY=APeVyi-adrh6xjJBS6yOKDX8AhR0TPK0rngRHnyj7oJMBJSvD7IfLnKRRhXHz2oImQwh4u7olm-zHO4DKbtdF2cviOapUUZuLjBDaHWrg0yye0mKdwWw1i_U1v4;"""

job_stats = {"active": False, "log": "جاهز", "current_file": "-", "total_done": 0, "total_count": 0, "skipped": 0, "start_time": 0, "eta": "00:00:00", "elapsed": "00:00:00"}

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
    job_stats.update({"active": True, "log": "🔍 تحليل القناة...", "total_done": 0, "skipped": 0, "start_time": time.time()})
    
    try:
        ydl_opts = {'cookiefile': 'cookies.txt', 'quiet': True, 'extract_flat': True, 'ignoreerrors': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url, download=False)
            videos = [v for v in res.get('entries', [res]) if v]

            # نظام الفرز المطور
            if sort_by == "Most Viewed": videos.sort(key=lambda x: x.get('view_count') or 0, reverse=True)
            elif sort_by == "Newest": videos.sort(key=lambda x: x.get('upload_date') or '', reverse=True)
            elif sort_by == "Oldest": videos.sort(key=lambda x: x.get('upload_date') or '')
            elif sort_by == "Rating": videos.sort(key=lambda x: x.get('like_count') or 0, reverse=True)
            elif sort_by == "Popular": # الأكثر ترويجاً (مزيج من المشاهدات والتفاعل)
                videos.sort(key=lambda x: (x.get('view_count') or 0) + (x.get('like_count') or 0) * 10, reverse=True)

            job_stats["total_count"] = len(videos)

        for i, video in enumerate(videos):
            token = get_token(engine_name)
            v_url = video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}"
            v_title = "".join([c for c in video.get('title', 'Video') if c.isalnum() or c in " "]).strip()
            
            processed = i + 1
            # حساب الوقت
            elapsed_sec = time.time() - job_stats["start_time"]
            avg_time = elapsed_sec / processed
            rem_sec = avg_time * (len(videos) - processed)
            job_stats["elapsed"] = str(timedelta(seconds=int(elapsed_sec)))
            job_stats["eta"] = str(timedelta(seconds=int(rem_sec)))

            tasks = []
            if mode in ["Audio Only", "Both"]: tasks.append(("Audio", "bestaudio/best", "mp3"))
            if mode in ["Videos Only", "Both"]: tasks.append(("Videos", f"bestvideo[height<={quality}]+bestaudio/best", "mp4"))

            for sub, fmt, ext in tasks:
                filename = f"{processed:03d} - {v_title}.{ext}"
                full_path = f"/{folder_name}/{sub}/{filename}"

                if check_exists(token, full_path):
                    job_stats["skipped"] += 1
                    continue

                job_stats.update({"current_file": f"[{sub}] {v_title[:20]}", "log": f"📡 معالجة {processed}"})
                
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

        job_stats.update({"log": "✅ اكتملت المهمة", "active": False})
    except Exception as e:
        job_stats.update({"log": f"⚠️ خطأ: {str(e)[:30]}", "active": False})

UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RADAR PRO v34.5</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; }
        .box { background: #111; max-width: 500px; margin: auto; padding: 25px; border: 2px solid #00ff41; border-radius: 20px; box-shadow: 0 0 20px rgba(0,255,65,0.2); }
        input, select, button { width: 100%; padding: 12px; margin: 8px 0; background: #000; color: #00ff41; border: 1px solid #333; border-radius: 10px; font-size: 14px; }
        button { background: #00ff41; color: #000; font-weight: bold; cursor: pointer; border: none; }
        .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; font-size: 12px; border-top: 1px solid #222; padding-top: 10px; }
        .bar { height: 10px; background: #222; border-radius: 5px; overflow: hidden; margin: 10px 0; }
        #fill { height: 100%; background: #00ff41; width: 0%; transition: 0.5s; }
        .label { color: #888; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="text-align:center; color:#fff;">🛰️ رادار برو v34.5</h2>
        <input id="u" placeholder="رابط القناة أو الفيديو">
        <input id="f" placeholder="اسم المجلد الرئيسي">
        <div style="display:flex; gap:10px;">
            <select id="m">
                <option value="Both">صوت + فيديو (Both)</option>
                <option value="Audio Only">صوت فقط</option>
                <option value="Videos Only">فيديو فقط</option>
            </select>
            <select id="q">
                <option value="144">144p</option>
                <option value="240">240p</option>
                <option value="360" selected>360p</option>
                <option value="480">480p</option>
                <option value="720">720p HD</option>
                <option value="1080">1080p FHD</option>
                <option value="1440">2K Quality</option>
                <option value="2160">4K Ultra HD</option>
            </select>
        </div>
        <select id="s">
            <option value="Popular">الأكثر ترويجاً 🔥</option>
            <option value="Most Viewed">الأكثر مشاهدة</option>
            <option value="Rating">الأعلى تقييماً</option>
            <option value="Newest">الأحدث</option>
            <option value="Oldest">الأقدم</option>
        </select>
        <button onclick="start()">بدء التشغيل 🚀</button>
        
        <div class="bar"><div id="fill"></div></div>
        <div id="log" style="text-align:center; font-size:14px;">جاهز</div>
        
        <div class="stat-grid">
            <div><span class="label">التقدم:</span> <span id="prog">0/0</span></div>
            <div><span class="label">تخطي:</span> <span id="skip">0</span></div>
            <div><span class="label">المنقضي:</span> <span id="elap">00:00:00</span></div>
            <div><span class="label">المتبقي:</span> <span id="eta">00:00:00</span></div>
        </div>
        <div style="text-align:center; font-size:11px; margin-top:10px; color:#555;" id="curr">-</div>
    </div>
    <script>
        function start(){
            const d = {url:document.getElementById('u').value, folder:document.getElementById('f').value, engine:'AK-A', sort:document.getElementById('s').value, mode:document.getElementById('m').value, quality:document.getElementById('q').value};
            fetch('/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
            setInterval(async () => {
                const r = await fetch('/status'); const j = await r.json();
                document.getElementById('log').innerText = j.log;
                document.getElementById('prog').innerText = j.total_done + " / " + j.total_count;
                document.getElementById('skip').innerText = j.skipped;
                document.getElementById('elap').innerText = j.elapsed;
                document.getElementById('eta').innerText = j.eta;
                document.getElementById('curr').innerText = j.current_file;
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
    threading.Thread(target=youtube_worker, args=(d['url'], d['folder'], d['mode'], d['quality'], d['sort'], 'AK-A')).start()
    return jsonify({"ok": True})

@app.route('/status')
def get_status(): return jsonify(job_stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
