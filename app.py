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

RAW_COOKIES = """GPS=1;VISITOR_INFO1_LIVE=20zT46tInss;""" # ضع كوكيزك هنا

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
    
    # تحسين الرابط لدعم القنوات (إضافة /videos لضمان جلب كل الفيديوهات)
    clean_url = url.strip()
    if "/channel/" in clean_url or "/c/" in clean_url or "/@" in clean_url:
        if not clean_url.endswith("/videos"):
            clean_url = clean_url.rstrip('/') + "/videos"

    job_stats.update({"active": True, "log": "🔍 جاري فحص القناة/الرابط...", "total_done": 0, "skipped": 0, "start_time": time.time()})
    
    try:
        # إعدادات الاستخراج لدعم القنوات الكبيرة
        ydl_opts = {
            'cookiefile': 'cookies.txt',
            'quiet': True,
            'extract_flat': True, # مهم جداً لجلب القائمة بسرعة دون تحميل الفيديوهات
            'force_generic_extractor': False,
            'ignoreerrors': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(clean_url, download=False)
            
            if not res:
                raise Exception("تعذر الوصول للرابط")

            # استخراج الفيديوهات سواء كانت قناة أو قائمة تشغيل أو فيديو مفرد
            if 'entries' in res:
                videos = [v for v in res['entries'] if v]
            else:
                videos = [res]

            # نظام الترتيب
            if sort_by == "Most Viewed": videos.sort(key=lambda x: x.get('view_count') or 0, reverse=True)
            elif sort_by == "Newest": videos.sort(key=lambda x: x.get('upload_date') or '', reverse=True)
            elif sort_by == "Oldest": videos.sort(key=lambda x: x.get('upload_date') or '')
            
            job_stats["total_count"] = len(videos)

        for i, video in enumerate(videos):
            token = get_token(engine_name)
            v_url = video.get('url') if video.get('url') else f"https://www.youtube.com/watch?v={video.get('id')}"
            v_title = "".join([c for c in video.get('title', 'Video') if c.isalnum() or c in " "]).strip()
            
            processed = i + 1
            
            # تحديث الوقت المتبقي
            elapsed_sec = time.time() - job_stats["start_time"]
            avg_time = elapsed_sec / processed if processed > 0 else 0
            rem_sec = avg_time * (len(videos) - processed)
            job_stats.update({"elapsed": str(timedelta(seconds=int(elapsed_sec))), "eta": str(timedelta(seconds=int(rem_sec)))})

            tasks = []
            if mode in ["Audio Only", "Both"]: tasks.append(("Audio", "bestaudio/best", "mp3"))
            if mode in ["Videos Only", "Both"]: tasks.append(("Videos", f"best[height<={quality}][ext=mp4]/best", "mp4"))

            for sub, fmt, ext in tasks:
                filename = f"{processed:03d} - {v_title}.{ext}"
                full_path = f"/خاص يوتيوب/{folder_name}/{sub}/{filename}"

                if check_exists(token, full_path):
                    job_stats["skipped"] += 1
                    continue

                job_stats.update({"current_file": f"[{sub}] {v_title[:25]}...", "log": f"📡 نقل فيديو {processed} من {len(videos)}"})
                
                try:
                    with yt_dlp.YoutubeDL({'format': fmt, 'cookiefile': 'cookies.txt', 'quiet': True, 'noplaylist': True}) as ydl_s:
                        info = ydl_s.extract_info(v_url, download=False)
                        if not info or 'url' not in info: continue
                        
                        with requests.get(info['url'], stream=True, timeout=300) as r:
                            r.raise_for_status()
                            requests.post("https://content.dropboxapi.com/2/files/upload", 
                                         headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream",
                                                  "Dropbox-API-Arg": json.dumps({"path": full_path, "mode": "overwrite"})}, 
                                         data=r.iter_content(chunk_size=1024*1024))
                except: continue
            
            job_stats["total_done"] = processed
            gc.collect()

        job_stats.update({"log": "✅ اكتمل العمل بنجاح", "active": False})
    except Exception as e:
        job_stats.update({"log": f"⚠️ خطأ: {str(e)[:40]}", "active": False})

# --- (بقية كود Flask والـ UI يبقى كما هو بدون تغيير) ---
UI = """...""" # نفس الـ UI السابق

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
