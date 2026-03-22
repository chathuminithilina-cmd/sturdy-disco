import os
import telebot
from pcloud import PyCloud

# 1. Environment Variables from Koyeb
BOT_TOKEN = os.getenv('BOT_TOKEN')
PCLOUD_EMAIL = os.getenv('PCLOUD_EMAIL')
PCLOUD_PASS = os.getenv('PCLOUD_PASS')

bot = telebot.TeleBot(BOT_TOKEN)
pc = PyCloud(PCLOUD_EMAIL, PCLOUD_PASS)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    help_text = (
        "🚀 **pCloud Manager Bot**\n\n"
        "📤 **Upload:** Just send me any file.\n"
        "📂 **List:** Use `/list` to see your cloud files.\n"
        "📥 **Download:** Use `/get [File ID]` to fetch a file.\n"
        "📊 **Status:** Use `/storage` for quota info.\n"
        "🔗 **Web:** Use `/link` for pCloud login."
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

# --- STORAGE & LINK ---
@bot.message_handler(commands=['storage'])
def check_storage(message):
    u = pc.userinfo()
    bot.reply_to(message, f"📊 Storage: {u['usedquota']/(1024**3):.2f}GB / {u['quota']/(1024**3):.2f}GB")

@bot.message_handler(commands=['link'])
def get_link(message):
    bot.reply_to(message, "🌐 https://my.pcloud.com")

# --- LIST FILES ---
@bot.message_handler(commands=['list'])
def list_pcloud_files(message):
    try:
        # Lists files in the root folder (folderid=0)
        contents = pc.listfolder(folderid=0)['metadata']['contents']
        file_list = "📂 **Your pCloud Files:**\n\n"
        for item in contents:
            if not item['isfolder']:
                file_list += f"📄 `{item['name']}`\nID: `{item['fileid']}`\n\n"
        file_list += "💡 _Use /get [ID] to download a file._"
        bot.send_message(message.chat.id, file_list, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ List Error: {str(e)}")

# --- DOWNLOAD: pCloud -> Telegram ---
@bot.message_handler(commands=['get'])
def download_from_pcloud(message):
    try:
        file_id = message.text.split()[-1]
        if file_id == "/get":
            return bot.reply_to(message, "Please provide a File ID. Example: `/get 123456789`", parse_mode="Markdown")
        
        bot.reply_to(message, "⏳ Fetching from pCloud...")
        
        # Get the temporary download link from pCloud
        link_data = pc.getfilelink(fileid=file_id)
        file_url = f"https://{link_data['hosts'][0]}{link_data['path']}"
        
        # Send the link as a button or just the link text
        bot.send_message(message.chat.id, f"📥 **Your Download Link:**\n{file_url}", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Download Error: Ensure the ID is correct.")

# --- UPLOAD: Telegram -> pCloud ---
@bot.message_handler(content_types=['document', 'video', 'photo'])
def handle_uploads(message):
    try:
        if message.document:
            f_id, f_name = message.document.file_id, message.document.file_name
        elif message.photo:
            f_id, f_name = message.photo[-1].file_id, f"IMG_{f_id[:8]}.jpg"
        elif message.video:
            f_id, f_name = message.video.file_id, message.video.file_name or f"VID_{f_id[:8]}.mp4"

        f_info = bot.get_file(f_id)
        data = bot.download_file(f_info.file_path)
        with open(f_name, 'wb') as f: f.write(data)
            
        pc.uploadfile(files=[f_name])
        bot.reply_to(message, f"✅ Uploaded to pCloud: `{f_name}`", parse_mode="Markdown")
        if os.path.exists(f_name): os.remove(f_name)
    except Exception as e:
        bot.reply_to(message, f"❌ Upload Error: {str(e)}")

bot.infinity_polling()
