import os
import psycopg2
import requests
import hashlib
import time
import mercadopago
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler,
    Filters
)


# ======================
# CONFIGURAÇÕES
# ======================

BOT_TOKEN = os.getenv("BOT_TOKEN")
LINK_GRUPO_VIP = "https://t.me/+yInsORz5ZKQ3MzUx"


VIDEO_1 = "BAACAgEAAxkBAAMMaVxtBmtQMa6p__yi7rTFF79AXagAAn4GAAIPieFG4ZCWKEzzv404BA"
VIDEO_2 = "BAACAgEAAxkBAAMQaVxtaUOwPdcwHDp2kgqGn2DoOqsAAn8GAAIPieFGhjEDHYsmd8c4BA"


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

mp = mercadopago.SDK(os.getenv("MERCADO_PAGO_ACCESS_TOKEN"))

def mp_criar_pix(valor, descricao):
    payment_data = {
        "transaction_amount": float(valor),
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {
            "email": "cliente@telegram.com"
        }
    }

    payment = mp.payment().create(payment_data)
    pix_code = payment["response"]["point_of_interaction"]["transaction_data"]["qr_code"]
    payment_id = payment["response"]["id"]

    return pix_code, payment_id

def mp_pagamento_aprovado(payment_id):
    payment = mp.payment().get(payment_id)
    status = payment["response"]["status"]
    return status == "approved", payment["response"]



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

    try:
        pix_code, identifier = mp_criar_pix(valor, nome)
        
    except Exception as e:
        query.message.reply_text("❌ Erro ao gerar PIX. Tente novamente mais tarde.")
        print("ERRO MERCADO PAGO:", e)
        return


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
            text="⚠️ Nenhum pagamento encontrado."
        )
        return

    aprovado, dados = mp_pagamento_aprovado(payment_id)

    if aprovado:
        user_id = context.user_data.get("user_id")
        plano = context.user_data.get("plano")
        valor_pago = dados.get("transaction_amount", 0)

        registrar_evento(
            user_id,
            "purchase",
            plano=plano,
            valor=valor_pago
        )

        enviar_evento_meta(
            "Purchase",
            user_id=user_id,
            valor=valor_pago
        )

        context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Pagamento confirmado!\n\nAcesse o grupo VIP:\n{LINK_GRUPO_VIP}"
        )
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text="⏳ Pagamento ainda não confirmado. Tente novamente em alguns segundos."
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

    # 🔥 LINHA NOVA (OBRIGATÓRIA)
    updater.bot.delete_webhook(drop_pending_updates=True)

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




































