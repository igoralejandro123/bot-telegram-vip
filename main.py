import base64
import io
import asyncio
import mercadopago
import qrcode
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from telegram.ext import MessageHandler, filters

async def capturar_video(update, context):
    if update.message.video:
        file_id = update.message.video.file_id
        await update.message.reply_text(f"FILE_ID:\n{file_id}")

app.add_handler(MessageHandler(filters.VIDEO, capturar_video))


# ==============================
# CONFIGURAÇÕES (EDITAR AQUI)
# ==============================

BOT_TOKEN = "8337535041:AAFyfor-WYhKL5wG6ct3VarJ5Y8i-MddLrU"
MP_ACCESS_TOKEN = "APP_USR-6292592654909636-122507-7c4203a2f6ce5376e87d2446eb46a5ee-247711451"

LINK_GRUPO_VIP = "https://t.me/+yInsORz5ZKQ3MzUx"


TEXTO_VENDA = (
    "🔥 *GRUPO VIP EXCLUSIVO* 🔥\n\n"
    "✔ Conteúdo diário\n"
    "✔ Acesso imediato\n"
    "✔ Sem enrolação\n\n"
    "Escolha um plano abaixo 👇"
)

PLANOS = {
    "mensal": ("Plano Mensal", 29.90),
    "trimestral": ("Plano Trimestral", 79.90),
    "semestral": ("Plano Semestral", 149.90),
    "vitalicio": ("Plano Vitalício", 299.90),
}

# ==============================
# MERCADO PAGO
# ==============================

sdk = mercadopago.SDK("APP_USR-6292592654909636-122507-7c4203a2f6ce5376e87d2446eb46a5ee-247711451")

# ==============================
# START
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    with open("video1.mp4", "rb") as v1:
        await context.bot.send_video(chat_id=chat_id, video=v1)

    with open("video2.mp4", "rb") as v2:
        await context.bot.send_video(chat_id=chat_id, video=v2)


    keyboard = [
        [InlineKeyboardButton(f"{nome} - R$ {valor}", callback_data=plano)]
        for plano, (nome, valor) in PLANOS.items()
    ]

    await context.bot.send_message(
        chat_id=chat_id,
        text=TEXTO_VENDA,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==============================
# CLIQUE NO PLANO
# ==============================

async def escolher_plano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plano = query.data
    nome, valor = PLANOS[plano]

    payment_data = {
        "transaction_amount": valor,
        "description": nome,
        "payment_method_id": "pix",
        "payer": {"email": "comprador@telegram.com"}
    }

    payment = sdk.payment().create(payment_data)
    payment = payment["response"]

    pix_code = payment["point_of_interaction"]["transaction_data"]["qr_code"]
    qr_base64 = payment["point_of_interaction"]["transaction_data"]["qr_code_base64"]

    context.user_data["payment_id"] = payment["id"]

    # Gerar QR Code imagem
    qr_bytes = base64.b64decode(qr_base64)
    image = io.BytesIO(qr_bytes)
    image.name = "qrcode.png"

    await query.message.reply_photo(
        photo=image,
        caption=(
            f"💳 *{nome}*\n"
            f"💰 Valor: R$ {valor}\n\n"
            "📲 *Pix Copia e Cola:*\n"
            f"`{pix_code}`\n\n"
            "Após o pagamento, aguarde a confirmação automática ⏳"
        ),
        parse_mode="Markdown"
    )

    asyncio.create_task(verificar_pagamento(update, context))

# ==============================
# VERIFICA PAGAMENTO
# ==============================

async def verificar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    payment_id = context.user_data.get("payment_id")

    for _ in range(60):  # verifica por até 5 minutos
        payment = sdk.payment().get(payment_id)["response"]

        if payment["status"] == "approved":
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "✅ *Pagamento confirmado!*\n\n"
                    "Aqui está seu acesso ao Grupo VIP 👇\n"
                    f"{LINK_GRUPO_VIP}"
                ),
                parse_mode="Markdown"
            )
            return

        await asyncio.sleep(5)

    await context.bot.send_message(
        chat_id=chat_id,
        text="⏰ Pagamento não confirmado ainda. Se já pagou, aguarde alguns minutos."
    )

# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(escolher_plano))

    app.run_polling()





