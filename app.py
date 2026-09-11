from flask import Flask, jsonify

app = Flask(__name__)

imoveis_db = []


@app.route("/imoveis", methods=["GET"])
def listar_imoveis():
    return jsonify(imoveis_db), 200


if __name__ == "__main__":
    app.run(debug=True)