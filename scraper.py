"""
Scraper do SIGAA/UnB para coleta de turmas abertas.
Uso: python scraper.py [--periodo 2026.1] [--output data.json]
"""

import argparse
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

SIGAA_URL = "https://sigaa.unb.br/sigaa/public/turmas/listar.jsf"


async def get_unidades(page) -> list[tuple[str, str]]:
    options = await page.query_selector_all("select#formTurma\\:inputDepto option")
    unidades = []
    for opt in options:
        value = await opt.get_attribute("value")
        label = await opt.inner_text()
        if value and value.strip() and value.strip() != "0":
            unidades.append((value.strip(), label.strip()))
    return unidades


async def parse_turmas(page) -> list[dict]:
    turmas = []
    rows = await page.query_selector_all("#turmasAbertas tbody tr")
    materia_atual = ""
    for row in rows:
        classes = await row.get_attribute("class") or ""
        if "agrupador" in classes:
            materia_atual = (await row.inner_text()).strip()
        else:
            cells = await row.query_selector_all("td")
            if len(cells) >= 4:
                turma = (await cells[0].inner_text()).strip()
                professor = (await cells[2].inner_text()).strip()
                horario = (await cells[3].inner_text()).strip()
                if turma and materia_atual:
                    turmas.append({
                        "materia": materia_atual,
                        "turma": turma,
                        "professor": professor,
                        "horario": horario,
                        "link": "",
                    })
    return turmas


async def scrape_unidade(page, unidade_value: str, ano: str, periodo: str) -> list[dict]:
    await page.goto(SIGAA_URL, wait_until="networkidle")

    await page.select_option("select#formTurma\\:inputNivel", value="G")
    await page.select_option("select#formTurma\\:inputDepto", value=unidade_value)
    await page.fill("input#formTurma\\:inputAno", ano)
    await page.select_option("select#formTurma\\:inputPeriodo", value=periodo)

    await page.click("input[value='Buscar']")
    await page.wait_for_load_state("networkidle")

    return await parse_turmas(page)


async def main(periodo_label: str, output: str):
    try:
        ano, periodo = periodo_label.split(".")
    except ValueError:
        print(f"Formato inválido: '{periodo_label}'. Use ex: 2026.1")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Carregando SIGAA...")
        await page.goto(SIGAA_URL, wait_until="networkidle")

        unidades = await get_unidades(page)
        print(f"{len(unidades)} departamentos encontrados.")
        print(f"Buscando turmas de {ano}.{periodo}...\n")

        all_turmas: list[dict] = []
        seen: set[tuple] = set()

        for i, (value, label) in enumerate(unidades, 1):
            print(f"[{i}/{len(unidades)}] {label}...", end=" ", flush=True)
            try:
                turmas = await scrape_unidade(page, value, ano, periodo)
                novas = 0
                for t in turmas:
                    key = (t["materia"], t["turma"])
                    if key not in seen:
                        seen.add(key)
                        all_turmas.append(t)
                        novas += 1
                print(f"{novas} turmas")
            except Exception as e:
                print(f"erro: {e}")

        await browser.close()

    all_turmas.sort(key=lambda x: (x["materia"], x["turma"]))

    # preserva links já existentes
    output_path = Path(output)
    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text())
            link_map = {(t["materia"], t["turma"]): t["link"] for t in existing if t.get("link")}
            for t in all_turmas:
                if (t["materia"], t["turma"]) in link_map:
                    t["link"] = link_map[(t["materia"], t["turma"])]
            if link_map:
                print(f"\nLinks existentes preservados: {len(link_map)}")
        except Exception:
            pass

    output_path.write_text(json.dumps(all_turmas, ensure_ascii=False, indent=2))
    print(f"\n✅ {len(all_turmas)} turmas salvas em {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper de turmas SIGAA/UnB")
    parser.add_argument("--periodo", default="2026.1", help="Período letivo (ex: 2026.1)")
    parser.add_argument("--output", default="data.json", help="Arquivo de saída")
    args = parser.parse_args()

    asyncio.run(main(args.periodo, args.output))
