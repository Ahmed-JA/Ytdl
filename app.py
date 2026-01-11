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

# الكوكيز الجديدة التي أرسلتها
RAW_COOKIES = """GPS=1;YSC=cRPU3pja-SY;VISITOR_INFO1_LIVE=20zT46tInss;VISITOR_PRIVACY_METADATA=CgJFRxIEGgAgQw%3D%3D;PREF=tz=Africa.Cairo&f5=30000&f7=100;__Secure-1PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;__Secure-3PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;HSID=AU_XHwPsXUSGUgZUq;SSID=AUtRaUQzpuXcGFlsb;APISID=GGcg9KjkJelNvooU/AvZNu9CDwwOGpuxn0;SAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-1PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-3PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;SID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_XpfS3nrxc6u1zRA46komJgACgYKAYwSARUSFQHGX2Mim9bkw294mS0juox0SqUHlRoVAUF8yKpxxgQ2GqF2sh645dKyGxGU0076;__Secure-1PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_Prv_jFBo8DGf7MvL3m3YUwACgYKAWASARUSFQHGX2MiB-68MTGXuISLXx-5gLyoNxoVAUF8yKqj5sYlM5mxOCH1yIqQpG3p0076;__Secure-3PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_tmt8C6WACoM_TRnt53rcYgACgYKAZISARUSFQHGX2Milx8SWGqPhNOfk0cfC1hrNxoVAUF8yKoXkn7Q5sDuY655VEVQaFfe0076;SIDCC=AKEyXzUytYQ4DZanBp0RRaZ0NAgAOLJ50yHIcFEz2MXoOv_LzBTxyZMvWLXt-M35vvAA4N-A;__Secure-1PSIDCC=AKEyXzXhU6LJKAri3dBWZkcCx2M3_HUntS_OHUwUkLBQYwIH2RA1EpNCGOjbtntbYqBTA4ur;__Secure-3PSIDCC=AKEyXzWzk43GaNloeUEZil5xX3tkNIOIaBS1ant_Be_hyHOhBcLincSU1ZSFMoqbkGY-XLZj;LOGIN_INFO=AFmmF2swRQIhAPjDN9b05Pm08f9dnxS73Hh4-ZyPVQnMWMTdhqvhin-9AiBXsnlmvdi0CXO8n-gKF4DXUxmi6i0YrK1KIgtd9XjAOw:QUQ3MjNmeTlfbGZFdmtlZWdhVHNPWllWcGF0RkQxVjBMLVBxM2Y3ZEhBcTlBRWxuQ2xRX1BhUEo1UzU1WEoyMEtiVGpvN3J4NlZpRUg3QXB2WnJJU3JtTlNwalE1RnIyYzhSMzhMOUNRRGV1cnFRQVp5c0VBbWZoZ2RMd2gtZVVJdFBxajlmbXFFc2hYcjJoMmdEVVotRmRrdHhWVVRnQUdB;ST-1533lks=csn=ks2V-ETXGiDneZd4&itct=CFgQ_FoYACITCOWSwOC6gpIDFZ0gBgAdnlUyZVoPRkVzdWJzY3JpcHRpb25zmgEHCLcBEPDwBcoBBNiFiEc%3D;"""

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
    job_status.update({"active": True, "log": "🔍 تحليل القائمة...", "total_done": 0})
    
    try:
        # إضافة ignoreerrors لتخطي الفيديوهات المحذوفة
        ydl_opts = {'cookiefile': 'cookies.txt', 'quiet': True, 'extract_flat': True, 'ignoreerrors': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url, download=False)
            if not res: raise Exception("لم يتم العثور على فيديوهات")
            videos = [v for v in res.get('entries', [res]) if v]

            if sort_by == "Most Viewed": videos.sort(key=lambda x: x.get('view_count') or 0, reverse=True)
            elif sort_by == "Newest": videos.sort(key=lambda x: x.get('upload_date') or '', reverse=True)
            elif sort_by == "Oldest": videos.sort(key=lambda x: x.get('upload_date') or '')

            job_status["total_count"] = len(videos)

        for i, video in enumerate(videos):
            try:
                token = get_token(engine_name)
                gc.collect() 
                
                v_url = video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}"
                v_title = "".join([c for c in video.get('title', 'Video') if c.isalnum() or c in " "]).strip()
                job_status.update({"current_file": v_title[:40], "log": f"📡 معالجة {i+1}"})

                if mode == "Audio Only": fmt = 'bestaudio/best'
                elif mode == "Both": fmt = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best'
                else: fmt = f'best[height<={quality}][ext=mp4]/best'
                
                with yt_dlp.YoutubeDL({'format': fmt, 'cookiefile': 'cookies.txt', 'quiet': True, 'noplaylist': True, 'ignoreerrors': True}) as ydl_s:
                    info = ydl_s.extract_info(v_url, download=False)
                    if not info: continue # تخطي إذا كان الفيديو غير متاح
                    
                    stream_url = info['url']
                    ext = info.get('ext', 'mp4')
                    filename = f"{(i+1):03d} - {v_title}.{ext}"

                    with requests.get(stream_url, stream=True, timeout=300) as r:
                        requests.post("https://content.dropboxapi.com/2/files/upload", 
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                                              "Dropbox-API-Arg": json.dumps({"path": f"/{folder_name}/{filename}", "mode": "overwrite"})}, 
                                     data=r.iter_content(chunk_size=1024*512))
                
                job_status["total_done"] = i + 1
                time.sleep(5)
            except Exception as e:
                print(f"فشل في معالجة فيديو: {e}")
                continue

        job_status.update({"log": "✅ المهمة انتهت", "active": False})
    except Exception as e:
        job_status.update({"log": f"⚠️ خطأ عام: {str(e)[:40]}", "active": False})

UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RADAR AK v33.4</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: sans-serif; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .box { background: #111; width: 92%; max-width: 450px; padding: 25px; border: 2px solid #00ff41; border-radius: 20px; }
        input, select, button { width: 100%; padding: 15px; margin: 8px 0; background: #000; color: #00ff41; border: 1px solid #00ff41; border-radius: 12px; font-size: 16px; box-sizing: border-box; }
        button { background: #00ff41; color: #000; font-weight: bold; cursor: pointer; border: none; }
        .bar-bg { height: 12px; background: #222; border-radius: 6px; overflow: hidden; margin: 15px 0; }
        .bar-fill { height: 100%; background: #00ff41; width: 0%; transition: 0.5s; }
        #log { text-align: center; font-size: 14px; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="text-align:center;">🛰️ رادار v33.4 Mapped</h2>
        <input id="u" placeholder="رابط يوتيوب">
        <input id="f" placeholder="المجلد في Dropbox">
        <select id="e">
            <option value="AK-A">المحرك AK-A</option>
            <option value="AK1">المحرك AK1</option>
        </select>
        <select id="m">
            <option value="Both">صوت وفيديو (Both)</option>
            <option value="Videos Only">فيديو فقط</option>
            <option value="Audio Only">صوت فقط</option>
        </select>
        <div style="display: flex; gap: 5px;">
            <select id="q"><option value="360">360p</option><option value="720">720p</option></select>
            <select id="s">
                <option value="Default">الترتيب الافتراضي</option>
                <option value="Most Viewed">الأكثر مشاهدة</option>
                <option value="Newest">الأحدث</option>
            </select>
        </div>
        <button onclick="start()">بدء التشغيل 🚀</button>
        <div class="bar-bg"><div id="fill" class="bar-fill"></div></div>
        <div id="log">الحالة: جاهز</div>
        <div id="stats" style="text-align:center; font-size:12px; margin-top:5px;"></div>
    </div>
    <script>
        function start(){
            const d = {url:document.getElementById('u').value, folder:document.getElementById('f').value, engine:document.getElementById('e').value, sort:document.getElementById('s').value, mode:document.getElementById('m').value, quality:document.getElementById('q').value};
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
