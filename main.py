import os
import psycopg2
import requests
import hashlib
import time
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

BOT_TOKEN = os.getenv("BOT_TOKEN")
LINK_GRUPO_VIP = "https://t.me/+yInsORz5ZKQ3MzUx"


VIDEO_1 = "BAACAgEAAxkBAAMKaVmsE6uLzN1eavu9LbmwGTcy9nkAAlAFAAI0vNFGSOpp8seZaPo4BA"
VIDEO_2 = "BAACAgEAAxkBAAMMaVmsNfyP4EH2JAikdyuhJ8QIHRkAAlEFAAI0vNFG4I0r6duZ84A4BA"

SYNCPAY_CLIENT_ID = os.getenv("SYNCPAY_CLIENT_ID")
SYNCPAY_CLIENT_SECRET = os.getenv("SYNCPAY_CLIENT_SECRET")

def syncpay_get_token():
    url = "https://syncpay.com.br/api/partner/v1/auth-token"
    payload = {
        "client_id": SYNCPAY_CLIENT_ID,
        "client_secret": SYNCPAY_CLIENT_SECRET
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()["access_token"]

def syncpay_create_cashin(amount, description):
    token = syncpay_get_token()
    url = "https://syncpay.com.br/api/partner/v1/cash-in"
    payload = {
        "amount": float(amount),
        "description": description,
        "client": {
            "name": "Cliente",
            "cpf": "00000000000",
            "email": "cliente@telegram.com",
            "phone": "00000000000"
        }
    }
    r = requests.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=15
    )
    r.raise_for_status()
    data = r.json()
    return data["pix_code"], data["identifier"]

def syncpay_get_transaction(identifier):
    token = syncpay_get_token()
    url = f"https://syncpay.com.br/api/partner/v1/transaction/{identifier}"
    r = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=15
    )
    r.raise_for_status()
    return r.json()["data"]


TEXTO_VENDA = """
    🔥 PARAÍSO DAS N0V!NH@ S ⁺¹⁸ 🔥

👧 Um grupo cheio de nov!nh@s com conteúdo v@z4do, g4rot@s saf@das que você não encontra em nenhum outro lugar 🕵️

⭐️ Mais de 10.000 VÍDEOS RAROS nunca vistos antes.

🔥D@ndo buc3t@s para o p@pai
🔥Inc3st0 R3al
🔥Tendo cuz!nh0 penetr@do
🔥Exibindo suas buc3t@s
🔥M@mand0 p@pai e !rmão
🔥Atualizações diárias
🔥Onlyf@ns e priv@cy
E MUITO MAIS...

🚨ATENÇÃO: APENAS HOJE COM 35% DE DESCONTO, AMANHÃ JÁ VOLTA O PREÇO NORMAL 🙀

🗝️PAGOU, ENTROU NO GRUPO VIP 
❖ Pagamento via Pix 
🕵️Completamente anônimo, não aparece no extrato.

 

👻 GARANTA O SEU ACESSO AGORA 👇
"""

PLANOS = {
    "P1": ("🥉1 MÊS DE ACESSO 🌸", 14.90),
    "P2": ("🥈1 MÊS DE ACESSO + !NC3ST0 R3AL 🌸👧", 19.90),
    "P3": ("🥇VITALÍCIO + !NC3ST0 R3AL + 5 GRPS DARK 🌸👧☠️", 29.90),
    "P4": ("💎 DARK SIDE - TEM DE TUDO 🌸👧☠️😈", 49.90),
}


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
    enviar_evento_meta("Lead", user_id=user_id)
    
    # context.bot.send_video(chat_id=chat_id, video=VIDEO_1)
    # context.bot.send_video(chat_id=chat_id, video=VIDEO_2)

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

def enviar_evento_meta(event_name, user_id=None, valor=None):
    url = "https://graph.facebook.com/v18.0/2315641305587153/events"

    payload = {
        "data": [{
            "event_name": event_name,
            "event_time": int(time.time()),
            "action_source": "website",
            "event_source_url": "https://dashboard-production-a6c3.up.railway.app",
            "custom_data": {
                "currency": "BRL",
                "value": float(valor or 0)
            },
            "user_data": {
                "external_id": hashlib.sha256(str(user_id).encode()).hexdigest()
            }
        }],
        "access_token": "EAAqaeJvWmy8BQQ2pEGYxRVKX7CV5IwbAzvb3JulC0UtzvSH1UuNORzVLynEmhMchXo1LXVffUjiYEM9XVfh4PMqVDx3dZBqIA22QsbSu35X4APJkuan9SYTuQXZAb2EX87CYFipRJBjFD67GZBlmjDbjs3bqGItk4QnZAbZAHrEZC5gO6ZBvFK5QtQjtdgTCQZDZD"
    }

    r = requests.post(url, json=payload)
    print("META:", r.status_code, r.text)



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

    enviar_evento_meta("InitiateCheckout", user_id=user_id, valor=valor)

    pix_code, identifier = syncpay_create_cashin(
        amount=valor,
        description=nome
    )

    context.user_data["payment_id"] = identifier

    query.message.reply_text(
        f"*💳 {nome}*\n"
        f"*💰 Valor:* R$ {valor}\n\n"
        "⬇️ *PIX Copia e Cola:*",
        parse_mode="Markdown"
    )

    query.message.reply_text(
        f"`{pix_code}`",
        parse_mode="Markdown"
    )

    query.message.reply_text(
        "👆 Copie a chave PIX acima e realize o pagamento.\n\n"
        "Após pagar, clique abaixo 👇",
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

    tx = syncpay_get_transaction(payment_id)

    if tx.get("status") == "completed":
        user_id = context.user_data.get("user_id")
        plano = context.user_data.get("plano")
        valor_pago = tx.get("amount", 0)

        enviar_evento_meta(
            "Purchase",
            user_id=user_id,
            valor=valor_pago
        )

        registrar_evento(
            user_id,
            "purchase",
            plano=plano,
            valor=valor_pago
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


    updater.start_polling(drop_pending_updates=True)
    print("BOT INICIADO COM SUCESSO")
    updater.idle()

if __name__ == "__main__":
    main()





























