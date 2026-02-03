import os
import requests
import threading
from flask import Flask
from telethon import TelegramClient, events

# --- خادم الويب لضمان استقرار Koyeb ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running perfectly!", 200

def run_flask():
    # استخدام المنفذ 8080 كما حددناه في إعدادات Koyeb
    app.run(host='0.0.0.0', port=8080)

# --- إعدادات البوت من متغيرات البيئة ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
WORKER_URL = os.getenv("WORKER_URL").rstrip('/')
MASTER_KEY = os.getenv("MASTER_KEY")

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("✅ البوت متصل بالخزنة الذهبية.\nأرسل أي ملف ليتم رفعه إلى مجلدك الخاص في DLytupe.")

@client.on(events.NewMessage)
async def handle_file(event):
    if event.message.file:
        user_id = str(event.sender_id)
        file_name = event.message.file.name or "unnamed_file"
        
        # بناء المسار حسب الخطة الذهنية: DLytupe/UserID/FileName
        target_path = f"DLytupe/{user_id}/{file_name}"
        upload_url = f"{WORKER_URL}/{target_path}"
        
        msg = await event.reply(f"🚀 جاري الرفع إلى: {target_path}...")
        
        try:
            # تحميل الملف من تيليجرام
            file_data = await event.download_media(file=bytes)
            
            # إرسال الملف للجسر (Cloudflare Worker)
            headers = {
                'X-Master-Key': MASTER_KEY,
                'Content-Type': 'application/octet-stream'
            }
            
            response = requests.put(upload_url, data=file_data, headers=headers)
            
            if response.status_code in [200, 201]:
                await msg.edit(f"✅ تم الرفع بنجاح!\nالمسار: `{target_path}`")
            else:
                await msg.edit(f"❌ خطأ في الجسر: {response.status_code}")
        
        except Exception as e:
            await msg.edit(f"⚠️ حدث خطأ أثناء الرفع: {str(e)}")

if __name__ == '__main__':
    # تشغيل خادم الويب في خيط منفصل (Thread)
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot is starting...")
    client.run_until_disconnected()
