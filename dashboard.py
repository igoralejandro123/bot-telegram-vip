import os
import psycopg2
from flask import Flask

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(DISTINCT user_id) FROM events")
    usuarios = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM events WHERE event = 'plan_click'")
    cliques = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM events WHERE event = 'purchase'")
    compras = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(valor), 0) FROM events WHERE event = 'purchase'")
    faturamento_total = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM events
        WHERE event = 'purchase'
        AND DATE(created_at) = CURRENT_DATE
    """)
    faturamento_hoje = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM events
        WHERE event = 'purchase'
        AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)
    """)
    faturamento_mes = cur.fetchone()[0]

    cur.close()
    conn.close()

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Bot Telegram</title>
        <style>
            body {{
                margin: 0;
                font-family: Arial, Helvetica, sans-serif;
                background: #0f0f12;
                color: #ffffff;
            }}
            .container {{
                padding: 30px;
                max-width: 1200px;
                margin: auto;
            }}
            h1 {{
                margin-bottom: 30px;
            }}
            .cards {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 20px;
            }}
            .card {{
                background: #1c1c22;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 0 10px rgba(0,0,0,0.4);
            }}
            .card h2 {{
                font-size: 14px;
                font-weight: normal;
                color: #aaaaaa;
            }}
            .card p {{
                font-size: 28px;
                margin: 10px 0 0;
                font-weight: bold;
            }}
            table {{
                width: 100%;
                margin-top: 40px;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 15px;
                text-align: left;
            }}
            th {{
                background: #1c1c22;
                color: #aaa;
            }}
            tr {{
                border-bottom: 1px solid #2a2a30;
            }}
            footer {{
                margin-top: 40px;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Dashboard — Bot Telegram VIP</h1>

            <div class="cards">
                <div class="card">
                    <h2>Usuários únicos</h2>
                    <p>{usuarios}</p>
                </div>
                <div class="card">
                    <h2>Cliques nos planos</h2>
                    <p>{cliques}</p>
                </div>
                <div class="card">
                    <h2>Compras realizadas</h2>
                    <p>{compras}</p>
                </div>
                <div class="card">
                    <h2>Faturamento hoje</h2>
                    <p>R$ {faturamento_hoje:.2f}</p>
                </div>
                <div class="card">
                    <h2>Faturamento do mês</h2>
                    <p>R$ {faturamento_mes:.2f}</p>
                </div>
                <div class="card">
                    <h2>Faturamento total</h2>
                    <p>R$ {faturamento_total:.2f}</p>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Métrica</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Usuários</td>
                        <td>{usuarios}</td>
                    </tr>
                    <tr>
                        <td>Cliques</td>
                        <td>{cliques}</td>
                    </tr>
                    <tr>
                        <td>Compras</td>
                        <td>{compras}</td>
                    </tr>
                </tbody>
            </table>

            <footer>
                Dashboard interno • Atualizado em tempo real
            </footer>
        </div>
    </body>
    </html>
    """
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
