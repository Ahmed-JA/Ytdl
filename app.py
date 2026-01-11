غير مهم الان اريد ان يدعم هذا الكود روابط القنوات مباشرة
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

# 🍪 ملاحظة: تأكد من تحديث الكوكيز إذا واجهت مشاكل في الوصول
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
    e = get_engines().get(engine_name)
    if not e: return None
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

            if sort_by == "Most Viewed": videos.sort(key=lambda x: x.get('view_count') or 0, reverse=True)
            elif sort_by == "Newest": videos.sort(key=lambda x: x.get('upload_date') or '', reverse=True)
            elif sort_by == "Oldest": videos.sort(key=lambda x: x.get('upload_date') or '')
            elif sort_by == "Rating": videos.sort(key=lambda x: x.get('like_count') or 0, reverse=True)
            elif sort_by == "Popular":
                videos.sort(key=lambda x: (x.get('view_count') or 0) + (x.get('like_count') or 0) * 10, reverse=True)

            job_stats["total_count"] = len(videos)

        for i, video in enumerate(videos):
            token = get_token(engine_name)
            v_url = video.get('url') or f"https://www.youtube.com/watch?v={video.get('id')}"
            v_title = "".join([c for c in video.get('title', 'Video') if c.isalnum() or c in " "]).strip()
            
            processed = i + 1
            elapsed_sec = time.time() - job_stats["start_time"]
            avg_time = elapsed_sec / processed if processed > 0 else 0
            rem_sec = avg_time * (len(videos) - processed)
            job_stats["elapsed"] = str(timedelta(seconds=int(elapsed_sec)))
            job_stats["eta"] = str(timedelta(seconds=int(rem_sec)))

            tasks = []
            if mode in ["Audio Only", "Both"]: tasks.append(("Audio", "bestaudio/best", "mp3"))
            # تم تعديل الصيغة هنا لضمان وجود الصوت والفيديو معاً لتلافي الملفات التي لا تعمل
            if mode in ["Videos Only", "Both"]: tasks.append(("Videos", f"best[height<={quality}][ext=mp4]/best[ext=mp4]/best", "mp4"))

            for sub, fmt, ext in tasks:
                filename = f"{processed:03d} - {v_title}.{ext}"
                # تم إضافة 'خاص يوتيوب' كمسار أب ثابت هنا
                full_path = f"/خاص يوتيوب/{folder_name}/{sub}/{filename}"

                if check_exists(token, full_path):
                    job_stats["skipped"] += 1
                    continue

                job_stats.update({"current_file": f"[{sub}] {v_title[:20]}", "log": f"📡 محرك {engine_name} ينقل {processed}"})
                
                try:
                    with yt_dlp.YoutubeDL({'format': fmt, 'cookiefile': 'cookies.txt', 'quiet': True, 'noplaylist': True}) as ydl_s:
                        info = ydl_s.extract_info(v_url, download=False)
                        if not info or 'url' not in info: continue
                        
                        # إضافة User-Agent لضمان قبول الطلب من خوادم يوتيوب
                        headers_download = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                        
                        with requests.get(info['url'], stream=True, headers=headers_download, timeout=300) as r:
                            r.raise_for_status()
                            requests.post("https://content.dropboxapi.com/2/files/upload", 
                                         headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                                                  "Dropbox-API-Arg": json.dumps({"path": full_path, "mode": "overwrite"})}, 
                                         data=r.iter_content(chunk_size=1024*1024))
                except:
                    continue
            
            job_stats["total_done"] = processed
            gc.collect()

        job_stats.update({"log": "✅ اكتمل العمل بنجاح", "active": False})
    except Exception as e:
        job_stats.update({"log": f"⚠️ خطأ: {str(e)[:30]}", "active": False})

UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RADAR AK PRO v35.6</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 15px; }
        .box { max-width: 500px; margin: auto; border: 1px solid #0f0; padding: 20px; border-radius: 15px; background: #050505; box-shadow: 0 0 20px #0f02; }
        input, select, button { width: 100%; padding: 12px; margin: 6px 0; background: #000; color: #0f0; border: 1px solid #0f0; border-radius: 10px; font-size: 14px; box-sizing: border-box; }
        button { background: #0f0; color: #000; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background: #0c0; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
        .bar { background: #111; height: 12px; border: 1px solid #0f0; margin: 15px 0; border-radius: 6px; overflow: hidden; }
        #fill { background: #0f0; height: 100%; width: 0%; transition: 0.5s; }
        .stat { display: flex; justify-content: space-between; font-size: 13px; border-bottom: 1px solid #020; padding: 5px 0; }
        .label { color: #888; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="text-align:center; margin-bottom:20px;">🛰️ رادار v35.6 - خاص يوتيوب</h2>
        <input id="u" placeholder="رابط القناة أو القائمة">
        <input id="f" placeholder="اسم المجلد (سيتم إنشاؤه داخل 'خاص يوتيوب')">
        <div class="grid">
            <select id="e">
                <option value="AK-A">المحرك AK-A</option>
                <option value="AK1">المحرك AK1</option>
            </select>
            <select id="m">
                <option value="Both">صوت + فيديو (Both)</option>
                <option value="Audio Only">صوت فقط</option>
                <option value="Videos Only">فيديو فقط</option>
            </select>
        </div>
        <div class="grid">
            <select id="q">
                <option value="144">144p</option>
                <option value="360" selected>360p</option>
                <option value="720">720p HD</option>
                <option value="1080">1080p FHD</option>
                <option value="2160">4K Ultra</option>
            </select>
            <select id="s">
                <option value="Popular" selected>الأكثر ترويجاً 🔥</option>
                <option value="Most Viewed">الأكثر مشاهدة</option>
                <option value="Newest">الأحدث</option>
                <option value="Oldest">الأقدم</option>
                <option value="Rating">الأعلى تقييماً</option>
            </select>
        </div>
        <button onclick="start()">إطلاق الرادار 🚀</button>
        <div class="bar"><div id="fill"></div></div>
        <div id="log" style="text-align:center; font-weight:bold; margin-bottom:10px;">الحالة: جاهز</div>
        <div class="stat"><span><span class="label">التقدم:</span> <span id="p">0 / 0</span></span> <span><span class="label">تخطي:</span> <span id="sk">0</span></span></div>
        <div class="stat"><span><span class="label">المنقضي:</span> <span id="el">00:00:00</span></span> <span><span class="label">المتبقي:</span> <span id="eta">00:00:00</span></span></div>
        <div id="curr" style="font-size:11px; color:#666; text-align:center; margin-top:8px;">- انتظار -</div>
    </div>
    <script>
        function start(){
            const d = {url:document.getElementById('u').value, folder:document.getElementById('f').value, engine:document.getElementById('e').value, sort:document.getElementById('s').value, mode:document.getElementById('m').value, quality:document.getElementById('q').value};
            fetch('/start', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
            setInterval(async () => {
                const r = await fetch('/status'); const j = await r.json();
                document.getElementById('log').innerText = j.log;
                document.getElementById('p').innerText = j.total_done + " / " + j.total_count;
                document.getElementById('sk').innerText = j.skipped;
                document.getElementById('el').innerText = j.elapsed;
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
    threading.Thread(target=youtube_worker, args=(d['url'], d['folder'], d['mode'], d['quality'], d['sort'], d['engine'])).start()
    return jsonify({"ok": True})

@app.route('/status')
def get_status(): return jsonify(job_stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
