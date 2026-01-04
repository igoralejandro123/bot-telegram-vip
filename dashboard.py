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

    # LISTAR GASTOS
    cur.execute("""
        SELECT data, tipo, valor, descricao
        FROM gastos
        ORDER BY data DESC
        LIMIT 20
    """)
    gastos = cur.fetchall()

    cur.close()
    conn.close()

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard - Gastos</title>
        <style>
            body {{
                background:#0f0f12;
                color:#fff;
                font-family:Arial;
            }}
            .container {{
                max-width:1000px;
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
                color:#000;
                cursor:pointer;
                font-weight:bold;
            }}
            table {{
                width:100%;
                border-collapse:collapse;
            }}
            th, td {{
                padding:12px;
                border-bottom:1px solid #2a2a30;
            }}
            th {{ color:#aaa; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💸 Controle de Gastos</h1>

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
                    <th>Tipo</th>
                    <th>Valor</th>
                    <th>Descrição</th>
                </tr>
                {''.join(f"<tr><td>{g[0]}</td><td>{g[1]}</td><td>R$ {float(g[2]):.2f}</td><td>{g[3] or ''}</td></tr>" for g in gastos)}
            </table>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
