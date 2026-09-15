import os
from flask import Flask, jsonify, request
import pymysql
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ssl": {}},
    )


def init_db():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS imoveis (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                logradouro TEXT NOT NULL,
                tipo_logradouro TEXT,
                bairro TEXT,
                cidade TEXT NOT NULL,
                cep TEXT,
                tipo TEXT,
                valor DOUBLE,  -- no Aiven (modo ANSI) REAL vira FLOAT e perde os centavos
                data_aquisicao TEXT
            )
        """
        )
    conn.commit()
    conn.close()


init_db()


CAMPOS_OBRIGATORIOS = [
    "logradouro",
    "tipo_logradouro",
    "bairro",
    "cidade",
    "cep",
    "tipo",
    "valor",
    "data_aquisicao",
]


def campos_faltando(dados):
    return [c for c in CAMPOS_OBRIGATORIOS if c not in dados]


# Função Auxiliar para Nível 3 de Richardson (HATEOAS)
def adicionar_links(imovel):
    imovel_com_links = dict(imovel)
    imovel_com_links["_links"] = {
        "self": f"/imoveis/{imovel['id']}",
        "update": f"/imoveis/{imovel['id']}",
        "delete": f"/imoveis/{imovel['id']}",
    }
    return imovel_com_links


# 1. LISTAR TODOS OS IMÓVEIS (com filtros e HATEOAS)
@app.route("/imoveis", methods=["GET"])
def listar_imoveis():
    tipo = request.args.get("tipo")
    cidade = request.args.get("cidade")

    query = "SELECT * FROM imoveis WHERE 1=1"
    params = []

    if tipo:
        query += " AND LOWER(tipo) = LOWER(%s)"
        params.append(tipo)

    if cidade:
        query += " AND LOWER(cidade) = LOWER(%s)"
        params.append(cidade)

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        imoveis = cursor.fetchall()
    conn.close()

    imoveis_com_links = [adicionar_links(i) for i in imoveis]
    return jsonify(imoveis_com_links), 200


# 2. ADICIONAR IMÓVEL (POST com HATEOAS)
@app.route("/imoveis", methods=["POST"])
def adicionar_imovel():
    dados = request.get_json(silent=True) or {}
    faltando = campos_faltando(dados)
    if faltando:
        return jsonify({"erro": f"Campos obrigatórios ausentes: {faltando}"}), 400

    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = f"INSERT INTO imoveis ({', '.join(CAMPOS_OBRIGATORIOS)}) VALUES ({', '.join(['%s'] * len(CAMPOS_OBRIGATORIOS))})"
        cursor.execute(sql, [dados[c] for c in CAMPOS_OBRIGATORIOS])
        novo_id = cursor.lastrowid
    conn.commit()
    conn.close()

    novo_imovel = {"id": novo_id, **{c: dados[c] for c in CAMPOS_OBRIGATORIOS}}
    return jsonify(adicionar_links(novo_imovel)), 201


# 3. BUSCAR IMÓVEL POR ID (GET com HATEOAS)
@app.route("/imoveis/<int:imovel_id>", methods=["GET"])
def buscar_imovel_por_id(imovel_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM imoveis WHERE id = %s", (imovel_id,))
        imovel = cursor.fetchone()
    conn.close()

    if imovel:
        return jsonify(adicionar_links(imovel)), 200

    return jsonify({"erro": "Imóvel não encontrado"}), 404


# 4. ATUALIZAR IMÓVEL (PUT com HATEOAS)
@app.route("/imoveis/<int:imovel_id>", methods=["PUT"])
def atualizar_imovel(imovel_id):
    dados = request.get_json(silent=True) or {}
    faltando = campos_faltando(dados)
    if faltando:
        return jsonify({"erro": f"Campos obrigatórios ausentes: {faltando}"}), 400

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM imoveis WHERE id = %s", (imovel_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"erro": "Imóvel não encontrado"}), 404

        sql = f"UPDATE imoveis SET {', '.join(f'{c}=%s' for c in CAMPOS_OBRIGATORIOS)} WHERE id=%s"
        cursor.execute(sql, [dados[c] for c in CAMPOS_OBRIGATORIOS] + [imovel_id])
        conn.commit()

        cursor.execute("SELECT * FROM imoveis WHERE id = %s", (imovel_id,))
        imovel_atualizado = cursor.fetchone()

    conn.close()
    return jsonify(adicionar_links(imovel_atualizado)), 200


# 5. REMOVER IMÓVEL (DELETE)
@app.route("/imoveis/<int:imovel_id>", methods=["DELETE"])
def remover_imovel(imovel_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM imoveis WHERE id = %s", (imovel_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"erro": "Imóvel não encontrado"}), 404

        cursor.execute("DELETE FROM imoveis WHERE id = %s", (imovel_id,))
        conn.commit()

    conn.close()
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)