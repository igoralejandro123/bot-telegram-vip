import os
import psycopg2
from flask import Flask, request

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def dashboard():
    data_inicio = request.args.get("inicio")
    data_fim = request.args.get("fim")

    filtro_data = ""
    params = []

    if data_inicio and data_fim:
        filtro_data = "AND DATE(created_at) BETWEEN %s AND %s"
        params = [data_inicio, data_fim]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT COUNT(DISTINCT user_id)
        FROM events
        WHERE 1=1 {filtro_data}
    """, params)
    usuarios = cur.fetchone()[0]

    cur.execute(f"""
        SELECT COUNT(*)
        FROM events
        WHERE event = 'plan_click' {filtro_data}
    """, params)
    cliques = cur.fetchone()[0]

    cur.execute(f"""
        SELECT COUNT(*)
        FROM events
        WHERE event = 'purchase' {filtro_data}
    """, params)
    compras = cur.fetchone()[0]

    cur.execute(f"""
        SELECT COALESCE(SUM(valor),0)
        FROM events
        WHERE event = 'purchase' {filtro_data}
    """, params)
    faturamento_total = cur.fetchone()[0]

    # Ranking de planos
    cur.execute(f"""
        SELECT plano, COUNT(*) AS qtd, SUM(valor) AS total
        FROM events
        WHERE event = 'purchase' {filtro_data}
        GROUP BY plano
        ORDER BY total DESC
    """, params)
    ranking = cur.fetchall()

    # Gráfico diário
    cur.execute(f"""
        SELECT DATE(created_at), COALESCE(SUM(valor),0)
        FROM events
        WHERE event = 'purchase' {filtro_data}
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """, params)
    grafico = cur.fetchall()

    cur.close()
    conn.close()

    labels = [str(r[0]) for r in grafico]
    valores = [float(r[1]) for r in grafico]

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Bot Telegram</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{
                background:#0f0f12;
                color:#fff;
                font-family:Arial;
                margin:0;
            }}
            .container {{
                max-width:1200px;
                margin:auto;
                padding:30px;
            }}
            h1 {{ margin-bottom:20px; }}
            .filters {{
                margin-bottom:30px;
            }}
            input, button {{
                padding:8px;
                border-radius:6px;
                border:none;
                margin-right:10px;
            }}
            button {{
                background:#4f46e5;
                color:white;
                cursor:pointer;
            }}
            .cards {{
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
                gap:20px;
            }}
            .card {{
                background:#1c1c22;
                padding:20px;
                border-radius:12px;
            }}
            .card h2 {{
                font-size:14px;
                color:#aaa;
            }}
            .card p {{
                font-size:26px;
                margin-top:10px;
                font-weight:bold;
            }}
            table {{
                width:100%;
                margin-top:40px;
                border-collapse:collapse;
            }}
            th, td {{
                padding:12px;
                border-bottom:1px solid #2a2a30;
            }}
            th {{ color:#aaa; }}
            canvas {{ margin-top:40px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Dashboard — Bot Telegram VIP</h1>

            <form class="filters" method="get">
                <input type="date" name="inicio" value="{data_inicio or ''}">
                <input type="date" name="fim" value="{data_fim or ''}">
                <button>Filtrar</button>
            </form>

            <div class="cards">
                <div class="card"><h2>Usuários</h2><p>{usuarios}</p></div>
                <div class="card"><h2>Cliques</h2><p>{cliques}</p></div>
                <div class="card"><h2>Compras</h2><p>{compras}</p></div>
                <div class="card"><h2>Faturamento</h2><p>R$ {faturamento_total:.2f}</p></div>
            </div>

            <h2 style="margin-top:40px;">🏆 Ranking de Planos</h2>
            <table>
                <tr><th>Plano</th><th>Vendas</th><th>Faturamento</th></tr>
                {''.join(f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>R$ {float(r[2]):.2f}</td></tr>" for r in ranking)}
            </table>

            <h2 style="margin-top:40px;">📈 Faturamento Diário</h2>
            <canvas id="grafico"></canvas>
        </div>

        <script>
            const ctx = document.getElementById('grafico');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {labels},
                    datasets: [{{
                        label: 'Faturamento',
                        data: {valores},
                        borderColor: '#4f46e5',
                        backgroundColor: 'rgba(79,70,229,0.2)',
                        tension: 0.3,
                        fill: true
                    }}]
                }},
                options: {{
                    plugins: {{
                        legend: {{ labels: {{ color: 'white' }} }}
                    }},
                    scales: {{
                        x: {{ ticks: {{ color: 'white' }} }},
                        y: {{ ticks: {{ color: 'white' }} }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
