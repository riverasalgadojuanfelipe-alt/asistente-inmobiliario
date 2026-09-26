"""
Parser de consultas en lenguaje natural con reglas simples.

Objetivo: extraer filtros ESTRUCTURADOS (ciudad, tipo_operacion, rangos de
precio, mínimos de habitaciones/área) sin llamar a un LLM. Estos filtros
alimentan la consulta a la BD; luego una única llamada a Gemini interpreta
matices de estilo de vida sobre los candidatos.

Filosofía:
- Conservador. Ante la duda, se deja `None` (más candidatos > filtrar de más).
- Solo extraemos números anclados a palabras clave claras ("máximo", "hasta",
  "mínimo", "desde", "N habitaciones", "N m2").
- Soporta español colombiano común: "800 millones", "2 mil millones", "1.5M",
  "3M al mes", "60 m2".
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.property import Ciudad, TipoOperacion


@dataclass(slots=True)
class ParsedFilters:
    ciudad: Ciudad | None = None
    tipo_operacion: TipoOperacion | None = None
    precio_min: float | None = None
    precio_max: float | None = None
    habitaciones_min: int | None = None
    area_min: float | None = None


# ---------------------------------------------------------------------------
# Ciudad
# ---------------------------------------------------------------------------
_CITY_PATTERNS: list[tuple[Ciudad, re.Pattern[str]]] = [
    (Ciudad.MEDELLIN, re.compile(r"\bmedell[ií]n\b", re.IGNORECASE)),
    (Ciudad.BOGOTA, re.compile(r"\bbogot[aá](?:\s+d\.?\s*c\.?)?\b", re.IGNORECASE)),
    (Ciudad.TULUA, re.compile(r"\btulu[aá]\b", re.IGNORECASE)),
    (Ciudad.CALI, re.compile(r"\bcali\b", re.IGNORECASE)),
]


def _extract_ciudad(q: str) -> Ciudad | None:
    for c, pat in _CITY_PATTERNS:
        if pat.search(q):
            return c
    return None


# ---------------------------------------------------------------------------
# Tipo de operación
# ---------------------------------------------------------------------------
_ARRIENDO_RE = re.compile(
    r"\b(arriendo|arrend|arrendar|alquil|alquilar|rentar?|renta\b)",
    re.IGNORECASE,
)
_VENTA_RE = re.compile(
    r"\b(compr[ao]|comprar|venta|vender|adquir[íi]r|adquirir)\b",
    re.IGNORECASE,
)


def _extract_tipo_operacion(q: str) -> TipoOperacion | None:
    if _ARRIENDO_RE.search(q):
        return TipoOperacion.ARRIENDO
    if _VENTA_RE.search(q):
        return TipoOperacion.VENTA
    return None


# ---------------------------------------------------------------------------
# Precios
# ---------------------------------------------------------------------------
# Un número, permite . o , como separador de miles o decimal.
_NUM = r"\d+(?:[.,]\d+)*"


def _to_float(s: str) -> float:
    """
    Convierte '1.500.000' o '1,500,000' a 1500000; '1.5' a 1.5.
    Regla: si el ÚLTIMO separador va seguido de exactamente 3 dígitos, es
    un separador de miles (europeo/colombiano); si no, es decimal.
    """
    if not s:
        return 0.0
    # normaliza: si tiene ambos, asume '.' miles y ',' decimal (formato es-CO)
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    seps = re.findall(r"[.,]", s)
    if not seps:
        return float(s)
    last_sep = seps[-1]
    tail = s.rsplit(last_sep, 1)[1]
    if len(tail) == 3 and s.count(last_sep) >= 1:
        # miles
        return float(s.replace(last_sep, ""))
    # decimal
    return float(s.replace(",", "."))


def _price_value(num_s: str, unit: str | None) -> float | None:
    """Devuelve el valor en COP dado (número, sufijo)."""
    n = _to_float(num_s)
    if n <= 0:
        return None
    u = (unit or "").lower().strip()
    if u in ("mil millones", "mil-millones"):
        return n * 1_000_000_000
    if u in ("millones", "millón", "millon"):
        return n * 1_000_000
    if u == "m":  # "800M" en Colombia = 800 millones
        return n * 1_000_000
    if u == "mil":
        return n * 1_000
    if u == "k":
        return n * 1_000
    # Sin unidad: solo aceptamos si el número ya es "razonablemente grande"
    # (>= 100_000). Descarta cosas como "3 habitaciones".
    if n >= 100_000:
        return n
    return None


# número + unidad opcional. Grupos: 1=num, 2=unit
_PRICE_TOKEN = re.compile(
    rf"({_NUM})\s*(mil\s+millones|millones|millón|millon|mil|m\b|k\b)?",
    re.IGNORECASE,
)

_MAX_ANCHOR = re.compile(
    r"\b(?:m[aá]ximo|hasta|tope|presupuesto\s+(?:de|hasta)|no\s+m[aá]s\s+de)\b",
    re.IGNORECASE,
)
_MIN_ANCHOR = re.compile(
    r"\b(?:m[ií]nimo|desde|al\s+menos|a\s+partir\s+de|no\s+menos\s+de)\b",
    re.IGNORECASE,
)


def _first_price_after(anchor_end: int, text: str) -> float | None:
    """Busca el primer precio en los ~60 chars después del anchor."""
    tail = text[anchor_end : anchor_end + 60]
    for m in _PRICE_TOKEN.finditer(tail):
        p = _price_value(m.group(1), m.group(2))
        if p is not None:
            return p
    return None


def _extract_prices(q: str) -> tuple[float | None, float | None]:
    precio_max: float | None = None
    precio_min: float | None = None

    m = _MAX_ANCHOR.search(q)
    if m:
        precio_max = _first_price_after(m.end(), q)
    m = _MIN_ANCHOR.search(q)
    if m:
        precio_min = _first_price_after(m.end(), q)

    # Fallback: si no hay anchor, pero mencionan un valor claramente monetario
    # ("800 millones", "3M"), lo interpretamos como TOPE (usuario dice presupuesto).
    if precio_max is None:
        for m in _PRICE_TOKEN.finditer(q):
            unit = (m.group(2) or "").lower().strip()
            # solo si hay unidad monetaria explícita
            if unit in ("millones", "millón", "millon", "m", "mil millones"):
                p = _price_value(m.group(1), m.group(2))
                if p and p >= 500_000:  # umbral defensivo
                    precio_max = p
                    break

    return precio_min, precio_max


# ---------------------------------------------------------------------------
# Habitaciones y área
# ---------------------------------------------------------------------------
_HAB_RE = re.compile(
    r"\b(\d+)\s+(?:habitaci\w*|alcob\w*|cuart\w*|rec[aá]mar\w*|dormitor\w*)",
    re.IGNORECASE,
)
_AREA_RE = re.compile(
    rf"\b({_NUM})\s*(?:m2|m²|metros?(?:\s+cuadrados)?)\b",
    re.IGNORECASE,
)


def _extract_habitaciones_min(q: str) -> int | None:
    matches = list(_HAB_RE.finditer(q))
    if not matches:
        return None
    # Tomamos la primera aparición; el usuario suele decir "2 habitaciones"
    # y esperar "al menos 2", así que lo tratamos como mínimo por defecto.
    return int(matches[0].group(1))


def _extract_area_min(q: str) -> float | None:
    m = _AREA_RE.search(q)
    if not m:
        return None
    n = _to_float(m.group(1))
    return n if n > 0 else None


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------
def parse_query(query: str) -> ParsedFilters:
    """Convierte texto libre en filtros estructurados sin usar LLM."""
    q = query.strip()
    precio_min, precio_max = _extract_prices(q)
    return ParsedFilters(
        ciudad=_extract_ciudad(q),
        tipo_operacion=_extract_tipo_operacion(q),
        precio_min=precio_min,
        precio_max=precio_max,
        habitaciones_min=_extract_habitaciones_min(q),
        area_min=_extract_area_min(q),
    )
