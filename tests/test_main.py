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

    def test_semestre_no_html(self):
        # O semestre deve aparecer no título e na navbar
        import os
        semester = os.getenv("SEMESTER", "2026.1")
        resp = client.get("/")
        assert semester in resp.text


# ── GET /status ────────────────────────────────────────────────────────────────

class TestGetStatus:
    def test_retorna_200(self):
        assert client.get("/status").status_code == 200

    def test_retorna_html(self):
        resp = client.get("/status")
        assert "text/html" in resp.headers["content-type"]

    def test_contem_cards(self):
        resp = client.get("/status")
        assert "Links cadastrados" in resp.text


class TestGetSobre:
    def test_retorna_200(self):
        assert client.get("/sobre").status_code == 200

    def test_retorna_html(self):
        resp = client.get("/sobre")
        assert "text/html" in resp.headers["content-type"]

    def test_contem_conteudo(self):
        resp = client.get("/sobre")
        assert "gruposfga" in resp.text
        assert "Mateus Lira" in resp.text


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
        for campo in ("materia", "turma", "professor", "horario", "unidade", "link"):
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

    def test_rejeita_link_vazio(self):
        # Link vazio nunca é permitido
        resp = client.post("/", data={
            "materia": "QUALQUER", "turma": "01",
            "link": "",
        })
        assert resp.status_code == 400
        assert resp.json()["ok"] is False

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


# ── Backup ────────────────────────────────────────────────────────────────────

import main as _main  # noqa: E402


class TestBackup:
    """Testes dos endpoints /backup/links.json e /backup/restore.
    Rodamos sem DATABASE_URL (conftest.py garante isso), então operações
    que dependem do banco retornam 503 mesmo com token correto."""

    def _set_token(self, valor):
        """Auxiliar: altera BACKUP_TOKEN no módulo e retorna o valor original."""
        original = _main.BACKUP_TOKEN
        _main.BACKUP_TOKEN = valor
        return original

    # --- Sem BACKUP_TOKEN configurado ---

    def test_export_sem_backup_token_retorna_503(self):
        original = self._set_token(None)
        try:
            resp = client.get("/backup/links.json",
                              headers={"Authorization": "Bearer qualquer"})
            assert resp.status_code == 503
        finally:
            _main.BACKUP_TOKEN = original

    def test_restore_sem_backup_token_retorna_503(self):
        original = self._set_token(None)
        try:
            resp = client.post("/backup/restore",
                               json=[],
                               headers={"Authorization": "Bearer qualquer"})
            assert resp.status_code == 503
        finally:
            _main.BACKUP_TOKEN = original

    # --- Com BACKUP_TOKEN configurado, autenticação errada ---

    def test_export_sem_header_retorna_401(self):
        original = self._set_token("token-secreto")
        try:
            resp = client.get("/backup/links.json")
            assert resp.status_code == 401
        finally:
            _main.BACKUP_TOKEN = original

    def test_export_token_errado_retorna_401(self):
        original = self._set_token("token-secreto")
        try:
            resp = client.get("/backup/links.json",
                              headers={"Authorization": "Bearer errado"})
            assert resp.status_code == 401
        finally:
            _main.BACKUP_TOKEN = original

    def test_restore_token_errado_retorna_401(self):
        original = self._set_token("token-secreto")
        try:
            resp = client.post("/backup/restore",
                               json=[],
                               headers={"Authorization": "Bearer errado"})
            assert resp.status_code == 401
        finally:
            _main.BACKUP_TOKEN = original

    # --- Com token correto, sem banco (DATABASE_URL ausente nos testes) ---

    def test_export_token_correto_sem_db_retorna_503(self):
        original = self._set_token("token-secreto")
        try:
            resp = client.get("/backup/links.json",
                              headers={"Authorization": "Bearer token-secreto"})
            assert resp.status_code == 503
        finally:
            _main.BACKUP_TOKEN = original

    # --- Restore: validação de payload ---

    def test_restore_json_invalido_retorna_400(self):
        original = self._set_token("token-secreto")
        try:
            resp = client.post("/backup/restore",
                               content=b"isso nao eh json",
                               headers={
                                   "Authorization": "Bearer token-secreto",
                                   "Content-Type": "application/json",
                               })
            assert resp.status_code == 400
        finally:
            _main.BACKUP_TOKEN = original

    def test_restore_objeto_em_vez_de_lista_retorna_400(self):
        original = self._set_token("token-secreto")
        try:
            resp = client.post("/backup/restore",
                               json={"materia": "X", "turma": "1", "link": "https://x.com"},
                               headers={"Authorization": "Bearer token-secreto"})
            assert resp.status_code == 400
        finally:
            _main.BACKUP_TOKEN = original

    def test_restore_entrada_sem_campos_obrigatorios_retorna_400(self):
        original = self._set_token("token-secreto")
        try:
            resp = client.post("/backup/restore",
                               json=[{"materia": "X"}],  # faltam turma e link
                               headers={"Authorization": "Bearer token-secreto"})
            assert resp.status_code == 400
        finally:
            _main.BACKUP_TOKEN = original
