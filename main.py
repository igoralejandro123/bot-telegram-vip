import asyncio
import mercadopago
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ======================
# CONFIGURAÇÕES
# ======================

BOT_TOKEN = "8337535041:AAFyfor-WYhKL5wG6ct3VarJ5Y8i-MddLrU"
MP_ACCESS_TOKEN = "APP_USR-6292592654909636-122507-7c4203a2f6ce5376e87d2446eb46a5ee-247711451"

LINK_GRUPO_VIP = "https://t.me/+yInsORz5ZKQ3MzUx"

TEXTO_VENDA = (
    "🔥 GRUPO VIP EXCLUSIVO 🔥\n\n"
    "✔ Conteúdo diário\n"
    "✔ Acesso imediato\n\n"
    "Escolha um plano abaixo 👇"
)

PLANOS = {
    "mensal": ("Plano Mensal", 29.90),
    "trimestral": ("Plano Trimestral", 79.90),
    "semestral": ("Plano Semestral", 149.90),
    "vitalicio": ("Plano Vitalício", 299.90),
}

# ======================
# MERCADO PAGO
# ======================

sdk = mercadopago.SDK("APP_USR-6292592654909636-122507-7c4203a2f6ce5376e87d2446eb46a5ee-247711451")

# ======================
# START
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton(f"{nome} - R$ {valor}", callback_data=plano)]
        for plano, (nome, valor) in PLANOS.items()
    ]

    await context.bot.send_message(
        chat_id=chat_id,
        text=TEXTO_VENDA,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ======================
# PLANO SELECIONADO
# ======================

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

    payment = sdk.payment().create(payment_data)["response"]

    pix_code = payment["point_of_interaction"]["transaction_data"]["qr_code"]

    context.user_data["payment_id"] = payment["id"]

    await query.message.reply_text(
        f"💳 *{nome}*\n"
        f"💰 R$ {valor}\n\n"
        f"Pix copia e cola:\n`{pix_code}`\n\n"
        "Após pagar, aguarde a confirmação ⏳",
        parse_mode="Markdown"
    )

    asyncio.create_task(verificar_pagamento(update, context))

# ======================
# VERIFICAR PAGAMENTO
# ======================

async def verificar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    payment_id = context.user_data.get("payment_id")

    for _ in range(60):
        payment = sdk.payment().get(payment_id)["response"]

        if payment["status"] == "approved":
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Pagamento confirmado!\n\nAcesse o grupo:\n{LINK_GRUPO_VIP}"
            )
            return

        await asyncio.sleep(5)

# ======================
# MAIN
# ======================

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(escolher_plano))

    app.run_polling()
