import os, requests, json, threading, time
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

DROPBOX_CRED = {
    "id": "9d4qz7zbqursfqv",
    "secret": "m26mrjxgbf8yk91",
    "refresh": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"
}

status = {"active": False, "log": "جاهز"}

def get_token():
    try:
        res = requests.post("https://api.dropboxapi.com/oauth2/token", data={
            "grant_type": "refresh_token", "refresh_token": DROPBOX_CRED["refresh"],
            "client_id": DROPBOX_CRED["id"], "client_secret": DROPBOX_CRED["secret"]})
        return res.json().get("access_token")
    except: return None

def run_task(url, folder):
    global status
    token = get_token()
    status.update({"active": True, "log": "🎭 محاكاة تطبيق هاتف (Bypass)..."})
    try:
        # إعدادات متقدمة لمحاكاة الأجهزة المحمولة لتجنب طلب تسجيل الدخول
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio.mp3',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}],
            'nocheckcertificate': True,
            'quiet': True,
            # السر هنا: استخدام عملاء يوتيوب المختلفين (iOS و Android)
            'extractor_args': {'youtube': {'player_client': ['ios', 'android'], 'skip': ['dash', 'hls']}},
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        if os.path.exists("audio.mp3"):
            status["log"] = "📤 جاري الرفع لدروب بوكس..."
            path = f"/خاص يوتيوب/{folder}/{int(time.time())}.mp3"
            with open("audio.mp3", "rb") as f:
                requests.post("https://content.dropboxapi.com/2/files/upload", 
                    headers={"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": path, "mode": "overwrite"})}, data=f)
            os.remove("audio.mp3")
            status["log"] = "✅ نجح التخطي والرفع!"
    except Exception as e:
        error_msg = str(e)
        if "Sign in" in error_msg:
            status["log"] = "❌ يوتيوب يطلب كوكيز (سأعطيك الطريقة الآن)"
        else:
            status["log"] = f"⚠️ خطأ: {error_msg[:30]}"
    status["active"] = False

@app.route('/')
def index():
    return render_template_string('''
    <body style="background:#000;color:#d4af37;text-align:center;padding:50px;font-family:sans-serif;">
        <h2 style="border-bottom:2px solid #d4af37;padding-bottom:10px;display:inline-block;">🛰️ رادار التخفي v7.0</h2>
        <div style="margin:20px auto;max-width:400px;background:#111;padding:20px;border-radius:15px;border:1px solid #333;">
            <input id="u" placeholder="ضع رابط الفيديو هنا" style="width:100%;padding:12px;margin-bottom:15px;border-radius:8px;border:1px solid #444;background:#000;color:#fff;">
            <input id="f" placeholder="اسم المجلد في Dropbox" style="width:100%;padding:12px;margin-bottom:15px;border-radius:8px;border:1px solid #444;background:#000;color:#fff;">
            <button onclick="start()" style="width:100%;background:#d4af37;color:#000;padding:15px;border:none;font-weight:bold;border-radius:10px;cursor:pointer;">بدأ عملية السحب</button>
        </div>
        <h3 id="l" style="color:#fff;">الحالة: جاهز</h3>
        <script>
            function start(){
                const d={url:document.getElementById("u").value,folder:document.getElementById("f").value};
                fetch("/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)});
                poll();
            }
            async function poll(){
                const res=await fetch("/status");const d=await res.json();
                document.getElementById("l").innerText="الحالة: " + d.log;
                if(d.active)setTimeout(poll,2000);
            }
        </script>
    </body>
    ''')

@app.route('/run', methods=['POST'])
def run():
    d = request.json
    threading.Thread(target=run_task, args=(d['url'], d['folder'])).start()
    return jsonify({"ok": True})

@app.route('/status')
def get_status(): return jsonify(status)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)    app.run(host='0.0.0.0', port=port)
