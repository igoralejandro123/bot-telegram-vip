from telegram.ext import ApplicationBuilder, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

BOT_TOKEN = "8337535041:AAFyfor-WYhKL5wG6ct3VarJ5Y8i-MddLrU"

async def receber_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video:
        await update.message.reply_text(
            f"FILE_ID:\n{update.message.video.file_id}"
        )
    else:
        await update.message.reply_text("Envie um VÍDEO 🎥")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.ALL, receber_video))
app.run_polling()
