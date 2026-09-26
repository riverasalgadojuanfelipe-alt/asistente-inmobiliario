"""
Scraper de Fincaraíz para Cali, Medellín, Bogotá y Tuluá (venta/arriendo).

=============================================================================
NOTAS DE MANTENIMIENTO — LEER ANTES DE MODIFICAR
=============================================================================

Fincaraíz es una app Next.js con SSR. En cada página de resultados existe un
tag `<script id="__NEXT_DATA__" type="application/json">` que contiene TODA
la data del listado como JSON estructurado. Preferimos extraer de ahí en vez
de parsear el DOM de las tarjetas, porque:

  1. Los selectores CSS de las tarjetas cambian con cada release del sitio
     (clases hasheadas tipo "listingCard__uFa9" o similares).
  2. El JSON de Next expone MÁS campos (bedrooms, bathrooms, m2, price, etc.)
     que la HTML de la tarjeta.
  3. Es el mismo payload que consume el frontend, así que es "estable" en
     tanto no cambien las props del componente de página.

Ruta del payload dentro de __NEXT_DATA__ (verificado 2026-09-26):

    root
      └── props
          └── pageProps
              └── fetchResult
                  └── searchFast
                      ├── data[]          -> lista de propiedades (21 por página)
                      └── paginatorInfo   -> {currentPage, lastPage, total, ...}

Campos por item que usamos (searchFast.data[i]):
    - id              int      -> id externo de Fincaraíz (dedup)
    - link            str      -> ruta relativa; URL absoluta con BASE_URL
    - title           str      -> titulo del anuncio (usado en descripcion)
    - description     str      -> descripcion larga
    - price.amount    number   -> precio en COP
    - bedrooms / rooms int     -> habitaciones (bedrooms es el correcto en la mayoria de tipos)
    - bathrooms       int
    - m2              number   -> area en m2 (a veces null; fallback a m2Built)
    - m2Built         number
    - address         str      -> direccion completa; usada como fallback de barrio
    - locations.location_main.name   -> ciudad/localidad
    - property_type.name / operation_type.name

Selectores DOM (fallback, por si tumban el __NEXT_DATA__):
    - Actualmente NO tenemos fallback DOM implementado. Si el JSON deja de
      existir, hay que reimplementar con Playwright o encontrar el endpoint
      GraphQL/REST que consume el frontend (la clave apolloState en el
      __NEXT_DATA__ sugiere Apollo Client + GraphQL).

URLs de listado:
    https://www.fincaraiz.com.co/{venta|arriendo}/{slug_ciudad}[/paginaN]

Slugs verificados:
    cali      -> cali/valle-del-cauca
    medellin  -> medellin/antioquia
    bogota    -> bogota-dc
    tulua     -> tulua/valle-del-cauca

Política de scraping:
    - Delay aleatorio 2-5s entre peticiones.
    - Headers de navegador real (Chrome desktop).
    - HTTP/2 (httpx) porque algunos anti-bots huelen HTTP/1.1 solitario.
    - Reintento simple ante 5xx / timeouts (2 intentos).
    - Un fallo de página NO aborta el scrape; se registra y se sigue.
=============================================================================
"""

from __future__ import annotations

import json
import logging
import random
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.property import Ciudad, Property, TipoOperacion

logger = logging.getLogger(__name__)

BASE_URL = "https://www.fincaraiz.com.co"

CITY_SLUGS: dict[Ciudad, str] = {
    Ciudad.CALI: "cali/valle-del-cauca",
    Ciudad.MEDELLIN: "medellin/antioquia",
    Ciudad.BOGOTA: "bogota-dc",
    Ciudad.TULUA: "tulua/valle-del-cauca",
}

OPERATION_SLUGS: dict[TipoOperacion, str] = {
    TipoOperacion.VENTA: "venta",
    TipoOperacion.ARRIENDO: "arriendo",
}

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

DELAY_MIN_S = 2.0
DELAY_MAX_S = 5.0
REQUEST_TIMEOUT_S = 30.0


@dataclass(slots=True)
class ScrapeStats:
    paginas_ok: int = 0
    paginas_fallidas: int = 0
    items_vistos: int = 0
    items_insertados: int = 0
    items_duplicados: int = 0


def _build_url(ciudad: Ciudad, tipo: TipoOperacion, pagina: int) -> str:
    op = OPERATION_SLUGS[tipo]
    slug = CITY_SLUGS[ciudad]
    if pagina <= 1:
        return f"{BASE_URL}/{op}/{slug}"
    return f"{BASE_URL}/{op}/{slug}/pagina{pagina}"


def _sleep_polite() -> None:
    time.sleep(random.uniform(DELAY_MIN_S, DELAY_MAX_S))


def _extract_next_data(html: str) -> dict | None:
    """Extrae el JSON del <script id="__NEXT_DATA__">."""
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__")
    if tag is None or not tag.string:
        # Fallback por regex en caso de HTML mal formado
        match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S
        )
        if not match:
            return None
        raw = match.group(1)
    else:
        raw = tag.string
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.exception("No se pudo parsear __NEXT_DATA__")
        return None


def _items_from_next_data(payload: dict) -> tuple[list[dict], dict]:
    """Devuelve (items, paginator_info) desde el payload de Next."""
    try:
        search = payload["props"]["pageProps"]["fetchResult"]["searchFast"]
    except KeyError:
        return [], {}
    return search.get("data", []) or [], search.get("paginatorInfo", {}) or {}


def _fetch_page(client: httpx.Client, url: str, *, retries: int = 2) -> str | None:
    for intento in range(retries + 1):
        try:
            resp = client.get(url, timeout=REQUEST_TIMEOUT_S)
            if resp.status_code == 200:
                return resp.text
            logger.warning("GET %s -> HTTP %s (intento %s)", url, resp.status_code, intento + 1)
            if resp.status_code < 500:
                return None
        except httpx.HTTPError as exc:
            logger.warning("GET %s falló: %s (intento %s)", url, exc, intento + 1)
        if intento < retries:
            time.sleep(1.5 * (intento + 1))
    return None


def _to_property_row(
    item: dict, ciudad: Ciudad, tipo: TipoOperacion
) -> dict | None:
    """Mapea un item del JSON de Fincaraíz al esquema de la tabla propiedades."""
    try:
        item_id = item.get("id")
        link = item.get("link") or ""
        if not item_id or not link:
            return None

        url_original = f"{BASE_URL}{link}" if link.startswith("/") else link

        price = (item.get("price") or {}).get("amount")
        if price in (None, 0):
            return None

        bedrooms = item.get("bedrooms") or item.get("rooms") or 0
        bathrooms = item.get("bathrooms") or 0
        area = item.get("m2") or item.get("m2Built") or item.get("m2apto")
        if area in (None, 0):
            return None

        barrio: str | None = None
        locations = item.get("locations") or {}
        if isinstance(locations, dict):
            main_loc = locations.get("location_main") or {}
            barrio = main_loc.get("name")
        if not barrio:
            address = item.get("address") or ""
            barrio = address.split(",")[0].strip() or None

        descripcion = item.get("description") or item.get("title") or None
        if descripcion:
            descripcion = descripcion.strip()[:2000]

        return {
            "ciudad": ciudad,
            "tipo_operacion": tipo,
            "precio": Decimal(str(price)),
            "habitaciones": int(bedrooms),
            "banos": int(bathrooms),
            "area_m2": Decimal(str(area)),
            "barrio": barrio,
            "descripcion": descripcion,
            "fuente": "fincaraiz",
            "url_original": url_original,
        }
    except (TypeError, ValueError):
        logger.exception("Item mal formado, se ignora: id=%s", item.get("id"))
        return None


def _upsert_batch(db: Session, rows: Iterable[dict]) -> tuple[int, int]:
    """
    Inserta el batch con ON CONFLICT DO NOTHING sobre url_original.
    Devuelve (insertados, duplicados_o_ignorados).
    """
    rows = list(rows)
    if not rows:
        return 0, 0
    stmt = pg_insert(Property).values(rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=["url_original"])
    result = db.execute(stmt)
    db.commit()
    inserted = result.rowcount or 0
    return inserted, len(rows) - inserted


def scrape_fincaraiz(
    db: Session,
    ciudad: Ciudad,
    tipo: TipoOperacion,
    paginas: int = 1,
    *,
    delay_range_s: tuple[float, float] = (DELAY_MIN_S, DELAY_MAX_S),
) -> ScrapeStats:
    """
    Scrapea `paginas` páginas de resultados de Fincaraíz para la combinación
    (ciudad, tipo_operacion) y guarda cada propiedad en la BD deduplicando por
    `url_original`.
    """
    stats = ScrapeStats()
    d_min, d_max = delay_range_s

    with httpx.Client(
        headers=DEFAULT_HEADERS,
        http2=True,
        follow_redirects=True,
    ) as client:
        for pagina in range(1, paginas + 1):
            url = _build_url(ciudad, tipo, pagina)
            logger.info("Fincaraíz [%s %s] página %s → %s", ciudad.value, tipo.value, pagina, url)
            html = _fetch_page(client, url)
            if html is None:
                stats.paginas_fallidas += 1
                time.sleep(random.uniform(d_min, d_max))
                continue

            payload = _extract_next_data(html)
            if payload is None:
                logger.error("Sin __NEXT_DATA__ en %s — ¿cambió la estructura?", url)
                stats.paginas_fallidas += 1
                time.sleep(random.uniform(d_min, d_max))
                continue

            items, paginator = _items_from_next_data(payload)
            stats.items_vistos += len(items)
            rows = [r for r in (_to_property_row(it, ciudad, tipo) for it in items) if r]
            ins, dup = _upsert_batch(db, rows)
            stats.items_insertados += ins
            stats.items_duplicados += dup
            stats.paginas_ok += 1

            last_page = paginator.get("lastPage") if isinstance(paginator, dict) else None
            if last_page and pagina >= last_page:
                logger.info("Se alcanzó la última página real (%s).", last_page)
                break

            if pagina < paginas:
                time.sleep(random.uniform(d_min, d_max))

    return stats
