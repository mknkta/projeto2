# projeto2

API RESTful de uma imobiliária, feita em Flask com banco de dados MySQL hospedado no Aiven.

API disponível em: http://3.131.133.149:5000/imoveis

---

# 📚 GUIA DE ESTUDO PARA A PROVA (explicado do zero)

## 1. Conceitos básicos (leia primeiro)

| Termo | O que é (em português simples) |
|---|---|
| **Cliente** | Quem faz o pedido (navegador, app, Postman, os testes). |
| **Servidor** | Quem recebe o pedido e responde (nosso programa Flask). |
| **API** | "Garçom" entre cliente e banco: o cliente pede, a API busca/salva e devolve a resposta. |
| **REST / RESTful** | Um jeito padrão de montar APIs usando URLs (recursos) + métodos HTTP. |
| **HTTP** | O "idioma" da web: pedido (request) e resposta (response). |
| **JSON** | Formato de texto para trocar dados: `{"cidade": "Santos", "valor": 750000.0}`. Parecido com dicionário do Python. |
| **Recurso** | A "coisa" que a API gerencia. Aqui: `imoveis`. |
| **Endpoint / Rota** | Uma URL + método. Ex: `GET /imoveis`. |
| **Banco de dados** | Onde os dados ficam guardados para sempre (MySQL). |
| **SQL** | Linguagem para falar com o banco (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). |
| **CRUD** | Create, Read, Update, Delete = Criar, Ler, Atualizar, Apagar. As 4 operações básicas. |
| **Flask** | Biblioteca Python para criar a API. |
| **Aiven** | Empresa que hospeda o MySQL na nuvem. |
| **.env** | Arquivo secreto com senhas/host do banco (não vai pro Git). |
| **Deploy** | Colocar a API no ar num servidor (aqui, um IP na AWS, usando gunicorn). |
| **gunicorn** | Servidor de produção para rodar Flask de verdade (o `app.run` é só para testes locais). |

## 2. Métodos HTTP ↔ CRUD (DECORE ESTA TABELA!)

| Operação | Método HTTP | Rota | SQL usado | Status de sucesso |
|---|---|---|---|---|
| Listar todos | **GET** | `/imoveis` | `SELECT` | 200 |
| Buscar um | **GET** | `/imoveis/<id>` | `SELECT ... WHERE id` | 200 |
| Criar | **POST** | `/imoveis` | `INSERT` | **201** |
| Atualizar | **PUT** | `/imoveis/<id>` | `UPDATE` | 200 |
| Apagar | **DELETE** | `/imoveis/<id>` | `DELETE` | **204** |

## 3. Códigos de status HTTP (cai muito em prova)

| Código | Nome | Quando aparece aqui |
|---|---|---|
| **200** | OK | GET/PUT deu certo |
| **201** | Created | POST criou o imóvel |
| **204** | No Content | DELETE apagou (resposta vazia) |
| **400** | Bad Request | Cliente esqueceu campo obrigatório |
| **404** | Not Found | Id não existe |

Regra de bolso: **2xx** = sucesso, **4xx** = erro do cliente, **5xx** = erro do servidor.

## 4. Níveis de Richardson e HATEOAS

Modelo que mede o quão "REST" uma API é:

- **Nível 0**: uma única URL para tudo (só usa HTTP como "túnel").
- **Nível 1**: **recursos** — cada coisa tem sua URL (`/imoveis/5`).
- **Nível 2**: usa os **métodos HTTP** certos (GET, POST, PUT, DELETE) e **status codes** certos.
- **Nível 3**: **HATEOAS** — a resposta traz **links** (`_links`) dizendo o que dá para fazer depois.

Nossa API é **nível 3**. Exemplo de resposta:

```json
{
  "id": 1,
  "logradouro": "Rua das Flores",
  "cidade": "Santos",
  "valor": 750000.0,
  "_links": {
    "self": "/imoveis/1",
    "update": "/imoveis/1",
    "delete": "/imoveis/1"
  }
}
```

## 5. Estrutura do projeto

```
projeto2/
├── app.py            # a API inteira (rotas + banco)
├── test_app.py       # testes automáticos (pytest)
├── requirements.txt  # lista das bibliotecas necessárias
├── .gitignore        # arquivos que o Git deve ignorar (ex: .env)
├── .env              # (NÃO está no Git) senhas do banco
└── README.md         # este arquivo
```

## 6. app.py explicado por partes

1. **Imports**: traz Flask, PyMySQL, dotenv e os.
2. **`load_dotenv()`**: lê o `.env` (host, usuário, senha do banco).
3. **`app = Flask(__name__)`**: cria a aplicação.
4. **`get_db_connection()`**: abre uma conexão com o MySQL. Usa `DictCursor` (linhas viram dicionários) e `ssl` (conexão criptografada, exigida pelo Aiven).
5. **`init_db()`**: cria a tabela `imoveis` se não existir. Colunas: `id`, `logradouro`, `tipo_logradouro`, `bairro`, `cidade`, `cep`, `tipo`, `valor`, `data_aquisicao`. Roda 1 vez quando o programa inicia.
6. **`CAMPOS_OBRIGATORIOS`**: lista dos campos que o cliente precisa mandar.
7. **`campos_faltando(dados)`**: devolve quais campos obrigatórios faltam (validação).
8. **`adicionar_links(imovel)`**: adiciona `_links` (HATEOAS) ao imóvel.
9. **Rotas** (cada uma é uma função com `@app.route`):
   - `listar_imoveis` — `GET /imoveis`, aceita filtros `?tipo=casa&cidade=Santos`.
   - `adicionar_imovel` — `POST /imoveis`, valida → INSERT → devolve 201.
   - `buscar_imovel_por_id` — `GET /imoveis/<id>`, devolve 200 ou 404.
   - `atualizar_imovel` — `PUT /imoveis/<id>`, valida → confere se existe → UPDATE → devolve 200/400/404.
   - `remover_imovel` — `DELETE /imoveis/<id>`, confere se existe → DELETE → 204/404.
10. **`if __name__ == "__main__": app.run(debug=True)`**: só sobe o servidor de teste se rodar `python app.py`.

### Fluxo de um pedido (exemplo: POST)

```
Cliente --POST /imoveis + JSON--> Flask acha a rota certa
   -> adicionar_imovel(): lê JSON -> valida campos
   -> abre conexão -> INSERT -> commit -> fecha
   -> monta resposta com _links
Cliente <--201 + JSON-- Flask
```

## 7. Palavras-chave do código Python que aparecem

| Código | Significado |
|---|---|
| `def nome():` | cria uma função |
| `return x` | devolve x e encerra a função |
| `if / else` | decisão: "se... senão..." |
| `for x in lista` | repete para cada item |
| `[x for x in lista if ...]` | list comprehension: cria lista filtrando/transformando |
| `with ... as ...:` | abre algo e fecha sozinho no final |
| `f"texto {var}"` | f-string: coloca o valor da variável no texto |
| `{**a, **b}` | junta dois dicionários |
| `dict(x)` | copia um dicionário |
| `@algo` | decorador: adiciona comportamento à função de baixo |
| `%s` | "buraco" do SQL preenchido com segurança (evita **SQL Injection**) |
| `os.getenv("X")` | lê a variável de ambiente X |
| `__name__ == "__main__"` | "só execute se este arquivo foi rodado diretamente" |

## 8. Comandos SQL usados

```sql
SELECT * FROM imoveis WHERE id = 5;      -- ler
INSERT INTO imoveis (cidade, ...) VALUES ('Santos', ...);  -- criar
UPDATE imoveis SET cidade='Santos' WHERE id = 5;  -- atualizar
DELETE FROM imoveis WHERE id = 5;         -- apagar
```
- `WHERE` = filtro. **Sem WHERE no UPDATE/DELETE afeta a tabela inteira!**
- `commit()` = salva de verdade. Sem ele, INSERT/UPDATE/DELETE não valem.

## 9. Segurança (pergunta comum)

- **SQL Injection**: atacante escreve SQL malicioso num campo. Defesa: usar `%s` + parâmetros (feito aqui) e nunca colar texto do usuário direto no SQL.
- **Senhas no `.env`**: nunca escrever senha no código nem subir o `.env` no Git.
- **SSL**: criptografa a conexão com o banco.
- **Validação**: conferir campos obrigatórios antes de gravar (devolve 400).

## 10. Testes (`test_app.py`)

- Rodar: `pytest`
- Usam um **banco separado** (`<nome>_teste`) para não estragar dados reais.
- `client` (fixture) = "navegador falso" que chama a API sem subir servidor.
- Cada função `test_...` faz um pedido e usa `assert` para conferir status e conteúdo.
- Cobrem: listar, criar (ok e 400), buscar, atualizar (ok, 400, 404), apagar (ok e 404), filtros por tipo/cidade e presença de `_links`.

## 11. Como rodar

```bash
pip install -r requirements.txt   # instala as bibliotecas
# criar arquivo .env com: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
python app.py                     # sobe local em http://127.0.0.1:5000
pytest                            # roda os testes
gunicorn app:app                  # jeito de produção (deploy)
```

Exemplos de chamada (curl):

```bash
curl http://127.0.0.1:5000/imoveis
curl "http://127.0.0.1:5000/imoveis?tipo=casa&cidade=Santos"
curl -X POST http://127.0.0.1:5000/imoveis -H "Content-Type: application/json" \
  -d '{"logradouro":"Rua A","tipo_logradouro":"Rua","bairro":"Centro","cidade":"Santos","cep":"11000","tipo":"casa","valor":500000,"data_aquisicao":"2020-01-01"}'
curl -X DELETE http://127.0.0.1:5000/imoveis/1
```

## 12. Possíveis perguntas de prova (com resposta rápida)

- **Que método HTTP cria?** POST (retorna 201).
- **E atualiza? E apaga?** PUT (200) e DELETE (204).
- **O que é HATEOAS?** Incluir links na resposta indicando as próximas ações; é o nível 3 de Richardson.
- **Diferença entre 400 e 404?** 400 = pedido inválido (faltam campos); 404 = recurso não existe.
- **Por que usar `%s` no SQL?** Evita SQL Injection.
- **Para que serve `commit()`?** Salvar as alterações no banco.
- **Para que serve o `.env`?** Guardar segredos fora do código.
- **O que é `jsonify`?** Converte dict/lista Python em resposta JSON.
- **O que faz `request.args.get`?** Lê parâmetros da URL (`?tipo=casa`).
- **O que faz `request.get_json`?** Lê o corpo JSON enviado pelo cliente.
- **Por que gunicorn?** Servidor de produção; o servidor do Flask (`app.run`) é só para desenvolvimento.
- **O que é um endpoint?** Combinação de URL + método HTTP.
- **O que é CRUD?** Create, Read, Update, Delete.
- **Por que `WHERE 1=1`?** Para poder acrescentar `AND ...` dinamicamente sem se preocupar se é o primeiro filtro.
- **Por que testes usam banco separado?** Para não apagar/sujar dados reais.
