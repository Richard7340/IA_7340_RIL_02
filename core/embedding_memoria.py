import openai
import os
import json
from datetime import datetime
from typing import List
from numpy import dot
from numpy.linalg import norm

from core.memoria import registrar_en_conciencia
from core.evolucion import cargar_conciencia, guardar_conciencia, evolucionar_conciencia

openai.api_key = os.getenv("OPENAI_API_KEY")
RUTA_CONSCIENCIA = "data/conciencia_default.json"

# -------------------------------
# Generar embedding desde texto
# -------------------------------
def generar_embedding(texto: str) -> List[float]:
    try:
        response = openai.Embedding.create(
            input=texto,
            model="text-embedding-3-small"
        )
        return response['data'][0]['embedding']
    except Exception as e:
        registrar_en_conciencia("embedding_error", texto, f"❌ Error: {str(e)}")
        return []

# -------------------------------
# Guardar interacción con embedding
# -------------------------------
def guardar_interaccion_con_embedding(entrada: str, salida: str):
    if not entrada or not salida:
        return

    embedding = generar_embedding(entrada)
    if not embedding:
        return

    nueva = {
        "timestamp": datetime.now().isoformat(),
        "tipo": "embedding",
        "entrada": entrada,
        "salida": salida,
        "embedding": embedding
    }

    conciencia = cargar_conciencia()
    conciencia.setdefault("interacciones", []).append(nueva)
    guardar_conciencia(conciencia)

    registrar_en_conciencia("embedding_guardado", entrada, salida)

    if conciencia.get("evolucion_activa", False):
        evolucionar_conciencia(entrada, salida)

# -------------------------------
# Buscar por similitud semántica
# -------------------------------
def buscar_por_embedding(texto: str, umbral=0.85):
    consulta_emb = generar_embedding(texto)
    if not consulta_emb:
        registrar_en_conciencia("embedding_fallo", texto, "⚠️ No se pudo generar embedding")
        return None

    conciencia = cargar_conciencia()
    interacciones = conciencia.get("interacciones", [])

    mejores = []
    for interaccion in interacciones:
        emb = interaccion.get("embedding")
        if not emb:
            continue
        sim = similitud_coseno(consulta_emb, emb)
        if sim >= umbral:
            mejores.append((sim, interaccion))

    if not mejores:
        registrar_en_conciencia("embedding_sin_coincidencia", texto, "🤷 Sin resultados sobre umbral")
        return None

    mejores.sort(reverse=True, key=lambda x: x[0])
    mejor = mejores[0]
    resultado = f"💡 Respuesta similar (similitud {mejor[0]:.2f}):\n\n{mejor[1]['salida']}"

    registrar_en_conciencia("embedding_encontrado", texto, resultado)

    if conciencia.get("evolucion_activa", False):
        evolucionar_conciencia(texto, resultado)

    return resultado

# -------------------------------
# Similitud coseno
# -------------------------------
def similitud_coseno(v1, v2):
    try:
        return dot(v1, v2) / (norm(v1) * norm(v2))
    except Exception:
        return 0.0
