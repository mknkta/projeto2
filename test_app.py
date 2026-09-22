# ============================================================================
# test_app.py -> TESTES AUTOMÁTICOS
# Teste automático = código que usa a sua API sozinho e confere se a resposta é a esperada.
# Rodar com o comando:  pytest
# "assert X" significa "afirmo que X é verdade"; se for falso, o teste FALHA.
# ============================================================================
import os  # ler/alterar variáveis de ambiente
import pymysql  # conversar com o MySQL
import pytest  # framework de testes
from dotenv import load_dotenv  # ler o .env

# Os testes usam um banco separado (ex: defaultdb_teste) para não sujar os dados reais
load_dotenv()  # carrega as variáveis do .env
os.environ["DB_NAME"] += "_teste"  # troca o nome do banco para "<nome>_teste" ANTES de importar o app
with pymysql.connect(  # conecta SEM escolher banco (ele talvez ainda não exista)
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    ssl={"ssl": {}},
) as conn:  # "with" fecha a conexão sozinho no final
    # cria o banco de teste se ainda não existir
    conn.cursor().execute(f"CREATE DATABASE IF NOT EXISTS {os.environ['DB_NAME']}")

from app import app  # só agora importa o app (ele já vai usar o banco de teste)


# Imóvel base no formato da tabela do imoveis.sql
IMOVEL = {
    "logradouro": "Rua das Flores",
    "tipo_logradouro": "Rua",
    "bairro": "Gonzaga",
    "cidade": "Santos",
    "cep": "11060",
    "tipo": "casa",
    "valor": 750000.0,
    "data_aquisicao": "2020-01-15",
}


def imovel(**campos):
    # Devolve uma cópia do IMOVEL base trocando só os campos passados.
    # Ex: imovel(tipo="terreno") -> igual ao base, mas com tipo="terreno".
    # **campos = recebe argumentos nomeados como dicionário; o segundo ** espalha os dicts (o da direita vence).
    return {**IMOVEL, **campos}


@pytest.fixture  # fixture = preparação que o pytest entrega aos testes que a pedirem
def client():
    app.config["TESTING"] = True  # modo de teste do Flask (erros viram exceções visíveis)
    with app.test_client() as client:  # test_client = "navegador falso" que faz requisições sem subir servidor
        yield client  # entrega o client ao teste; depois do teste, o "with" limpa tudo


def test_listar_todos_imoveis_retorna_200_e_lista(client):  # o pytest acha funções que começam com "test_"
    response = client.get("/imoveis")  # faz GET /imoveis
    assert response.status_code == 200  # código HTTP tem que ser 200 (OK)
    assert response.is_json  # a resposta tem que ser JSON
    assert isinstance(response.get_json(), list)  # o JSON tem que ser uma lista

def test_adicionar_imovel_com_sucesso(client):
    # Faz um POST enviando dados no formato JSON
    response = client.post("/imoveis", json=IMOVEL)

    # 201 Created é o padrao REST para criacao com sucesso
    assert response.status_code == 201
    assert response.is_json

    dados = response.get_json()  # converte a resposta JSON em dict Python
    assert "id" in dados  # o banco tem que ter gerado um id
    assert dados["logradouro"] == "Rua das Flores"  # e o dado tem que voltar igual



def test_adicionar_imovel_sem_campos_obrigatorios_retorna_400(client):
    response = client.post("/imoveis", json={"logradouro": "Rua Incompleta"})  # manda só 1 campo
    assert response.status_code == 400  # tem que dar erro do cliente


def test_buscar_imovel_por_id_com_sucesso(client):
    novo = imovel(logradouro="Estrada do Sitio", tipo="terreno", cidade="Ibiuna", valor=200000.0)
    res_post = client.post("/imoveis", json=novo)  # cria um imóvel
    imovel_id = res_post.get_json()["id"]  # guarda o id gerado

    response = client.get(f"/imoveis/{imovel_id}")  # busca pelo id
    assert response.status_code == 200
    dados = response.get_json()
    assert dados["logradouro"] == "Estrada do Sitio"  # confere cada campo
    assert dados["tipo"] == "terreno"
    assert dados["cidade"] == "Ibiuna"
    assert dados["valor"] == 200000.0


def test_atualizar_imovel_com_sucesso(client):
    # 1. Criamos um imóvel para ter certeza do que vamos atualizar
    res_post = client.post("/imoveis", json=imovel(valor=300000.0))
    imovel_id = res_post.get_json()["id"]

    # 2. Enviamos requisição PUT com os dados novos
    dados_atualizados = imovel(logradouro="Rua Reformada", valor=450000.0)
    response = client.put(f"/imoveis/{imovel_id}", json=dados_atualizados)

    # 3. Validamos a resposta
    assert response.status_code == 200
    assert response.get_json()["logradouro"] == "Rua Reformada"
    assert response.get_json()["valor"] == 450000.0


def test_atualizar_imovel_sem_campos_obrigatorios_retorna_400(client):
    res_post = client.post("/imoveis", json=IMOVEL)
    imovel_id = res_post.get_json()["id"]

    # PUT com dados incompletos -> 400
    response = client.put(f"/imoveis/{imovel_id}", json={"logradouro": "Sem os outros campos"})
    assert response.status_code == 400


def test_atualizar_imovel_nao_encontrado(client):
    # Tentamos atualizar um ID inexistente
    response = client.put("/imoveis/999999", json=IMOVEL)

    assert response.status_code == 404  # 404 = não encontrado
def test_remover_imovel_com_sucesso(client):
    # 1. Cria um imóvel temporário para deletar
    novo = imovel(tipo="terreno", cidade="Curitiba", valor=150000.0)
    res_post = client.post("/imoveis", json=novo)
    imovel_id = res_post.get_json()["id"]

    # 2. Faz a requisição DELETE
    response = client.delete(f"/imoveis/{imovel_id}")
    assert response.status_code == 204  # 204 = apagou, sem conteúdo na resposta

    # 3. Prova real: tenta buscar o imóvel deletado e espera receber 404
    res_get = client.get(f"/imoveis/{imovel_id}")
    assert res_get.status_code == 404


def test_remover_imovel_nao_encontrado(client):
    response = client.delete("/imoveis/999999")  # id que não existe
    assert response.status_code == 404

def test_filtrar_imoveis_por_tipo(client):
    # 1. Cadastra dois imóveis de tipos diferentes
    client.post("/imoveis", json=imovel(tipo="casa", cidade="SP"))
    client.post("/imoveis", json=imovel(tipo="apartamento", cidade="SP"))

    # 2. Busca filtrando apenas por tipo "casa"
    response = client.get("/imoveis?tipo=casa")
    assert response.status_code == 200

    dados = response.get_json()
    assert len(dados) >= 1  # veio pelo menos um
    assert all(i["tipo"] == "casa" for i in dados)  # all() = TODOS os itens precisam ser "casa"


def test_filtrar_imoveis_por_cidade(client):
    # 1. Cadastra dois imóveis de cidades diferentes
    client.post("/imoveis", json=imovel(cidade="Santos"))
    client.post("/imoveis", json=imovel(cidade="Sao Paulo"))

    # 2. Busca filtrando apenas por cidade "Santos"
    response = client.get("/imoveis?cidade=Santos")
    assert response.status_code == 200

    dados = response.get_json()
    assert len(dados) >= 1
    assert all(i["cidade"] == "Santos" for i in dados)

def test_respostas_contem_links_hateoas(client):
    response = client.post("/imoveis", json=imovel(tipo="apartamento", valor=1200000.0))
    dados = response.get_json()

    # Valida se a propriedade _links existe e contém self, update e delete
    assert "_links" in dados
    assert "self" in dados["_links"]
    assert "update" in dados["_links"]
    assert "delete" in dados["_links"]
