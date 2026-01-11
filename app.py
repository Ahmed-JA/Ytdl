import os, requests, json, threading, time
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# 1. بيانات دروب بوكس
DROPBOX_CRED = {
    "id": "9d4qz7zbqursfqv",
    "secret": "m26mrjxgbf8yk91",
    "refresh": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"
}

# 2. الكوكيز الخاصة بك (هويتك الرقمية)
MY_COOKIES = "GPS=1;YSC=cRPU3pja-SY;VISITOR_INFO1_LIVE=20zT46tInss;VISITOR_PRIVACY_METADATA=CgJFRxIEGgAgQw%3D%3D;PREF=tz=Africa.Cairo;__Secure-1PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;__Secure-3PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;HSID=AU_XHwPsXUSGUgZUq;SSID=AUtRaUQzpuXcGFlsb;APISID=GGcg9KjkJelNvooU/AvZNu9CDwwOGpuxn0;SAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-1PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-3PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;SID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_XpfS3nrxc6u1zRA46komJgACgYKAYwSARUSFQHGX2Mim9bkw294mS0juox0SqUHlRoVAUF8yKpxxgQ2GqF2sh645dKyGxGU0076;__Secure-1PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_Prv_jFBo8DGf7MvL3m3YUwACgYKAWASARUSFQHGX2MiB-68MTGXuISLXx-5gLyoNxoVAUF8yKqj5sYlM5mxOCH1yIqQpG3p0076;__Secure-3PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_tmt8C6WACoM_TRnt53rcYgACgYKAZISARUSFQHGX2Milx8SWGqPhNOfk0cfC1hrNxoVAUF8yKoXkn7Q5sDuY655VEVQaFfe0076;SIDCC=AKEyXzXbs9U_0rXrAMwsUsNPo6241A1pvdWMBo5jMumu_tZQ9oCCIWJjxpWhz39Lmy-8_RGG;__Secure-1PSIDCC=AKEyXzUrixeXBrKvilXAOfFF2vomAbwfekYfnRcsQbueJgwR4_WwL_aFnudX9Gf6SgYBw1FC;__Secure-3PSIDCC=AKEyXzVCBBwgu1cRise8l6N6GXku2xxp8V0b5yqLtAGikatgYPob-f91jH2fbJpvyluC1mP5;LOGIN_INFO=AFmmF2swRQIhAPjDN9b05Pm08f9dnxS73Hh4-ZyPVQnMWMTdhqvhin-9AiBXsnlmvdi0CXO8n-gKF4DXUxmi6i0YrK1KIgtd9XjAOw:QUQ3MjNmeTlfbGZFdmtlZWdhVHNPWllWcGF0RkQxVjBMLVBxM2Y3ZEhBcTlBRWxuQ2xRX1BhUEo1UzU1WEoyMEtiVGpvN3J4NlZpRUg3QXB2WnJJU3JtTlNwalE1RnIyYzhSMzhMOUNRRGV1cnFRQVp5c0VBbWZoZ2RMd2gtZVVJdFBxajlmbXFFc2hYcjJoMmdEVVotRmRrdHhWVVRnQUdB;"

status = {"active": False, "log": "الرادار متصل بحسابك ✅"}

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
    status.update({"active": True, "log": "🔐 تم التحقق من الكوكيز.. جاري السحب"})
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'auth_download.mp3',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}],
        'nocheckcertificate': True,
        'quiet': True,
        # هنا نرسل الكوكيز ليظن يوتيوب أنك تتصفح من جهازك
        'http_headers': {
            'Cookie': MY_COOKIES,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        if os.path.exists("auth_download.mp3"):
            status["log"] = "📤 جاري الرفع لحسابك..."
            path = f"/خاص يوتيوب/{folder}/{int(time.time())}.mp3"
            with open("auth_download.mp3", "rb") as f:
                requests.post("https://content.dropboxapi.com/2/files/upload", 
                    headers={"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": path, "mode": "overwrite"})}, data=f)
            os.remove("auth_download.mp3")
            status["log"] = "✅ تمت العملية بنجاح تام!"
        else:
            status["log"] = "❌ لم يتم إنشاء الملف (تأكد من الرابط)"
            
    except Exception as e:
        status["log"] = f"⚠️ خطأ: {str(e)[:40]}"
        print(e)
    status["active"] = False

@app.route('/')
def index():
    return render_template_string('''
    <body style="background:#0e0e0e;color:#d4af37;text-align:center;padding:20px;font-family:sans-serif;">
        <div style="border:2px solid #d4af37;border-radius:20px;padding:25px;background:#1a1a1a;max-width:500px;margin:auto;">
            <h2>🔐 رادار يوتيوب (نسخة الكوكيز)</h2>
            <p style="color:#0f0;font-size:12px;">✅ الحساب متصل: Bypass Active</p>
            <input id="u" placeholder="رابط الفيديو" style="width:100%;padding:15px;margin:10px 0;border-radius:8px;border:none;">
            <input id="f" placeholder="المجلد (Dropbox)" style="width:100%;padding:15px;margin:10px 0;border-radius:8px;border:none;">
            <button onclick="start()" id="b" style="width:100%;background:#d4af37;color:#000;padding:15px;font-weight:bold;border-radius:8px;cursor:pointer;margin-top:10px;">سحب ورفع 🚀</button>
            <h3 id="l" style="margin-top:20px;color:#ccc;">جاهز</h3>
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
    app.run(host='0.0.0.0', port=port)            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
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
