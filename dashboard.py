import os
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()

    # Usuários únicos
    cur.execute("SELECT COUNT(DISTINCT user_id) FROM events")
    usuarios = cur.fetchone()[0]

    # Cliques em planos
    cur.execute("SELECT COUNT(*) FROM events WHERE event = 'plan_click'")
    cliques = cur.fetchone()[0]

    # Compras
    cur.execute("SELECT COUNT(*) FROM events WHERE event = 'purchase'")
    compras = cur.fetchone()[0]

    # Faturamento total
    cur.execute("SELECT COALESCE(SUM(valor), 0) FROM events WHERE event = 'purchase'")
    faturamento_total = cur.fetchone()[0]

    # Faturamento hoje
    cur.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM events
        WHERE event = 'purchase'
        AND DATE(created_at) = CURRENT_DATE
    """)
    faturamento_hoje = cur.fetchone()[0]

    # Faturamento do mês
    cur.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM events
        WHERE event = 'purchase'
        AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)
    """)
    faturamento_mes = cur.fetchone()[0]

    cur.close()
    conn.close()

    return jsonify({
        "usuarios": usuarios,
        "cliques": cliques,
        "compras": compras,
        "faturamento_total": float(faturamento_total),
        "faturamento_hoje": float(faturamento_hoje),
        "faturamento_mes": float(faturamento_mes)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
