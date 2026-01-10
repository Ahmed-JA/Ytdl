import os, requests, json, threading, time
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# بيانات دروب بوكس (ثابتة)
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
    status.update({"active": True, "log": "🚀 جاري السحب من المنصة الجديدة...", "done": 0, "total": 1})
    
    ydl_opts = {
        'format': 'bestaudio/best' if mode == "Audio Only" else f'bestvideo[height<={quality}]+bestaudio/best',
        'outtmpl': 'ByAK_file.%(ext)s',
        'quiet': True,
        'no_check_certificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0 Safari/537.36',
    }

    if mode == "Audio Only":
        ydl_opts.update({'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        ext = "mp3" if mode == "Audio Only" else "mp4"
        filename = f"ByAK_file.{ext}"
        
        if os.path.exists(filename):
            status["log"] = "📤 رفع سحابي..."
            path = f"/خاص يوتيوب/{folder}/{mode}/{int(time.time())}_ByAK.{ext}"
            with open(filename, "rb") as f:
                requests.post("https://content.dropboxapi.com/2/files/upload", 
                    headers={"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": path, "mode": "overwrite"})},
                    data=f)
            os.remove(filename)
            status.update({"done": 1, "log": "✅ تم الرفع بنجاح!"})
        else:
            status["log"] = "❌ لم يتم سحب الملف"
    except Exception as e:
        status["log"] = f"⚠️ خطأ: {str(e)[:40]}"
    
    status["active"] = False

@app.route('/')
def index():
    return render_template_string('''
    <body style="background:#000; color:#d4af37; text-align:center; font-family:sans-serif; padding:20px;">
        <div style="border:2px solid #d4af37; padding:20px; border-radius:15px; max-width:400px; margin:auto;">
            <h3>🛰️ رادار يوتيوب v6.1</h3>
            <p style="font-size:12px; color:white;">المنصة: نشطة ✅</p>
            <input id="u" placeholder="الرابط" style="width:100%; padding:10px; margin:10px 0; box-sizing:border-box;">
            <input id="f" placeholder="المجلد" style="width:100%; padding:10px; margin:10px 0; box-sizing:border-box;">
            <select id="m" style="width:100%; padding:10px; margin:10px 0; box-sizing:border-box;"><option>Audio Only</option><option>Videos Only</option></select>
            <button onclick="start()" id="btn" style="width:100%; padding:12px; background:#d4af37; border:none; font-weight:bold; border-radius:8px;">تشغيل المحرك</button>
            <div id="l" style="margin-top:20px; font-weight:bold;">الحالة: جاهز</div>
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
    # الحصول على المنفذ تلقائياً من المنصة لتجنب 404
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
