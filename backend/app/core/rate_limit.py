"""
Rate limiter global compartido, basado en slowapi.

Key: IP del cliente. En producción vivimos detrás del proxy de Render, así
que preferimos X-Forwarded-For (leftmost) cuando existe. Localmente cae al
`request.client.host` real.

Notas de seguridad:
- X-Forwarded-For es spoof-eable si el backend está expuesto directo a
  internet. Detrás de Render el proxy lo setea al IP real; no hay riesgo.
- slowapi guarda el contador en memoria del proceso. En free tier de Render
  hay un solo worker → no necesitamos backend externo (Redis) para esta
  demo. Si algún día escalamos, cambiar a un Limiter con storage_uri Redis.
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Leftmost = cliente original (los proxies van appendeando el suyo).
        return xff.split(",")[0].strip()
    return get_remote_address(request)


# Limiter global — se importa desde main.py y desde cada router que lo use.
limiter = Limiter(key_func=_client_ip)
