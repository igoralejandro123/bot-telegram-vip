import time
import mercadopago
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext
)

# ======================
# CONFIGURAÇÕES
# ======================

BOT_TOKEN = "8337535041:AAFyfor-WYhKL5wG6ct3VarJ5Y8i-MddLrU"
MP_ACCESS_TOKEN = "APP_USR-6292592654909636-122507-7c4203a2f6ce5376e87d2446eb46a5ee-247711451"
LINK_GRUPO_VIP = "https://t.me/+yInsORz5ZKQ3MzUx"

VIDEO_1 = "BAACAgEAAxkBAAMKaVmsE6uLzN1eavu9LbmwGTcy9nkAAlAFAAI0vNFGSOpp8seZaPo4BA"
VIDEO_2 = "BAACAgEAAxkBAAMMaVmsNfyP4EH2JAikdyuhJ8QIHRkAAlEFAAI0vNFG4I0r6duZ84A4BA"

TEXTO_VENDA = """
    🔥 PARAÍSO DAS NOV!NHAS ⁺¹⁸ 🔥

👧 Um grupo cheio de novinhas com conteúdo vazado, garotas safadas que você não encontra em nenhum outro lugar 🕵️

⭐️ Mais de 10.000 VÍDEOS RAROS nunca vistos antes.

👧Garotas dando suas bucetas para o papai
👧Inc3sto Real
👧Novinhas tendo cuzinho penetrado
👧Novinhas exibindo suas bucetas
👧Novinhas gostosas mamando papai e irmão
👧Atualizações diárias
👧Onlyfans e privacy
E MUITO MAIS...

🚨ATENÇÃO: APENAS HOJE COM 35% DE DESCONTO, AMANHÃ JÁ VOLTA O PREÇO NORMAL 🙀

🗝️PAGOU, ENTROU NO GRUPO (não tem taxa de desbloqueio) 
❖ Pagamento via Pix 
🕵️Completamente anônimo, não aparece no extrato.
 

👻 GARANTA O SEU ACESSO AGORA 👇
"""

PLANOS = {
    "P1": ("🥉1 MÊS DE ACESSO 🌸", 14.90),
    "P2": ("🥈1 MÊS DE ACESSO + INC3STO R3AL 🌸👧", 19.90),
    "P3": ("🥇VITALÍCIO + INC3STO R3AL + 5 GRPS DARK 🌸👧☠️", 29.90),
    "P4": ("💎 DARK SIDE - TEM DE TUDO 🌸👧☠️😈", 49.90),
}

sdk = mercadopago.SDK("APP_USR-6292592654909636-122507-7c4203a2f6ce5376e87d2446eb46a5ee-247711451")

# ======================
# START
# ======================

def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    # ENVIA OS VÍDEOS (autoplay no chat)
    context.bot.send_video(chat_id=chat_id, video=VIDEO_1)
    context.bot.send_video(chat_id=chat_id, video=VIDEO_2)

    keyboard = [
        [InlineKeyboardButton(f"{nome} - R$ {valor}", callback_data=plano)]
        for plano, (nome, valor) in PLANOS.items()
    ]

    context.bot.send_message(
        chat_id=chat_id,
        text=TEXTO_VENDA,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ======================
# ESCOLHER PLANO
# ======================

def escolher_plano(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

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

    query.message.reply_text(
        f"💳 {nome}\n"
        f"💰 R$ {valor}\n\n"
        f"Pix copia e cola:\n{pix_code}\n\n"
        "Após pagar, aguarde a confirmação ⏳"
    )

    verificar_pagamento(query.message.chat_id, context)

# ======================
# VERIFICAR PAGAMENTO
# ======================

def verificar_pagamento(chat_id, context: CallbackContext):
    payment_id = context.user_data.get("payment_id")

    for _ in range(60):
        payment = sdk.payment().get(payment_id)["response"]

        if payment["status"] == "approved":
            context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Pagamento confirmado!\n\nAcesse o grupo:\n{LINK_GRUPO_VIP}"
            )
            return

        time.sleep(5)

# ======================
# MAIN
# ======================

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(escolher_plano))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()




