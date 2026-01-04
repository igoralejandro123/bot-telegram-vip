import os
import psycopg2
from flask import Flask, request, redirect

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/", methods=["GET", "POST"])
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()

    # SALVAR GASTO
    if request.method == "POST":
        data = request.form["data"]
        tipo = request.form["tipo"]
        valor = request.form["valor"]
        descricao = request.form.get("descricao")

        cur.execute(
            """
            INSERT INTO gastos (data, tipo, valor, descricao)
            VALUES (%s, %s, %s, %s)
            """,
            (data, tipo, valor, descricao)
        )
        conn.commit()
        return redirect("/")

    # RESUMO POR DIA
    cur.execute("""
        SELECT 
            d.data,
            COALESCE(f.faturamento, 0) AS faturamento,
            COALESCE(g.facebook, 0) AS facebook,
            COALESCE(g.outros, 0) AS outros
        FROM (
            SELECT DISTINCT DATE(created_at) AS data FROM events
            UNION
            SELECT DISTINCT data FROM gastos
        ) d
        LEFT JOIN (
            SELECT DATE(created_at) AS data, SUM(valor) AS faturamento
            FROM events
            WHERE event = 'purchase'
            GROUP BY DATE(created_at)
        ) f ON f.data = d.data
        LEFT JOIN (
            SELECT data,
                SUM(CASE WHEN tipo = 'facebook' THEN valor ELSE 0 END) AS facebook,
                SUM(CASE WHEN tipo = 'outros' THEN valor ELSE 0 END) AS outros
            FROM gastos
            GROUP BY data
        ) g ON g.data = d.data
        ORDER BY d.data DESC
        LIMIT 30
    """)

    resumo = cur.fetchall()

    cur.close()
    conn.close()

    linhas = ""
    for r in resumo:
        data, faturamento, facebook, outros = r
        gastos_totais = facebook + outros
        lucro = faturamento - gastos_totais
        roi = (lucro / gastos_totais * 100) if gastos_totais > 0 else 0

        linhas += f"""
        <tr>
            <td>{data}</td>
            <td>R$ {faturamento:.2f}</td>
            <td>R$ {facebook:.2f}</td>
            <td>R$ {outros:.2f}</td>
            <td>R$ {gastos_totais:.2f}</td>
            <td style="color:{'#22c55e' if lucro >= 0 else '#ef4444'}">
                R$ {lucro:.2f}
            </td>
            <td>{roi:.1f}%</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Financeiro</title>
        <style>
            body {{
                background:#0f0f12;
                color:#fff;
                font-family:Arial;
            }}
            .container {{
                max-width:1200px;
                margin:auto;
                padding:30px;
            }}
            h1 {{ margin-bottom:20px; }}
            form {{
                background:#1c1c22;
                padding:20px;
                border-radius:12px;
                margin-bottom:40px;
            }}
            input, select, button {{
                padding:10px;
                margin-right:10px;
                border-radius:6px;
                border:none;
            }}
            button {{
                background:#22c55e;
                font-weight:bold;
                cursor:pointer;
            }}
            table {{
                width:100%;
                border-collapse:collapse;
            }}
            th, td {{
                padding:12px;
                border-bottom:1px solid #2a2a30;
                text-align:center;
            }}
            th {{ color:#aaa; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Financeiro Diário</h1>

            <form method="post">
                <input type="date" name="data" required>
                <select name="tipo">
                    <option value="facebook">Facebook Ads</option>
                    <option value="outros">Outros gastos</option>
                </select>
                <input type="number" step="0.01" name="valor" placeholder="Valor" required>
                <input type="text" name="descricao" placeholder="Descrição (opcional)">
                <button>Salvar gasto</button>
            </form>

            <table>
                <tr>
                    <th>Data</th>
                    <th>Faturamento</th>
                    <th>Facebook</th>
                    <th>Outros</th>
                    <th>Gastos Totais</th>
                    <th>Lucro</th>
                    <th>ROI</th>
                </tr>
                {linhas}
            </table>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
