# ============================================================================
# app.py  ->  ARQUIVO PRINCIPAL DA API
# Uma "API" é um programa que fica esperando pedidos (requisições) pela internet
# e responde com dados. Aqui a API guarda imóveis (casas, apartamentos...) num
# banco de dados e deixa você: listar, criar, buscar, atualizar e apagar (CRUD).
# ============================================================================

# "import" = trazer código pronto de outra biblioteca para usar aqui.
import os  # módulo do Python para ler variáveis do sistema (ex: senha do banco)
from flask import Flask, jsonify, request
# Flask   = framework (kit de ferramentas) para criar sites/APIs em Python
# jsonify = transforma dados do Python (dict/lista) em JSON (texto que a internet entende)
# request = objeto com tudo que o cliente mandou no pedido (dados, filtros na URL...)
import pymysql  # biblioteca para conversar com o banco de dados MySQL
from dotenv import load_dotenv  # lê o arquivo ".env" (onde ficam as senhas)

# Lê o arquivo .env e coloca o conteúdo como variáveis de ambiente.
# Assim a senha do banco NÃO fica escrita no código (segurança).
load_dotenv()

# Cria a aplicação Flask. __name__ é o nome deste arquivo; o Flask usa para se localizar.
app = Flask(__name__)


def get_db_connection():
    # "def" cria uma FUNÇÃO (bloco de código reutilizável com um nome).
    # Esta função abre uma conexão nova com o banco e devolve ela.
    return pymysql.connect(
        host=os.getenv("DB_HOST"),  # endereço do servidor do banco (lido do .env)
        port=int(os.getenv("DB_PORT", 3306)),  # porta; se não existir no .env usa 3306 (padrão do MySQL). int() converte texto em número
        user=os.getenv("DB_USER"),  # usuário do banco
        password=os.getenv("DB_PASSWORD"),  # senha do banco
        database=os.getenv("DB_NAME"),  # nome do banco de dados
        cursorclass=pymysql.cursors.DictCursor,  # faz cada linha do banco vir como dicionário {"coluna": valor} em vez de tupla
        ssl={"ssl": {}},  # liga conexão criptografada (o Aiven exige isso)
    )


def init_db():
    # Cria a tabela "imoveis" se ela ainda não existir.
    conn = get_db_connection()  # abre conexão com o banco
    with conn.cursor() as cursor:
        # cursor = "ponteiro" usado para mandar comandos SQL ao banco.
        # "with" garante que o cursor é fechado sozinho no fim do bloco.
        cursor.execute(
            # SQL = linguagem dos bancos de dados. Texto entre """ """ pode ter várias linhas.
            """
            CREATE TABLE IF NOT EXISTS imoveis (  -- cria a tabela só se não existir
                id INTEGER PRIMARY KEY AUTO_INCREMENT,  -- número único; PRIMARY KEY = identifica a linha; AUTO_INCREMENT = o banco conta 1,2,3... sozinho
                logradouro TEXT NOT NULL,  -- nome da rua; NOT NULL = obrigatório
                tipo_logradouro TEXT,  -- "Rua", "Avenida"... (pode ficar vazio)
                bairro TEXT,
                cidade TEXT NOT NULL,  -- obrigatório
                cep TEXT,
                tipo TEXT,  -- casa, apartamento, terreno...
                valor DOUBLE,  -- preço; DOUBLE = número com casas decimais
                data_aquisicao TEXT  -- data em que foi comprado
            )
        """
        )
    conn.commit()  # commit = "salvar de verdade" as alterações no banco
    conn.close()  # fecha a conexão (boa prática, libera recurso)


init_db()  # chama a função acima assim que o programa inicia, garantindo que a tabela existe


# Lista de campos que o cliente É OBRIGADO a mandar em POST e PUT.
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
    # Recebe o JSON enviado (dict) e devolve a lista dos campos obrigatórios que NÃO estão nele.
    # [c for c in LISTA if condição] = "list comprehension": monta uma lista filtrando.
    # Lê-se: "para cada campo c da lista de obrigatórios, guarde c se c não estiver em dados".
    return [c for c in CAMPOS_OBRIGATORIOS if c not in dados]


# Função Auxiliar para Nível 3 de Richardson (HATEOAS)
# HATEOAS = a resposta da API já traz LINKS dizendo o que você pode fazer em seguida.
# Modelo de Maturidade de Richardson: nível 0,1,2,3. O nível 3 é usar HATEOAS.
def adicionar_links(imovel):
    imovel_com_links = dict(imovel)  # cria uma CÓPIA do imóvel (para não alterar o original)
    imovel_com_links["_links"] = {  # adiciona a chave "_links" com os links úteis
        "self": f"/imoveis/{imovel['id']}",    # link do próprio imóvel (f"..." insere o valor de id no texto)
        "update": f"/imoveis/{imovel['id']}",  # onde atualizar (usando PUT)
        "delete": f"/imoveis/{imovel['id']}",  # onde apagar (usando DELETE)
    }
    return imovel_com_links  # devolve o imóvel já com os links


# 1. LISTAR TODOS OS IMÓVEIS (com filtros e HATEOAS)
# @app.route = "decorador": liga uma URL + método HTTP a esta função.
# GET = método HTTP para LER/buscar dados.
@app.route("/imoveis", methods=["GET"])
def listar_imoveis():
    # request.args = parâmetros da URL depois do "?". Ex: /imoveis?tipo=casa&cidade=Santos
    tipo = request.args.get("tipo")  # pega o valor de "tipo" (ou None se não veio)
    cidade = request.args.get("cidade")  # idem para "cidade"

    query = "SELECT * FROM imoveis WHERE 1=1"  # SELECT * = pega todas as colunas. "1=1" é sempre verdadeiro: truque para poder encadear "AND ..." depois
    params = []  # lista dos valores que vão substituir os %s (evita SQL Injection)

    if tipo:  # se o cliente mandou um tipo...
        query += " AND LOWER(tipo) = LOWER(%s)"  # ...acrescenta filtro; LOWER ignora maiúsculas/minúsculas; %s é um "buraco" preenchido depois
        params.append(tipo)  # guarda o valor que vai no buraco

    if cidade:  # se mandou cidade...
        query += " AND LOWER(cidade) = LOWER(%s)"
        params.append(cidade)

    conn = get_db_connection()  # abre conexão
    with conn.cursor() as cursor:
        cursor.execute(query, params)  # roda o SQL; o pymysql troca os %s pelos params de forma SEGURA
        imoveis = cursor.fetchall()  # fetchall = pega TODAS as linhas do resultado (lista de dicts)
    conn.close()  # fecha conexão

    imoveis_com_links = [adicionar_links(i) for i in imoveis]  # coloca _links em cada imóvel
    return jsonify(imoveis_com_links), 200  # devolve JSON + status 200 (OK)


# 2. ADICIONAR IMÓVEL (POST com HATEOAS)
# POST = método HTTP para CRIAR algo novo.
@app.route("/imoveis", methods=["POST"])
def adicionar_imovel():
    # get_json lê o corpo (body) do pedido. silent=True evita erro se vier lixo.
    # "or {}" -> se vier vazio/None, usa um dicionário vazio.
    dados = request.get_json(silent=True) or {}
    faltando = campos_faltando(dados)  # descobre quais campos obrigatórios não vieram
    if faltando:  # lista não vazia = tem campo faltando
        # 400 = Bad Request (o cliente errou o pedido)
        return jsonify({"erro": f"Campos obrigatórios ausentes: {faltando}"}), 400

    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Monta o INSERT dinamicamente:
        #  ', '.join(CAMPOS_OBRIGATORIOS)      -> "logradouro, tipo_logradouro, ..."
        #  ', '.join(['%s'] * len(...))         -> "%s, %s, %s, ..." (um buraco por campo)
        sql = f"INSERT INTO imoveis ({', '.join(CAMPOS_OBRIGATORIOS)}) VALUES ({', '.join(['%s'] * len(CAMPOS_OBRIGATORIOS))})"
        # Lista com os valores, na MESMA ordem dos campos, para preencher os %s
        cursor.execute(sql, [dados[c] for c in CAMPOS_OBRIGATORIOS])
        novo_id = cursor.lastrowid  # id que o banco gerou (AUTO_INCREMENT) para a linha nova
    conn.commit()  # salva no banco (sem commit o INSERT some)
    conn.close()

    # Monta o dict do novo imóvel: id + todos os campos. "**" espalha o dicionário dentro do outro.
    novo_imovel = {"id": novo_id, **{c: dados[c] for c in CAMPOS_OBRIGATORIOS}}
    return jsonify(adicionar_links(novo_imovel)), 201  # 201 = Created (criado com sucesso)


# 3. BUSCAR IMÓVEL POR ID (GET com HATEOAS)
# <int:imovel_id> = parte variável da URL, precisa ser número inteiro. Ex: /imoveis/5 -> imovel_id=5
@app.route("/imoveis/<int:imovel_id>", methods=["GET"])
def buscar_imovel_por_id(imovel_id):  # o número da URL chega como parâmetro da função
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM imoveis WHERE id = %s", (imovel_id,))  # (x,) = tupla de 1 item (a vírgula é obrigatória)
        imovel = cursor.fetchone()  # fetchone = pega UMA linha (ou None se não existe)
    conn.close()

    if imovel:  # achou
        return jsonify(adicionar_links(imovel)), 200

    return jsonify({"erro": "Imóvel não encontrado"}), 404  # 404 = Not Found


# 4. ATUALIZAR IMÓVEL (PUT com HATEOAS)
# PUT = método HTTP para SUBSTITUIR/atualizar um item existente (por isso exige todos os campos).
@app.route("/imoveis/<int:imovel_id>", methods=["PUT"])
def atualizar_imovel(imovel_id):
    dados = request.get_json(silent=True) or {}
    faltando = campos_faltando(dados)
    if faltando:
        return jsonify({"erro": f"Campos obrigatórios ausentes: {faltando}"}), 400

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM imoveis WHERE id = %s", (imovel_id,))  # primeiro confere se o imóvel existe
        if not cursor.fetchone():  # não existe
            conn.close()
            return jsonify({"erro": "Imóvel não encontrado"}), 404

        # Monta "UPDATE imoveis SET logradouro=%s, bairro=%s, ... WHERE id=%s"
        sql = f"UPDATE imoveis SET {', '.join(f'{c}=%s' for c in CAMPOS_OBRIGATORIOS)} WHERE id=%s"
        # valores dos campos + o id no final (é o último %s)
        cursor.execute(sql, [dados[c] for c in CAMPOS_OBRIGATORIOS] + [imovel_id])
        conn.commit()  # salva

        cursor.execute("SELECT * FROM imoveis WHERE id = %s", (imovel_id,))  # busca de novo para devolver o dado atualizado
        imovel_atualizado = cursor.fetchone()

    conn.close()
    return jsonify(adicionar_links(imovel_atualizado)), 200  # 200 = OK


# 5. REMOVER IMÓVEL (DELETE)
# DELETE = método HTTP para APAGAR.
@app.route("/imoveis/<int:imovel_id>", methods=["DELETE"])
def remover_imovel(imovel_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM imoveis WHERE id = %s", (imovel_id,))  # confere se existe
        if not cursor.fetchone():
            conn.close()
            return jsonify({"erro": "Imóvel não encontrado"}), 404

        cursor.execute("DELETE FROM imoveis WHERE id = %s", (imovel_id,))  # apaga a linha
        conn.commit()  # salva

    conn.close()
    return "", 204  # 204 = No Content (deu certo e não há nada para devolver)


# Só roda quando você executa "python app.py" diretamente (não quando é importado pelos testes).
if __name__ == "__main__":
    app.run(debug=True)  # sobe o servidor local; debug=True recarrega sozinho e mostra erros detalhados (só p/ desenvolvimento)
