from flask import Flask, jsonify, request

app = Flask(__name__)

imoveis_db = []


# 1. LISTAR TODOS OS IMÓVEIS (com suporte a filtros por tipo e cidade)
@app.route("/imoveis", methods=["GET"])
def listar_imoveis():
    tipo = request.args.get("tipo")
    cidade = request.args.get("cidade")

    resultado = imoveis_db

    if tipo:
        resultado = [i for i in resultado if i["tipo"].lower() == tipo.lower()]

    if cidade:
        resultado = [i for i in resultado if i["cidade"].lower() == cidade.lower()]

    return jsonify(resultado), 200


# 2. ADICIONAR IMÓVEL (POST)
@app.route("/imoveis", methods=["POST"])
def adicionar_imovel():
    dados = request.get_json()
    novo_id = len(imoveis_db) + 1
    novo_imovel = {
        "id": novo_id,
        "titulo": dados["titulo"],
        "tipo": dados["tipo"],
        "cidade": dados["cidade"],
        "preco": dados["preco"],
    }
    imoveis_db.append(novo_imovel)
    return jsonify(novo_imovel), 201


# 3. BUSCAR IMÓVEL POR ID (GET)
@app.route("/imoveis/<int:imovel_id>", methods=["GET"])
def buscar_imovel_por_id(imovel_id):
    for imovel in imoveis_db:
        if imovel["id"] == imovel_id:
            return jsonify(imovel), 200
    return jsonify({"erro": "Imóvel não encontrado"}), 404


# 4. ATUALIZAR IMÓVEL (PUT)
@app.route("/imoveis/<int:imovel_id>", methods=["PUT"])
def atualizar_imovel(imovel_id):
    dados = request.get_json()
    for imovel in imoveis_db:
        if imovel["id"] == imovel_id:
            imovel["titulo"] = dados["titulo"]
            imovel["tipo"] = dados["tipo"]
            imovel["cidade"] = dados["cidade"]
            imovel["preco"] = dados["preco"]
            return jsonify(imovel), 200
    return jsonify({"erro": "Imóvel não encontrado"}), 404


# 5. REMOVER IMÓVEL (DELETE)
@app.route("/imoveis/<int:imovel_id>", methods=["DELETE"])
def remover_imovel(imovel_id):
    for imovel in imoveis_db:
        if imovel["id"] == imovel_id:
            imoveis_db.remove(imovel)
            return "", 204
    return jsonify({"erro": "Imóvel não encontrado"}), 404


if __name__ == "__main__":
    app.run(debug=True)