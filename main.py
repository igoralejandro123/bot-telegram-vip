from telegram.ext import Updater, MessageHandler, Filters

BOT_TOKEN = "8337535041:AAFyfor-WYhKL5wG6ct3VarJ5Y8i-MddLrU"

def pegar_file_id(update, context):
    if update.message.video:
        update.message.reply_text(
            f"FILE_ID DO VÍDEO:\n{update.message.video.file_id}"
        )
    else:
        update.message.reply_text("Envie um vídeo 🎥")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.all, pegar_file_id))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
