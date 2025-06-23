import os
import logging
import yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

# 🔐 TOKEN
BOT_TOKEN = '7652520907:AAGYUYo9AjUtOJBqgmypTKqSAn0Po9oamDc'

# 📁 Yuklash katalogi
DOWNLOAD_DIR = "downloads"

# 🧾 Log sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🟢 /start komandasi
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Salom!\nYouTube videosini yuklab olish uchun link yuboring.\nMP3 yoki MP4 formatini tanlang."
    )

# 📩 Foydalanuvchi xabarini qabul qilish
def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        context.user_data['url'] = url
        keyboard = [
            [InlineKeyboardButton("🎵 MP3 (audio)", callback_data='mp3'),
             InlineKeyboardButton("🎥 MP4 (video)", callback_data='mp4')]
        ]
        update.message.reply_text("📤 Qanday formatda yuklab olmoqchisiz?", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        update.message.reply_text("❗ Iltimos, YouTube link yuboring.")

# 🔘 Format tanlash
def format_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    format_type = query.data
    url = context.user_data.get('url')
    user_id = query.from_user.id
    msg = query.message

    if not url:
        query.edit_message_text("❗ Iltimos, avval YouTube link yuboring.")
        return

    msg.edit_text("⏳ Yuklab olinmoqda, kuting...")

    os.makedirs(f"{DOWNLOAD_DIR}/{user_id}", exist_ok=True)
    outtmpl = f"{DOWNLOAD_DIR}/{user_id}/output.%(ext)s"

    # 🛠 YDL sozlamalari
    ydl_opts = {
        'outtmpl': outtmpl,
        'quiet': True,
        'noplaylist': True,
        'merge_output_format': 'mp4',
        'postprocessors': [],
    }

    if format_type == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    elif format_type == 'mp4':
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type == 'mp3':
                filename = filename.rsplit(".", 1)[0] + ".mp3"

        # Fayl tekshirish
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            msg.edit_text("❌ Yuklab olish muvaffaqiyatsiz tugadi.")
            return

        title = info.get('title', 'Nomaʼlum')
        duration = int(info.get('duration', 0))
        minutes, seconds = divmod(duration, 60)
        caption = f"✅ Yuklandi!\n🎬 {title}\n⏱ {minutes} daq {seconds} son\n📦 {format_type.upper()}"

        with open(filename, 'rb') as f:
            if format_type == 'mp3':
                context.bot.send_audio(chat_id=query.message.chat_id, audio=f, caption=caption)
            else:
                context.bot.send_video(chat_id=query.message.chat_id, video=f, caption=caption)

        os.remove(filename)
    except Exception as e:
        logger.error(e)
        msg.edit_text("❌ Xatolik: video yuklab bo‘lmadi.")
    finally:
        try:
            os.rmdir(f"{DOWNLOAD_DIR}/{user_id}")
        except:
            pass

# ▶️ Botni ishga tushirish
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(format_choice))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
