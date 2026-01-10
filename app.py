import os, requests, json, threading, time
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# بيانات دروب بوكس
DROPBOX_CRED = {
    "id": "9d4qz7zbqursfqv",
    "secret": "m26mrjxgbf8yk91",
    "refresh": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"
}

status = {"active": False, "log": "جاهز", "file": "", "done": 0, "total": 0}

def get_token():
    try:
        res = requests.post("https://api.dropboxapi.com/oauth2/token", data={
            "grant_type": "refresh_token", "refresh_token": DROPBOX_CRED["refresh"],
            "client_id": DROPBOX_CRED["id"], "client_secret": DROPBOX_CRED["secret"]})
        return res.json().get("access_token")
    except: return None

def run_task(url, folder, mode, quality):
    global status
    token = get_token()
    status.update({"active": True, "log": "📡 محاولة الاتصال عبر بروتوكول مشفر...", "done": 0, "total": 1})
    
    base_dropbox = f"/خاص يوتيوب/{folder}"
    filename_base = f"ByAK_{int(time.time())}"
    
    # إعدادات متقدمة جداً لاستخدام "مشغل الويب" بدلاً من "مشغل الأندرويد"
    dl_opts = {
        'format': 'bestaudio/best' if mode == "Audio Only" else f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'outtmpl': f'{filename_base}.%(ext)s',
        'quiet': True,
        'no_check_certificate': True,
        'youtube_include_dash_manifest': False,
        'extract_flat': False,
        # تقنية تخطي الحظر عبر محاكاة مشغل يوتيوب الرسمي (Web Client)
        'client_name': 'WEB',
        'client_version': '2.20240210.01.00',
    }

    if mode == "Audio Only":
        dl_opts.update({'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})

    try:
        with yt_dlp.YoutubeDL(dl_opts) as ydl:
            status["log"] = "📥 جاري سحب البيانات (Web Bypass)..."
            # محاولة التحميل
            ydl.download([url])
            
        ext = "mp3" if mode == "Audio Only" else "mp4"
        downloaded_file = f"{filename_base}.{ext}"
        
        if os.path.exists(downloaded_file):
            status["log"] = "📤 جاري الرفع لدروب بوكس..."
            final_path = f"{base_dropbox}/{'Audio' if mode == 'Audio Only' else 'Videos'}/001 - Done ByAK.{ext}"
            
            with open(downloaded_file, "rb") as f:
                requests.post("https://content.dropboxapi.com/2/files/upload", 
                    headers={"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": final_path, "mode": "overwrite"})},
                    data=f)
            
            os.remove(downloaded_file)
            status.update({"done": 1, "log": "✅ تم الرفع بنجاح!"})
        else:
            status["log"] = "🚫 يوتيوب حظر الـ IP بشكل نهائي لهذا السيرفر"

    except Exception as e:
        status["log"] = f"⚠️ خطأ: {str(e)[:40]}"
    
    status["active"] = False

@app.route('/')
def index():
    return render_template_string('''
    <body style="background:#000; color:#d4af37; text-align:center; font-family:sans-serif; padding:20px;">
        <div style="border:1px solid #d4af37; padding:20px; border-radius:15px; max-width:400px; margin:auto;">
            <h3>🛰️ رادار يوتيوب v5.0</h3>
            <input id="u" placeholder="الرابط" style="width:100%; padding:10px; margin:10px 0;">
            <input id="f" placeholder="المجلد" style="width:100%; padding:10px; margin:10px 0;">
            <select id="m" style="width:100%; padding:10px; margin:10px 0;"><option>Audio Only</option><option>Videos Only</option></select>
            <button onclick="start()" id="btn" style="width:100%; padding:10px; background:#d4af37; border:none; font-weight:bold;">تشغيل</button>
            <div id="l" style="margin-top:20px;">الحالة: جاهز</div>
            <div id="stats" style="font-size:12px; margin-top:5px;">0 / 1</div>
        </div>
        <script>
            function start(){
                document.getElementById('btn').disabled = true;
                const d = {url:document.getElementById('u').value, folder:document.getElementById('f').value, mode:document.getElementById('m').value, quality:'480'};
                fetch('/run', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
                poll();
            }
            async function poll(){
                const res = await fetch('/status'); const d = await res.json();
                document.getElementById('l').innerText = d.log;
                document.getElementById('stats').innerText = d.done + " / 1";
                if(d.active) setTimeout(poll, 2000); else document.getElementById('btn').disabled = false;
            }
        </script>
    </body>
    ''')

@app.route('/run', methods=['POST'])
def run():
    d = request.json
    threading.Thread(target=run_task, args=(d['url'], d['folder'], d['mode'], d['quality'])).start()
    return jsonify({"ok": True})

@app.route('/status')
def get_status(): return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
