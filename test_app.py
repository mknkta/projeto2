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