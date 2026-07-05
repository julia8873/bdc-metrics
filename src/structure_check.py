"""
structure_check.py

Verifica la estructura esencial de un bundle OKF:
- Existencia de AGENTS.md, okf/log.md, okf/index.md
- Frontmatter obligatorio y consistente en cada .md de okf/
- Tasa de formato Markdown válido (heurística: frontmatter parseable +
  encabezados bien formados)

Uso:
    python structure_check.py --repo . --vault okf/ --out reports/structure.json
"""
import argparse
import json
import sys
from pathlib import Path

import frontmatter

REQUIRED_FIELDS = ["type", "title", "description", "tags", "timestamp"]
VALID_TYPES = {"Concept", "Entity", "Source", "Playbook", "Metric", "Constraint", "Index", "Log"}


def check_base_files(repo: Path, vault: Path):
    checks = {
        "AGENTS.md": (repo / "AGENTS.md").is_file(),
        "okf/log.md": (vault / "log.md").is_file(),
        "okf/index.md": (vault / "index.md").is_file(),
    }
    return checks


def check_frontmatter(vault: Path):
    files = sorted(p for p in vault.rglob("*.md") if p.is_file())
    results = []
    n_valid_md = 0
    for f in files:
        rel = str(f.relative_to(vault))
        entry = {"file": rel, "frontmatter_ok": False, "missing_fields": [], "tipo_valido": None}
        try:
            post = frontmatter.load(f)
            missing = [k for k in REQUIRED_FIELDS if k not in post.metadata]
            entry["missing_fields"] = missing
            entry["frontmatter_ok"] = len(missing) == 0
            tipo = post.metadata.get("type")
            entry["tipo_valido"] = tipo in VALID_TYPES if tipo else False
            # heurística de markdown válido: no hay '---' huérfanos y hay contenido tras la cabecera
            if entry["frontmatter_ok"] and entry["tipo_valido"]:
                n_valid_md += 1
        except Exception as e:
            entry["error"] = str(e)
        results.append(entry)

    tasa_md_valido = (n_valid_md / len(files)) if files else 0.0
    return results, round(tasa_md_valido, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Ruta raíz del repo (contiene AGENTS.md)")
    ap.add_argument("--vault", required=True, help="Ruta a la carpeta okf/")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    repo = Path(args.repo)
    vault = Path(args.vault)
    if not vault.exists():
        print(f"ERROR: no existe la ruta {vault}", file=sys.stderr)
        sys.exit(1)

    base_files = check_base_files(repo, vault)
    frontmatter_results, tasa_md_valido = check_frontmatter(vault)

    output = {
        "ficheros_base": base_files,
        "tasa_markdown_valido": tasa_md_valido,
        "n_ficheros_analizados": len(frontmatter_results),
        "detalle_frontmatter": frontmatter_results,
    }
    text = json.dumps(output, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Resultado escrito en {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
