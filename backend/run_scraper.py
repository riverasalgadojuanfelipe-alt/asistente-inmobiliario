#!/usr/bin/env python
"""
CLI para correr los scrapers de propiedades.

Uso:
    python run_scraper.py --ciudad cali --tipo venta --paginas 3
    python run_scraper.py --ciudad medellin --tipo arriendo --paginas 5
    python run_scraper.py --ciudad todas --tipo venta --paginas 2

Fuentes soportadas:
    --fuente fincaraiz  (default)
"""

from __future__ import annotations

import argparse
import logging
import sys

from app.core.database import SessionLocal
from app.models.property import Ciudad, TipoOperacion
from app.services.scraping import scrape_fincaraiz

CIUDADES_CLI = {c.value: c for c in Ciudad}
TIPOS_CLI = {t.value: t for t in TipoOperacion}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scraper de propiedades")
    parser.add_argument(
        "--ciudad",
        required=True,
        choices=[*CIUDADES_CLI.keys(), "todas"],
        help="Ciudad a scrapear (o 'todas')",
    )
    parser.add_argument(
        "--tipo",
        required=True,
        choices=[*TIPOS_CLI.keys(), "todas"],
        help="Tipo de operación (o 'todas')",
    )
    parser.add_argument(
        "--paginas",
        type=int,
        default=1,
        help="Número de páginas a recorrer (default: 1)",
    )
    parser.add_argument(
        "--fuente",
        default="fincaraiz",
        choices=["fincaraiz"],
        help="Fuente de datos (por ahora solo fincaraiz)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Log DEBUG",
    )
    return parser.parse_args()


def _resolver_ciudades(v: str) -> list[Ciudad]:
    return list(Ciudad) if v == "todas" else [CIUDADES_CLI[v]]


def _resolver_tipos(v: str) -> list[TipoOperacion]:
    return list(TipoOperacion) if v == "todas" else [TIPOS_CLI[v]]


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    ciudades = _resolver_ciudades(args.ciudad)
    tipos = _resolver_tipos(args.tipo)

    total_ins = 0
    total_dup = 0
    with SessionLocal() as db:
        for ciudad in ciudades:
            for tipo in tipos:
                print(f"\n>>> Scraping {args.fuente} | {ciudad.value} | {tipo.value} | {args.paginas} páginas")
                stats = scrape_fincaraiz(db, ciudad, tipo, paginas=args.paginas)
                print(
                    f"    ok={stats.paginas_ok} fail={stats.paginas_fallidas} "
                    f"vistos={stats.items_vistos} insertados={stats.items_insertados} "
                    f"duplicados={stats.items_duplicados}"
                )
                total_ins += stats.items_insertados
                total_dup += stats.items_duplicados

    print(f"\n=== TOTAL insertados={total_ins} duplicados/ignorados={total_dup} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
