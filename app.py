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
                id INT AUTO_INCREMENT PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                tipo VARCHAR(50) NOT NULL,
                cidade VARCHAR(100) NOT NULL,
                preco FLOAT NOT NULL
            )
        """
        )
    conn.commit()
    conn.close()


init_db()


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
    dados = request.get_json()

    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = "INSERT INTO imoveis (titulo, tipo, cidade, preco) VALUES (%s, %s, %s, %s)"
        cursor.execute(
            sql,
            (dados["titulo"], dados["tipo"], dados["cidade"], dados["preco"]),
        )
        novo_id = cursor.lastrowid
    conn.commit()
    conn.close()

    novo_imovel = {
        "id": novo_id,
        "titulo": dados["titulo"],
        "tipo": dados["tipo"],
        "cidade": dados["cidade"],
        "preco": dados["preco"],
    }
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
    dados = request.get_json()

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM imoveis WHERE id = %s", (imovel_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"erro": "Imóvel não encontrado"}), 404

        sql = "UPDATE imoveis SET titulo=%s, tipo=%s, cidade=%s, preco=%s WHERE id=%s"
        cursor.execute(
            sql,
            (
                dados["titulo"],
                dados["tipo"],
                dados["cidade"],
                dados["preco"],
                imovel_id,
            ),
        )
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