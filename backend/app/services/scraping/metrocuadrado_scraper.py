"""
Scraper de Metrocuadrado para Cali, Medellín, Bogotá y Tuluá (venta/arriendo).

=============================================================================
NOTAS DE MANTENIMIENTO — LEER ANTES DE MODIFICAR
=============================================================================

A diferencia de Fincaraíz, Metrocuadrado **NO** entrega los datos en un
`<script id="__NEXT_DATA__">`. El sitio es un shell client-side (React SPA)
que muestra skeletons y luego pide los datos a una API REST autenticada.

Descubrimos el endpoint inspeccionando los chunks JS y el RSC inicial:

    GET https://www.metrocuadrado.com/rest-search/search
    Header requerido: X-Api-Key: <clave pública embebida en el RSC>

Parámetros:
    - size=50        (OBLIGATORIO exactamente 50; otros valores devuelven
                      totalHits=0. Anti-scraping simple.)
    - from=0,50,...  (paginación)
    - realEstateTypeList=apartamento,casa
    - realEstateBusinessList=venta|arriendo
    - city=Cali|Medellín|Bogotá D.C.|Tuluá   (con acentos, URL-encoded)

La respuesta trae ~65 items por página (los 50 pedidos + hasta ~15
"highlights" promocionados). Dedup por `midinmueble` dentro de la página y
por `url_original` en base (mismo mecanismo que Fincaraíz).

Mapeo de campos (Metrocuadrado → nuestro modelo Property):
    ciudad          <- mciudad.nombre           (normalizado a enum)
    tipo_operacion  <- mtiponegocio             ("Venta"/"Arriendo" -> lower)
    precio          <- mvalorventa | mvalorarriendo (según operación)
    habitaciones    <- mnrocuartos              (string, cast a int)
    banos           <- mnrobanos                (string, cast a int)
    area_m2         <- areaPrivada | marea      (float)
    barrio          <- mbarrio
    descripcion     <- comment
    property_type   <- mtipoinmueble.nombre     (lower)
    url_original    <- BASE_URL + link
    image_url       <- imageLink                (host multimedia.metrocuadrado.com)
    fuente          <- "metrocuadrado"

Si la API rota la key: descargar https://www.metrocuadrado.com/apartamentos-casas-en-venta/cali
con header `RSC: 1` y buscar `"apiKey"` en la respuesta.

Política de scraping (misma que Fincaraíz):
    - Delay aleatorio 2-5s entre peticiones.
    - Reintento simple ante 5xx / timeouts (2 intentos).
    - Un fallo de página NO aborta el scrape; se registra y se sigue.
=============================================================================
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Iterable
from decimal import Decimal

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.property import Ciudad, Property, TipoOperacion
from app.services.scraping.fincaraiz_scraper import (
    DEFAULT_ALLOWED_PROPERTY_TYPES,
    ScrapeStats,
    _parse_coords,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://www.metrocuadrado.com"
API_URL = f"{BASE_URL}/rest-search/search"
API_KEY = "P1MfFHfQMOtL16Zpg36NcntJYCLFm8FqFfudnavl"
PAGE_SIZE = 50  # OBLIGATORIO — otros valores devuelven totalHits=0

CITY_PARAM: dict[Ciudad, str] = {
    Ciudad.CALI: "Cali",
    Ciudad.MEDELLIN: "Medellín",
    Ciudad.BOGOTA: "Bogotá D.C.",
    Ciudad.TULUA: "Tuluá",
}

BUSINESS_PARAM: dict[TipoOperacion, str] = {
    TipoOperacion.VENTA: "venta",
    TipoOperacion.ARRIENDO: "arriendo",
}

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/",
    "X-Api-Key": API_KEY,
}

DELAY_MIN_S = 2.0
DELAY_MAX_S = 5.0
REQUEST_TIMEOUT_S = 30.0


def _fetch_page(
    client: httpx.Client,
    ciudad: Ciudad,
    tipo: TipoOperacion,
    offset: int,
    *,
    retries: int = 2,
) -> dict | None:
    params = {
        "realEstateTypeList": "apartamento,casa",
        "realEstateBusinessList": BUSINESS_PARAM[tipo],
        "city": CITY_PARAM[ciudad],
        "from": offset,
        "size": PAGE_SIZE,
    }
    for intento in range(retries + 1):
        try:
            resp = client.get(API_URL, params=params, timeout=REQUEST_TIMEOUT_S)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(
                "GET %s offset=%s -> HTTP %s (intento %s)",
                API_URL, offset, resp.status_code, intento + 1,
            )
            if resp.status_code < 500:
                return None
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning(
                "GET %s offset=%s falló: %s (intento %s)",
                API_URL, offset, exc, intento + 1,
            )
        if intento < retries:
            time.sleep(1.5 * (intento + 1))
    return None


def _first_number(item: dict, keys: Iterable[str]) -> float | int | None:
    for k in keys:
        v = item.get(k)
        if v not in (None, 0, "", "0"):
            return v
    return None


def _to_property_row(
    item: dict, ciudad: Ciudad, tipo: TipoOperacion
) -> dict | None:
    try:
        link = item.get("link") or ""
        if not link:
            return None
        url_original = f"{BASE_URL}{link}" if link.startswith("/") else link

        price = item.get("mvalorventa") if tipo == TipoOperacion.VENTA else item.get("mvalorarriendo")
        if price in (None, 0):
            return None

        cuartos = item.get("mnrocuartos")
        banos = item.get("mnrobanos")
        if cuartos in (None, "") or banos in (None, ""):
            return None

        area = _first_number(item, ("areaPrivada", "areaprivada", "marea", "mareac"))
        if area in (None, 0):
            return None

        barrio = item.get("mbarrio") or None
        if barrio:
            barrio = barrio.strip().title() or None

        descripcion = item.get("comment") or item.get("title") or None
        if descripcion:
            descripcion = descripcion.strip()[:2000]

        prop_type_raw = ((item.get("mtipoinmueble") or {}).get("nombre") or "").strip()
        property_type = prop_type_raw.lower() or None

        image_url = item.get("imageLink") or None

        # Coordenadas: `localizacion` viene como floats. El sentinel (0, 0)
        # se filtra en _parse_coords (compartido con fincaraiz).
        loc = item.get("localizacion") or {}
        latitud, longitud = _parse_coords(loc.get("lat"), loc.get("lon"))

        return {
            "ciudad": ciudad,
            "tipo_operacion": tipo,
            "precio": Decimal(str(price)),
            "habitaciones": int(cuartos),
            "banos": int(banos),
            "area_m2": Decimal(str(area)),
            "barrio": barrio,
            "descripcion": descripcion,
            "fuente": "metrocuadrado",
            "property_type": property_type,
            "url_original": url_original,
            "image_url": image_url,
            "latitud": latitud,
            "longitud": longitud,
        }
    except (TypeError, ValueError):
        logger.exception("Item mal formado, se ignora: mid=%s", item.get("midinmueble"))
        return None


def _upsert_batch(db: Session, rows: Iterable[dict]) -> tuple[int, int]:
    """Idéntica lógica al scraper de Fincaraíz. Dedup por url_original."""
    from sqlalchemy import func as _func, select as _select

    rows = list(rows)
    if not rows:
        return 0, 0

    urls = [r["url_original"] for r in rows if r.get("url_original")]
    already = 0
    if urls:
        already = db.execute(
            _select(_func.count())
            .select_from(Property)
            .where(Property.url_original.in_(urls))
        ).scalar() or 0

    stmt = pg_insert(Property).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["url_original"],
        set_={
            "precio": stmt.excluded.precio,
            "area_m2": stmt.excluded.area_m2,
            "property_type": stmt.excluded.property_type,
            "descripcion": stmt.excluded.descripcion,
            "barrio": stmt.excluded.barrio,
            "image_url": stmt.excluded.image_url,
            "latitud": stmt.excluded.latitud,
            "longitud": stmt.excluded.longitud,
        },
    )
    db.execute(stmt)
    db.commit()

    inserted_new = len(rows) - already
    return inserted_new, already


def scrape_metrocuadrado(
    db: Session,
    ciudad: Ciudad,
    tipo: TipoOperacion,
    paginas: int = 1,
    *,
    delay_range_s: tuple[float, float] = (DELAY_MIN_S, DELAY_MAX_S),
    allowed_property_types: frozenset[str] | None = DEFAULT_ALLOWED_PROPERTY_TYPES,
) -> ScrapeStats:
    """
    Scrapea `paginas` páginas de Metrocuadrado para (ciudad, tipo_operacion).
    Cada "página" == 50 items pedidos vía API (from = (pagina-1) * 50).
    """
    stats = ScrapeStats()
    d_min, d_max = delay_range_s
    seen_ids: set[str] = set()  # dedup local por midinmueble (highlights repetidos)

    with httpx.Client(headers=DEFAULT_HEADERS, http2=True, follow_redirects=True) as client:
        total_hits: int | None = None
        for pagina in range(1, paginas + 1):
            offset = (pagina - 1) * PAGE_SIZE
            logger.info(
                "Metrocuadrado [%s %s] página %s (from=%s)",
                ciudad.value, tipo.value, pagina, offset,
            )
            payload = _fetch_page(client, ciudad, tipo, offset)
            if payload is None:
                stats.paginas_fallidas += 1
                time.sleep(random.uniform(d_min, d_max))
                continue

            if total_hits is None:
                total_hits = payload.get("totalHits")
                logger.info("totalHits=%s para %s/%s", total_hits, ciudad.value, tipo.value)

            items = payload.get("results") or []
            stats.items_vistos += len(items)

            rows: list[dict] = []
            for it in items:
                mid = it.get("midinmueble")
                if mid and mid in seen_ids:
                    continue
                if mid:
                    seen_ids.add(mid)

                row = _to_property_row(it, ciudad, tipo)
                if row is None:
                    continue
                if allowed_property_types is not None:
                    if (row.get("property_type") or "") not in allowed_property_types:
                        stats.items_filtrados += 1
                        continue
                rows.append(row)

            ins, dup = _upsert_batch(db, rows)
            stats.items_insertados += ins
            stats.items_duplicados += dup
            stats.paginas_ok += 1

            if total_hits is not None and offset + PAGE_SIZE >= total_hits:
                logger.info("Se alcanzó totalHits (%s).", total_hits)
                break

            if pagina < paginas:
                time.sleep(random.uniform(d_min, d_max))

    return stats
