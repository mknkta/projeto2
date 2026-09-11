from flask import Flask, jsonify, request  # <-- Importamos 'request'

app = Flask(__name__)

imoveis_db = []

@app.route("/imoveis", methods=["GET"])
def listar_imoveis():
    return jsonify(imoveis_db), 200


# ROTA NOVA
@app.route("/imoveis", methods=["POST"])
def adicionar_imovel():
    # 1. Pega os dados enviados pelo teste/cliente
    dados = request.get_json()
    
    # 2. Gera um ID unico usando o tamanho da lista
    novo_id = len(imoveis_db) + 1
    
    # 3. Monta o dicionario do imóvel
    novo_imovel = {
        "id": novo_id,
        "titulo": dados["titulo"],
        "tipo": dados["tipo"],
        "cidade": dados["cidade"],
        "preco": dados["preco"]
    }
    
    # 4. Salva no nosso "banco" temporario
    imoveis_db.append(novo_imovel)
    
    # 5. Retorna o imóvel criado com código 201 (Created)
    return jsonify(novo_imovel), 201


if __name__ == "__main__":
    app.run(debug=True)