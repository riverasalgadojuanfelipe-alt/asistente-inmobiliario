#!/usr/bin/env python
"""
CLI para correr los scrapers de propiedades.

Uso:
    python run_scraper.py --ciudad cali --tipo venta --paginas 3
    python run_scraper.py --ciudad medellin --tipo arriendo --paginas 5
    python run_scraper.py --ciudad todas --tipo venta --paginas 2

Filtro de tipos de propiedad (default: solo residencial apartamento+casa):
    python run_scraper.py ... --tipos-propiedad apartamento,casa,apartaestudio
    python run_scraper.py ... --tipos-propiedad todos    # sin filtrar

Fuentes soportadas:
    --fuente fincaraiz | metrocuadrado | todas   (default: fincaraiz)
"""

from __future__ import annotations

import argparse
import logging
import sys

from app.core.database import SessionLocal
from app.models.property import Ciudad, TipoOperacion
from app.services.scraping import scrape_fincaraiz, scrape_metrocuadrado
from app.services.scraping.fincaraiz_scraper import DEFAULT_ALLOWED_PROPERTY_TYPES

CIUDADES_CLI = {c.value: c for c in Ciudad}
TIPOS_CLI = {t.value: t for t in TipoOperacion}

SCRAPERS = {
    "fincaraiz": scrape_fincaraiz,
    "metrocuadrado": scrape_metrocuadrado,
}


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
        choices=[*SCRAPERS.keys(), "todas"],
        help="Fuente de datos (fincaraiz, metrocuadrado, o todas)",
    )
    parser.add_argument(
        "--tipos-propiedad",
        default=",".join(sorted(DEFAULT_ALLOWED_PROPERTY_TYPES)),
        help=(
            "Lista separada por comas de tipos permitidos (en minusculas). "
            "Usa 'todos' para no filtrar. "
            f"Default: {','.join(sorted(DEFAULT_ALLOWED_PROPERTY_TYPES))}"
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Log DEBUG",
    )
    return parser.parse_args()


def _parse_tipos_propiedad(raw: str) -> frozenset[str] | None:
    v = raw.strip().lower()
    if v in {"todos", "todas", "*", ""}:
        return None
    return frozenset(t.strip() for t in v.split(",") if t.strip())


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
    allowed = _parse_tipos_propiedad(args.tipos_propiedad)
    filtro_txt = "todos" if allowed is None else ",".join(sorted(allowed))
    fuentes = list(SCRAPERS.keys()) if args.fuente == "todas" else [args.fuente]

    total_ins = 0
    total_dup = 0
    total_filt = 0
    with SessionLocal() as db:
        for fuente in fuentes:
            scrape_fn = SCRAPERS[fuente]
            for ciudad in ciudades:
                for tipo in tipos:
                    print(
                        f"\n>>> Scraping {fuente} | {ciudad.value} | {tipo.value} "
                        f"| {args.paginas} páginas | tipos={filtro_txt}"
                    )
                    stats = scrape_fn(
                        db, ciudad, tipo,
                        paginas=args.paginas,
                        allowed_property_types=allowed,
                    )
                    print(
                        f"    ok={stats.paginas_ok} fail={stats.paginas_fallidas} "
                        f"vistos={stats.items_vistos} nuevos={stats.items_insertados} "
                        f"actualizados={stats.items_duplicados} filtrados={stats.items_filtrados}"
                    )
                    total_ins += stats.items_insertados
                    total_dup += stats.items_duplicados
                    total_filt += stats.items_filtrados

    print(
        f"\n=== TOTAL nuevos={total_ins} actualizados={total_dup} "
        f"filtrados_por_tipo={total_filt} ==="
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
