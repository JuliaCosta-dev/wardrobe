# importa o cliente de testes do FASTAPI e a aplicação que queremos testas
from fastapi.testclient import TestClient

from app.main import app

# cria o cliente que consegue enviar requisições para nossa aplicação
client = TestClient(app)


def test_root_endpoint():
    # simula uma requisição para a rota
    response = client.get("/")
    # verificamos se a api respondeu com sucesso.
    assert response.status_code == 200
    # verificamos se o conteudo retornado é exatamente o esperado
    assert response.json() == {
        "message": " Hello, World! Wardrobe AI API está funcionando!",
        "status": "online",
    }


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
