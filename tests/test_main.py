"""
Testes do servidor FastAPI (main.py).
Roda sem banco de dados — DATABASE_URL não definida usa data.json local.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ── GET / ─────────────────────────────────────────────────────────────────────

class TestGetIndex:
    def test_retorna_200(self):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_retorna_html(self):
        resp = client.get("/")
        assert "text/html" in resp.headers["content-type"]
        assert "TurmasUnB" in resp.text


# ── GET /json ─────────────────────────────────────────────────────────────────

class TestGetJson:
    def test_retorna_200(self):
        resp = client.get("/json")
        assert resp.status_code == 200

    def test_retorna_lista_nao_vazia(self):
        data = client.get("/json").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_estrutura_dos_itens(self):
        item = client.get("/json").json()[0]
        for campo in ("materia", "turma", "professor", "horario", "link"):
            assert campo in item, f"Campo ausente: {campo}"

    def test_ordenado_por_materia_e_turma(self):
        data = client.get("/json").json()
        chaves = [(t["materia"], t["turma"]) for t in data]
        assert chaves == sorted(chaves)


# ── POST / ────────────────────────────────────────────────────────────────────

class TestPostLink:
    def test_link_https_valido(self):
        resp = client.post("/", data={
            "materia": "QUALQUER", "turma": "01",
            "link": "https://meet.google.com/abc-defg-hij",
        })
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_link_http_valido(self):
        resp = client.post("/", data={
            "materia": "QUALQUER", "turma": "01",
            "link": "http://example.com",
        })
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_link_vazio_limpa(self):
        # Link vazio é permitido para remover o link de uma turma
        resp = client.post("/", data={
            "materia": "QUALQUER", "turma": "01",
            "link": "",
        })
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_rejeita_javascript(self):
        resp = client.post("/", data={
            "materia": "QUALQUER", "turma": "01",
            "link": "javascript:alert(1)",
        })
        assert resp.status_code == 400
        assert resp.json()["ok"] is False

    def test_rejeita_ftp(self):
        resp = client.post("/", data={
            "materia": "QUALQUER", "turma": "01",
            "link": "ftp://arquivos.example.com",
        })
        assert resp.status_code == 400
        assert resp.json()["ok"] is False

    def test_rejeita_link_sem_protocolo(self):
        resp = client.post("/", data={
            "materia": "QUALQUER", "turma": "01",
            "link": "meet.google.com/abc",
        })
        assert resp.status_code == 400
        assert resp.json()["ok"] is False

    def test_rejeita_link_muito_longo(self):
        resp = client.post("/", data={
            "materia": "QUALQUER", "turma": "01",
            "link": "https://" + "a" * 2100,
        })
        assert resp.status_code == 400
        assert resp.json()["ok"] is False

    def test_turma_inexistente_retorna_ok(self):
        # Falha silenciosa por design — não expõe que a turma não existe
        resp = client.post("/", data={
            "materia": "MATERIA QUE NAO EXISTE XYZ999", "turma": "99",
            "link": "https://example.com",
        })
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_link_salvo_aparece_no_json(self):
        # Pega uma turma real do /json e salva um link nela
        turmas = client.get("/json").json()
        turma = turmas[0]

        client.post("/", data={
            "materia": turma["materia"],
            "turma": turma["turma"],
            "link": "https://example.com/teste",
        })

        # Confirma que o link aparece em memória
        turmas_atualizadas = client.get("/json").json()
        correspondente = next(
            t for t in turmas_atualizadas
            if t["materia"] == turma["materia"] and t["turma"] == turma["turma"]
        )
        assert correspondente["link"] == "https://example.com/teste"
