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

# الكوكيز التي أرسلتها
RAW_COOKIES = "GPS=1;YSC=cRPU3pja-SY;VISITOR_INFO1_LIVE=20zT46tInss;VISITOR_PRIVACY_METADATA=CgJFRxIEGgAgQw%3D%3D;PREF=tz=Africa.Cairo;__Secure-1PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;__Secure-3PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;HSID=AU_XHwPsXUSGUgZUq;SSID=AUtRaUQzpuXcGFlsb;APISID=GGcg9KjkJelNvooU/AvZNu9CDwwOGpuxn0;SAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-1PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-3PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;SID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_XpfS3nrxc6u1zRA46komJgACgYKAYwSARUSFQHGX2Mim9bkw294mS0juox0SqUHlRoVAUF8yKpxxgQ2GqF2sh645dKyGxGU0076;__Secure-1PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_Prv_jFBo8DGf7MvL3m3YUwACgYKAWASARUSFQHGX2MiB-68MTGXuISLXx-5gLyoNxoVAUF8yKqj5sYlM5mxOCH1yIqQpG3p0076;__Secure-3PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_tmt8C6WACoM_TRnt53rcYgACgYKAZISARUSFQHGX2Milx8SWGqPhNOfk0cfC1hrNxoVAUF8yKoXkn7Q5sDuY655VEVQaFfe0076;SIDCC=AKEyXzXbs9U_0rXrAMwsUsNPo6241A1pvdWMBo5jMumu_tZQ9oCCIWJjxpWhz39Lmy-8_RGG;__Secure-1PSIDCC=AKEyXzUrixeXBrKvilXAOfFF2vomAbwfekYfnRcsQbueJgwR4_WwL_aFnudX9Gf6SgYBw1FC;__Secure-3PSIDCC=AKEyXzVCBBwgu1cRise8l6N6GXku2xxp8V0b5yqLtAGikatgYPob-f91jH2fbJpvyluC1mP5;LOGIN_INFO=AFmmF2swRQIhAPjDN9b05Pm08f9dnxS73Hh4-ZyPVQnMWMTdhqvhin-9AiBXsnlmvdi0CXO8n-gKF4DXUxmi6i0YrK1KIgtd9XjAOw:QUQ3MjNmeTlfbGZFdmtlZWdhVHNPWllWcGF0RkQxVjBMLVBxM2Y3ZEhBcTlBRWxuQ2xRX1BhUEo1UzU1WEoyMEtiVGpvN3J4NlZpRUg3QXB2WnJJU3JtTlNwalE1RnIyYzhSMzhMOUNRRGV1cnFRQVp5c0VBbWZoZ2RMd2gtZVVJdFBxajlmbXFFc2hYcjJoMmdEVVotRmRrdHhWVVRnQUdB"

status = {"active": False, "log": "جاهز"}

def create_cookie_file():
    with open("cookies.txt", "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in RAW_COOKIES.split(';'):
            try:
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    f.write(f".youtube.com\tTRUE\t/\tFALSE\t2698716888\t{key}\t{value}\n")
            except: pass

def get_token():
    try:
        res = requests.post("https://api.dropboxapi.com/oauth2/token", data={
            "grant_type": "refresh_token", "refresh_token": DROPBOX_CRED["refresh"],
            "client_id": DROPBOX_CRED["id"], "client_secret": DROPBOX_CRED["secret"]})
        return res.json().get("access_token")
    except: return None

def run_task(url, folder):
    global status
    create_cookie_file()
    token = get_token()
    status.update({"active": True, "log": "⚡ جاري السحب السريع..."})
    
    # إعدادات بدون تحويل لتجنب خطأ ffprobe
    ydl_opts = {
        'format': 'bestaudio/best', 
        'outtmpl': 'audio_file.%(ext)s',
        'nocheckcertificate': True,
        'quiet': True,
        'cookiefile': 'cookies.txt',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        if os.path.exists(filename):
            status["log"] = "📤 جاري الرفع لـ Dropbox..."
            # استخراج الصيغة الأصلية للملف لرفعها بشكل صحيح
            ext = filename.split('.')[-1]
            path = f"/خاص يوتيوب/{folder}/{int(time.time())}.{ext}"
            
            with open(filename, "rb") as f:
                requests.post("https://content.dropboxapi.com/2/files/upload", 
                    headers={"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": path, "mode": "overwrite"})}, data=f)
            
            os.remove(filename)
            status["log"] = "✅ تم الرفع بنجاح!"
        else:
            status["log"] = "❌ لم يتم العثور على الملف"
    except Exception as e:
        status["log"] = f"⚠️ خطأ: {str(e)[:40]}"
    status["active"] = False

@app.route('/')
def index():
    return render_template_string('''
    <body style="background:#000;color:#d4af37;text-align:center;padding:20px;font-family:sans-serif;">
        <div style="border:2px solid #d4af37;border-radius:20px;padding:20px;background:#111;max-width:450px;margin:auto;">
            <h2>🛰️ رادار يوتيوب السريع v12</h2>
            <p style="color:#888;">التحميل بالصيغة الأصلية (بدون FFmpeg)</p>
            <input id="u" placeholder="رابط فيديو يوتيوب" style="width:100%;padding:15px;margin:10px 0;border-radius:10px;border:none;">
            <input id="f" placeholder="اسم المجلد في Dropbox" style="width:100%;padding:15px;margin:10px 0;border-radius:10px;border:none;">
            <button onclick="start()" id="b" style="width:100%;background:#d4af37;color:#000;padding:15px;font-weight:bold;border-radius:10px;cursor:pointer;">بدء السحب والرفع</button>
            <h3 id="l" style="margin-top:20px;color:#fff;">جاهز</h3>
        </div>
        <script>
            function start(){
                const b=document.getElementById("b");
                b.disabled=true; b.style.opacity="0.5";
                const d={url:document.getElementById("u").value,folder:document.getElementById("f").value};
                fetch("/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)});
                poll();
            }
            async function poll(){
                const res=await fetch("/status");const d=await res.json();
                document.getElementById("l").innerText=d.log;
                if(d.active)setTimeout(poll,2000); else { document.getElementById("b").disabled=false; document.getElementById("b").style.opacity="1"; }
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
    app.run(host='0.0.0.0', port=port)
