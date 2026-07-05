"""
report.py

Ejecuta graph_analysis.py y structure_check.py sobre un vault OKF
y agrega ambos resultados en un único informe con timestamp.

Uso:
    python report.py --repo . --vault okf/ --out reports/report.json
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pretty_report

HERE = Path(__file__).parent


def run(script: str, args: list[str]) -> dict:
    result = subprocess.run(
        [sys.executable, str(HERE / script), *args],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip()}
    return json.loads(result.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    graph = run("graph_analysis.py", ["--vault", args.vault])
    structure = run("structure_check.py", ["--repo", args.repo, "--vault", args.vault])

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo": args.repo,
        "grafo": graph,
        "estructura": structure,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Informe combinado escrito en {out_path}")

    md_path = out_path.with_suffix(".md")
    md_path.write_text(pretty_report.render(report), encoding="utf-8")
    print(f"Informe legible escrito en {md_path}")


if __name__ == "__main__":
    main()
