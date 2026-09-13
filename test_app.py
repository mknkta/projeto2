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
    
    
    
def test_adicionar_imovel_sem_campos_obrigatorios_retorna_400(client):
    response = client.post("/imoveis", json={"titulo": "Casa Incompleta"})
    assert response.status_code == 400


def test_buscar_imovel_por_id_com_sucesso(client):
    novo = {"titulo": "Sitio", "tipo": "terreno", "cidade": "Ibiuna", "preco": 200000.0}
    res_post = client.post("/imoveis", json=novo)
    imovel_id = res_post.get_json()["id"]

    response = client.get(f"/imoveis/{imovel_id}")
    assert response.status_code == 200
    dados = response.get_json()
    assert dados["titulo"] == "Sitio"
    assert dados["tipo"] == "terreno"
    assert dados["cidade"] == "Ibiuna"
    assert dados["preco"] == 200000.0


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


def test_atualizar_imovel_sem_campos_obrigatorios_retorna_400(client):
    novo = {"titulo": "Casa", "tipo": "casa", "cidade": "Santos", "preco": 300000.0}
    res_post = client.post("/imoveis", json=novo)
    imovel_id = res_post.get_json()["id"]

    response = client.put(f"/imoveis/{imovel_id}", json={"titulo": "Sem os outros campos"})
    assert response.status_code == 400


def test_atualizar_imovel_nao_encontrado(client):
    # Tentamos atualizar um ID inexistente
    dados = {"titulo": "Novo Titulo", "tipo": "casa", "cidade": "Santos", "preco": 100000.0}
    response = client.put("/imoveis/999999", json=dados)
    
    assert response.status_code == 404
def test_remover_imovel_com_sucesso(client):
    # 1. Cria um imóvel temporário para deletar
    novo = {"titulo": "Terreno Vazio", "tipo": "terreno", "cidade": "Curitiba", "preco": 150000.0}
    res_post = client.post("/imoveis", json=novo)
    imovel_id = res_post.get_json()["id"]

    # 2. Faz a requisição DELETE
    response = client.delete(f"/imoveis/{imovel_id}")
    assert response.status_code == 204

    # 3. Prova real: tenta buscar o imóvel deletado e espera receber 404
    res_get = client.get(f"/imoveis/{imovel_id}")
    assert res_get.status_code == 404


def test_remover_imovel_nao_encontrado(client):
    response = client.delete("/imoveis/999999")
    assert response.status_code == 404

def test_filtrar_imoveis_por_tipo(client):
    # 1. Cadastra dois imóveis de tipos diferentes
    client.post("/imoveis", json={"titulo": "Casa 1", "tipo": "casa", "cidade": "SP", "preco": 300000.0})
    client.post("/imoveis", json={"titulo": "Apto 1", "tipo": "apartamento", "cidade": "SP", "preco": 400000.0})

    # 2. Busca filtrando apenas por tipo "casa"
    response = client.get("/imoveis?tipo=casa")
    assert response.status_code == 200
    
    dados = response.get_json()
    assert len(dados) >= 1
    assert all(imovel["tipo"] == "casa" for imovel in dados)


def test_filtrar_imoveis_por_cidade(client):
    # 1. Cadastra dois imóveis de cidades diferentes
    client.post("/imoveis", json={"titulo": "Casa Santos", "tipo": "casa", "cidade": "Santos", "preco": 500000.0})
    client.post("/imoveis", json={"titulo": "Casa SP", "tipo": "casa", "cidade": "Sao Paulo", "preco": 600000.0})

    # 2. Busca filtrando apenas por cidade "Santos"
    response = client.get("/imoveis?cidade=Santos")
    assert response.status_code == 200
    
    dados = response.get_json()
    assert len(dados) >= 1
    assert all(imovel["cidade"] == "Santos" for imovel in dados)
    
def test_respostas_contem_links_hateoas(client):
    novo = {"titulo": "Cobertura", "tipo": "apartamento", "cidade": "SP", "preco": 1200000.0}
    response = client.post("/imoveis", json=novo)
    dados = response.get_json()

    # Valida se a propriedade _links existe e contém self, update e delete
    assert "_links" in dados
    assert "self" in dados["_links"]
    assert "update" in dados["_links"]
    assert "delete" in dados["_links"]