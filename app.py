import os, requests, json, threading, time
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# بيانات دروب بوكس الخاصة بك
DROPBOX_CRED = {
    "id": "9d4qz7zbqursfqv",
    "secret": "m26mrjxgbf8yk91",
    "refresh": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"
}

status = {"active": False, "log": "جاهز"}

def get_token():
    res = requests.post("https://api.dropboxapi.com/oauth2/token", data={
        "grant_type": "refresh_token", "refresh_token": DROPBOX_CRED["refresh"],
        "client_id": DROPBOX_CRED["id"], "client_secret": DROPBOX_CRED["secret"]})
    return res.json().get("access_token")

def run_task(url, folder):
    global status
    token = get_token()
    status.update({"active": True, "log": "📥 جاري السحب..."})
    try:
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'audio.mp3', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if os.path.exists("audio.mp3"):
            status["log"] = "📤 جاري الرفع..."
            path = f"/خاص يوتيوب/{folder}/{int(time.time())}.mp3"
            with open("audio.mp3", "rb") as f:
                requests.post("https://content.dropboxapi.com/2/files/upload", 
                    headers={"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": path, "mode": "overwrite"})}, data=f)
            os.remove("audio.mp3")
            status["log"] = "✅ تم بنجاح!"
    except Exception as e:
        status["log"] = f"⚠️ خطأ: {str(e)[:30]}"
    status["active"] = False

@app.route('/')
def index():
    return render_template_string('<body style="background:#000;color:#d4af37;text-align:center;padding:50px;font-family:sans-serif;"><h2>🛰️ رادار Koyeb v1</h2><input id="u" placeholder="رابط يوتيوب" style="width:80%;padding:12px;margin:10px;"><br><input id="f" placeholder="اسم المجلد" style="width:80%;padding:12px;"><br><br><button onclick="start()" style="background:#d4af37;color:#000;padding:15px 60px;border:none;font-weight:bold;border-radius:10px;">ابدأ السحب</button><h3 id="l" style="margin-top:30px;">الحالة: جاهز</h3><script>function start(){const d={url:document.getElementById("u").value,folder:document.getElementById("f").value};fetch("/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)});poll();}async function poll(){const res=await fetch("/status");const d=await res.json();document.getElementById("l").innerText="الحالة: " + d.log;if(d.active)setTimeout(poll,2000);}</script></body>')

@app.route('/run', methods=['POST'])
def run():
    d = request.json
    threading.Thread(target=run_task, args=(d['url'], d['folder'])).start()
    return jsonify({"ok": True})

@app.route('/status')
def get_status(): return jsonify(status)

if __name__ == '__main__':
    # مهم جداً لـ Koyeb
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
