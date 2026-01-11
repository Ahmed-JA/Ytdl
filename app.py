import os, requests, json, threading, time
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

DROPBOX_CRED = {
    "id": "9d4qz7zbqursfqv",
    "secret": "m26mrjxgbf8yk91",
    "refresh": "vFHAEY3OTC0AAAAAAAAAAYZ24BsCaJxfipat0zdsJnwy9QTWRRec439kHlYTGYLc"
}

RAW_COOKIES = "GPS=1;YSC=cRPU3pja-SY;VISITOR_INFO1_LIVE=20zT46tInss;VISITOR_PRIVACY_METADATA=CgJFRxIEGgAgQw%3D%3D;PREF=tz=Africa.Cairo;__Secure-1PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;__Secure-3PSIDTS=sidts-CjUB7I_69LSciYHXZh3o2hM0pQXNmWT7E0bSJ7XtwWP1gZtDILx6nr6sqNbmDVuJJTzLzEUK0hAA;HSID=AU_XHwPsXUSGUgZUq;SSID=AUtRaUQzpuXcGFlsb;APISID=GGcg9KjkJelNvooU/AvZNu9CDwwOGpuxn0;SAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-1PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;__Secure-3PAPISID=IXCWIdAajZ3-A5A6/A2PfSXhj_WRIO3r_B;SID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_XpfS3nrxc6u1zRA46komJgACgYKAYwSARUSFQHGX2Mim9bkw294mS0juox0SqUHlRoVAUF8yKpxxgQ2GqF2sh645dKyGxGU0076;__Secure-1PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_Prv_jFBo8DGf7MvL3m3YUwACgYKAWASARUSFQHGX2MiB-68MTGXuISLXx-5gLyoNxoVAUF8yKqj5sYlM5mxOCH1yIqQpG3p0076;__Secure-3PSID=g.a0005giXgKs500hEm0IcasdI-ZteDk_7LMmKgY5J1pSN24PAUbY_tmt8C6WACoM_TRnt53rcYgACgYKAZISARUSFQHGX2Milx8SWGqPhNOfk0cfC1hrNxoVAUF8yKoXkn7Q5sDuY655VEVQaFfe0076;SIDCC=AKEyXzXbs9U_0rXrAMwsUsNPo6241A1pvdWMBo5jMumu_tZQ9oCCIWJjxpWhz39Lmy-8_RGG;__Secure-1PSIDCC=AKEyXzUrixeXBrKvilXAOfFF2vomAbwfekYfnRcsQbueJgwR4_WwL_aFnudX9Gf6SgYBw1FC;__Secure-3PSIDCC=AKEyXzVCBBwgu1cRise8l6N6GXku2xxp8V0b5yqLtAGikatgYPob-f91jH2fbJpvyluC1mP5;LOGIN_INFO=AFmmF2swRQIhAPjDN9b05Pm08f9dnxS73Hh4-ZyPVQnMWMTdhqvhin-9AiBXsnlmvdi0CXO8n-gKF4DXUxmi6i0YrK1KIgtd9XjAOw:QUQ3MjNmeTlfbGZFdmtlZWdhVHNPWllWcGF0RkQxVjBMLVBxM2Y3ZEhBcTlBRWxuQ2xRX1BhUEo1UzU1WEoyMEtiVGpvN3J4NlZpRUg3QXB2WnJJU3JtTlNwalE1RnIyYzhSMzhMOUNRRGV1cnFRQVp5c0VBbWZoZ2RMd2gtZVVJdFBxajlmbXFFc2hYcjJoMmdEVVotRmRrdHhWVVRnQUdB;"

status = {"active": False, "log": "جاهز"}

def create_cookie_file():
    c_path = os.path.join(os.getcwd(), "cookies.txt")
    with open(c_path, "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in RAW_COOKIES.split(';'):
            if '=' in cookie:
                k, v = cookie.strip().split('=', 1)
                f.write(f".youtube.com\tTRUE\t/\tFALSE\t2698716888\t{k}\t{v}\n")
    return c_path

def get_token():
    try:
        res = requests.post("https://api.dropboxapi.com/oauth2/token", data={
            "grant_type": "refresh_token", "refresh_token": DROPBOX_CRED["refresh"],
            "client_id": DROPBOX_CRED["id"], "client_secret": DROPBOX_CRED["secret"]})
        return res.json().get("access_token")
    except: return None

def run_task(url, folder):
    global status
    c_path = create_cookie_file()
    token = get_token()
    status.update({"active": True, "log": "🛸 جاري سحب الرابط المباشر..."})
    
    # تحميل الصوت بصيغة واحدة ثابتة لتجنب الحاجة للدمج أو المعالجة
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio', 
        'cookiefile': c_path,
        'quiet': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False) # لا تحمل الملف، فقط اسحب بياناته
            stream_url = info['url'] # الرابط المباشر للملف الصوتي
            title = "".join(x for x in info['title'] if x.isalnum() or x in " -_").strip()
            
        status["log"] = "📥 جاري النقل السحابي..."
        # سحب الملف من يوتيوب ودفعه فوراً لدروب بوكس في نفس الوقت (Stream)
        with requests.get(stream_url, stream=True) as r:
            r.raise_for_status()
            db_path = f"/خاص يوتيوب/{folder}/{title}.m4a"
            requests.post("https://content.dropboxapi.com/2/files/upload", 
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream", "Dropbox-API-Arg": json.dumps({"path": db_path, "mode": "overwrite"})}, data=r.raw)
        
        status["log"] = "✅ تم السحب والرفع بنجاح!"
    except Exception as e:
        status["log"] = f"⚠️ خطأ: {str(e)[:50]}"
    status["active"] = False

@app.route('/')
def index():
    return render_template_string('''
    <body style="background:#000;color:#d4af37;text-align:center;padding:20px;font-family:sans-serif;">
        <div style="border:1px solid #d4af37;border-radius:15px;padding:20px;max-width:400px;margin:auto;">
            <h2>🚀 الرادار السحابي المباشر v14</h2>
            <input id="u" placeholder="رابط يوتيوب" style="width:100%;padding:12px;margin:10px 0;border-radius:8px;">
            <input id="f" placeholder="اسم المجلد" style="width:100%;padding:12px;margin:10px 0;border-radius:8px;">
            <button onclick="start()" id="b" style="width:100%;background:#d4af37;color:#000;padding:15px;font-weight:bold;border-radius:10px;">سحب ورفع سحابي</button>
            <h3 id="l" style="margin-top:20px;color:#fff;">جاهز للعمل</h3>
        </div>
        <script>
            function start(){
                fetch("/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:document.getElementById("u").value,folder:document.getElementById("f").value})});
                poll();
            }
            async function poll(){
                const res=await fetch("/status"); const d=await res.json();
                document.getElementById("l").innerText=d.log;
                if(d.active) setTimeout(poll,2000);
            }
        </script>
    </body>
    ''')

@app.route('/run', methods=['POST'])
def run():
    threading.Thread(target=run_task, args=(request.json['url'], request.json['folder'])).start()
    return jsonify({"ok": True})

@app.route('/status')
def get_status(): return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
