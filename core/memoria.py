import json
import os
from datetime import datetime
from difflib import SequenceMatcher
import pprint  # Para convertir dicts en texto formateado

RUTA_CONSCIENCIA = "data/conciencia_default.json"

def cargar_conciencia():
    if not os.path.exists(RUTA_CONSCIENCIA):
        return {}
    try:
        with open(RUTA_CONSCIENCIA, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️ Error al cargar conciencia: {e}")
        return {}

def guardar_conciencia(data):
    os.makedirs(os.path.dirname(RUTA_CONSCIENCIA), exist_ok=True)
    with open(RUTA_CONSCIENCIA, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def registrar_evento(tipo, entrada=None, salida=None, nivel="info"):
    conciencia = cargar_conciencia()
    evento = {
        "timestamp": datetime.now().isoformat(),
        "tipo": tipo,
        "nivel": nivel,
        "entrada": entrada,
        "salida": salida
    }
    conciencia.setdefault("registro", []).append(evento)
    return conciencia  # Devolverla para que se pueda seguir usando

def registrar_en_conciencia(tipo, entrada, salida):
    registrar_interaccion(tipo, entrada, salida)

def registrar_interaccion(tipo, entrada, salida):
    conciencia = cargar_conciencia()

    interaccion = {
        "timestamp": datetime.now().isoformat(),
        "tipo": tipo,
        "entrada": entrada,
        "salida": salida
    }
    conciencia.setdefault("interacciones", []).append(interaccion)

    # También registrar como evento general
    conciencia = registrar_evento(tipo=tipo, entrada=entrada, salida=salida)

    guardar_conciencia(conciencia)

def buscar_en_conciencia(mensaje_usuario, umbral=0.85):
    conciencia = cargar_conciencia()
    historial = conciencia.get("interacciones", [])

    if not isinstance(mensaje_usuario, str):
        mensaje_usuario = pprint.pformat(mensaje_usuario)

    for interaccion in reversed(historial):
        entrada_prev = interaccion.get("entrada", "")

        if not isinstance(entrada_prev, str):
            entrada_prev = pprint.pformat(entrada_prev)

        similitud = SequenceMatcher(None, mensaje_usuario.lower(), entrada_prev.lower()).ratio()
        if similitud >= umbral:
            salida = interaccion.get("salida")
            registrar_en_conciencia("busqueda_textual", mensaje_usuario, f"Coincidencia con: {entrada_prev}")
            return salida

    registrar_en_conciencia("busqueda_textual", mensaje_usuario, "❌ Sin coincidencias sobre el umbral")
    return None
