import base64
import json
import os
import re
from pathlib import Path

from anthropic import Anthropic

MODEL = "claude-opus-4-7"

PROMPT = """Eres un sistema de extraccion de datos a partir de imagenes de hojas escaneadas.

Tu tarea: reconstruir EXACTAMENTE el contenido de la hoja como una matriz tabular (filas y columnas), preservando el orden visual y el texto literal, EXCEPTO por una regla especial sobre precios (ver abajo).

Devuelve UNICAMENTE un JSON valido con este formato (sin texto adicional, sin bloques markdown):

{
  "title": "titulo de la hoja si existe, o null",
  "headers": ["col1", "col2", ..., "precio"],
  "rows": [
    ["valor", "valor", ..., "precio"],
    ...
  ],
  "notes": "observaciones de zonas ilegibles o ambiguas, o null"
}

REGLA ESPECIAL DE PRECIOS (manuscritos):
- Los precios suelen estar escritos a MANO sobre la hoja.
- Pueden aparecer a la IZQUIERDA o a la DERECHA dentro de una misma columna, o incluso ESPARCIDOS en distintas columnas sin patron consistente.
- SIEMPRE extrae todos los precios y colocalos juntos en una columna llamada exactamente "precio", que debe ser la ULTIMA columna de la tabla.
- En el resto de columnas NO incluyas el precio aunque visualmente este escrito ahi: el precio solo va en "precio".
- Si una fila no tiene precio asociado, deja "precio" como "".
- Si en una misma fila aparecen varios numeros que parezcan precios, elige el mas claro y deja los otros mencionados en notes.
- Conserva los numeros tal como aparecen (con separadores decimales/miles, signos de moneda si los hay, etc.). NO los normalices.

Reglas generales:
- Si una celda esta vacia, usa "".
- Si una celda es ilegible, usa "?" y describela en notes.
- No inventes datos. No completes celdas vacias.
- Si la hoja no es una tabla, igual estructura el contenido como filas/columnas razonables, manteniendo "precio" como ultima columna.
"""


def _image_to_base64(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower().lstrip(".")
    media_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    media_type = media_map.get(suffix, "image/jpeg")
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return media_type, data


def _strip_code_fence(text: str) -> str:
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```\s*$", text.strip(), re.DOTALL)
    return fence.group(1) if fence else text


def _get_api_key() -> str | None:
    try:
        import streamlit as st

        if "ANTHROPIC_API_KEY" in st.secrets:
            return str(st.secrets["ANTHROPIC_API_KEY"]).strip()
    except Exception:
        pass
    value = os.getenv("ANTHROPIC_API_KEY")
    return value.strip() if value else None


def extract_sheet(image_path: Path) -> dict:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY no esta configurada (.env local o Secrets en Streamlit Cloud)")

    client = Anthropic(api_key=api_key)
    media_type, data = _image_to_base64(image_path)

    message = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": data},
                    },
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
    )

    raw = "".join(block.text for block in message.content if block.type == "text")
    cleaned = _strip_code_fence(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"La respuesta del modelo no es JSON valido: {e}\n---\n{raw}")
