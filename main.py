import os
import psycopg2
import requests
import hashlib
import base64
import io
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

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não está definido nas Variables do Railway (serviço do BOT).")
    return psycopg2.connect(DATABASE_URL)

def criar_tabela_eventos():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            event VARCHAR(50),
            plano VARCHAR(50),
            valor NUMERIC,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

def criar_tabela_gastos():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id SERIAL PRIMARY KEY,
            data DATE NOT NULL,
            tipo VARCHAR(20),
            valor NUMERIC NOT NULL,
            descricao TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


def registrar_evento(user_id, event, plano=None, valor=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO events (user_id, event, plano, valor)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, event, plano, valor)
        )

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Erro ao registrar evento:", e)




# ======================
# START
# ======================

def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    registrar_evento(user_id, "start")

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
# pixel
# ======================

def enviar_evento_meta(event_name, valor=None):
    url = f"https://graph.facebook.com/v18.0/2315641305587153/events"

    payload = {
        "data": [{
            "event_name": event_name,
            "event_time": int(time.time()),
            "action_source": "chat",
            "event_source_url": "telegram_bot",
            "custom_data": {
                "currency": "BRL",
                "value": valor if valor else 0
            }
        }],
        "access_token": "EAAqaeJvWmy8BQXFE0XOLKX14fqx0RTsr8ZC4mXpxyQUpZCapjypMjaTnwxlF0gKwlvKHIN7nGcEt5XNt7h3WRwLf1EParsRSz6EVyvjrzZB0wjb0bGpZCwzQiYwlwbyb7Dad7tZCDopTELS8kjpwraHzeyJetrUK78FMZAnBDZCwxbuz9vLGxaTK6M6zUiQKwZDZD"
    }

    requests.post(url, json=payload, timeout=5)



# ======================
# ESCOLHER PLANO
# ======================

def escolher_plano(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    context.user_data["user_id"] = query.from_user.id

    plano = query.data
    context.user_data["plano"] = plano
    nome, valor = PLANOS[plano]

    user_id = query.from_user.id
    registrar_evento(user_id, "plan_click", plano=plano, valor=valor)

    enviar_evento_meta("InitiateCheckout", valor)

    payment_data = {
        "transaction_amount": valor,
        "description": nome,
        "payment_method_id": "pix",
        "payer": {"email": "comprador@telegram.com"}
    }

    payment = sdk.payment().create(payment_data)["response"]
    context.user_data["payment_id"] = payment["id"]


    pix_data = payment["point_of_interaction"]["transaction_data"]
    pix_code = pix_data["qr_code"]
    qr_base64 = pix_data["qr_code_base64"]

    qr_bytes = base64.b64decode(qr_base64)
    qr_image = io.BytesIO(qr_bytes)
    qr_image.name = "qrcode.png"

    query.message.reply_photo(
        photo=qr_image,
        caption=(
            f"💳 *{nome}*\n"
            f"💰 *Valor:* R$ {valor}\n\n"
            "💠 *Como realizar o pagamento:*\n\n"
            "1️⃣ Abra o aplicativo do seu banco.\n"
            "2️⃣ Selecione a opção *Pagar* ou *PIX*.\n"
            "3️⃣ Escolha *PIX Copia e Cola*.\n"
            "4️⃣ Cole o código abaixo e finalize o pagamento com segurança.\n\n"
            "⬇️ *PIX Copia e Cola:*"
        ),
        parse_mode="Markdown"
    )

    query.message.reply_text(
        f"`{pix_code}`",
        parse_mode="Markdown",
    )

    query.message.reply_text(
        "👆 *Toque na chave PIX acima para copiá-la e pague no seu banco.*\n\n"
        "‼️ *APÓS O PAGAMENTO, clique no botão abaixo para verificar o pagamento* 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ VERIFICAR PAGAMENTO", callback_data="verificar_pagamento")]
        ])
    )



# ======================
# VERIFICAR PAGAMENTO
# ======================

def verificar_pagamento(chat_id, context: CallbackContext):
    payment_id = context.user_data.get("payment_id")

    if not payment_id:
        context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Nenhum pagamento encontrado para verificar."
        )
        return

    payment = sdk.payment().get(payment_id)["response"]

    if payment["status"] == "approved":
        enviar_evento_meta("Purchase", payment["transaction_amount"])

        user_id = context.user_data.get("user_id")
        plano = context.user_data.get("plano")

        registrar_evento(
            user_id,
            "purchase",
            plano=plano,
            valor=payment["transaction_amount"]
        )



        context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Pagamento confirmado!\n\nAcesse o grupo:\n{LINK_GRUPO_VIP}"
        )
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text="⏳ Pagamento ainda não confirmado. Clique novamente em alguns segundos."
        )




def verificar_pagamento_manual(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer("Verificando pagamento... ⏳")

    verificar_pagamento(query.message.chat_id, context)



# ======================
# MAIN
# ======================

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(verificar_pagamento_manual, pattern="^verificar_pagamento$"))
    dp.add_handler(CallbackQueryHandler(escolher_plano))

    
    criar_tabela_eventos()
    criar_tabela_gastos()


    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()


















