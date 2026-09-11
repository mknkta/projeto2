import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_listar_todos_imoveis_retorna_200_e_lista(client):
    response = client.get("/imoveis")
    assert response.status_code == 200
    assert response.is_json
    assert isinstance(response.get_json(), list)
    
def test_adicionar_imovel_com_sucesso(client):
    novo_imovel = {
        "titulo": "Casa de Praia",
        "tipo": "casa",
        "cidade": "Santos",
        "preco": 750000.0
    }
    
    # Faz um POST enviando dados no formato JSON
    response = client.post("/imoveis", json=novo_imovel)
    
    # 201 Created é o padrao REST para criacao com sucesso
    assert response.status_code == 201
    assert response.is_json
    
    dados = response.get_json()
    assert "id" in dados
    assert dados["titulo"] == "Casa de Praia"
    
    
    
def test_atualizar_imovel_com_sucesso(client):
    # 1. Criamos um imóvel para ter certeza do que vamos atualizar
    novo = {"titulo": "Casa Velha", "tipo": "casa", "cidade": "Santos", "preco": 300000.0}
    res_post = client.post("/imoveis", json=novo)
    imovel_id = res_post.get_json()["id"]

    # 2. Enviamos requisição PUT com os dados novos
    dados_atualizados = {
        "titulo": "Casa Reformada",
        "tipo": "casa",
        "cidade": "Santos",
        "preco": 450000.0
    }
    response = client.put(f"/imoveis/{imovel_id}", json=dados_atualizados)

    # 3. Validamos a resposta
    assert response.status_code == 200
    assert response.get_json()["titulo"] == "Casa Reformada"
    assert response.get_json()["preco"] == 450000.0


def test_atualizar_imovel_nao_encontrado(client):
    # Tentamos atualizar um ID inexistente
    dados = {"titulo": "Novo Titulo", "tipo": "casa", "cidade": "Santos", "preco": 100000.0}
    response = client.put("/imoveis/999999", json=dados)
    
    assert response.status_code == 404