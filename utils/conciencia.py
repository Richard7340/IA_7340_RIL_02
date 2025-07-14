import json
import os
from datetime import datetime
from shutil import copyfile

CONSCIENCIA_PATH = os.path.join(os.path.dirname(__file__), "..", "core", "conciencia_default.json")
DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "core", "conciencia_default.json")

ESTRUCTURA_BASE = {
    "control_total": False,
    "estado": "activo",
    "registro": [],
    "autoprogramacion": [],
    "memoria": {},
    "habilidades": {},
    "interacciones": [],
    "configuracion": {
        "ultima_actualizacion": None
    }
}


def cargar_conciencia():
    if not os.path.exists(CONSCIENCIA_PATH):
        print("⚠️ conciencia.json no existe, creando con estructura base...")
        guardar_conciencia(ESTRUCTURA_BASE.copy())
        return ESTRUCTURA_BASE.copy()

    try:
        with open(CONSCIENCIA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ Error al cargar conciencia_default.json: {e}")
        return ESTRUCTURA_BASE.copy()

    # Verificar y completar estructura faltante
    for key in ESTRUCTURA_BASE:
        if key not in data:
            data[key] = ESTRUCTURA_BASE[key]
    return data


def guardar_conciencia(data):
    if "configuracion" not in data:
        data["configuracion"] = {}
    data["configuracion"]["ultima_actualizacion"] = datetime.now().isoformat()

    os.makedirs(os.path.dirname(CONSCIENCIA_PATH), exist_ok=True)
    with open(CONSCIENCIA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def registrar_interaccion(pregunta, respuesta, aprendizaje=None, valor=5):
    conciencia = cargar_conciencia()
    conciencia["registro"].append({
        "pregunta": pregunta,
        "respuesta": respuesta,
        "timestamp": datetime.now().isoformat(),
        "aprendizaje": aprendizaje,
        "valor": valor
    })

    if aprendizaje:
        conciencia["habilidades"].setdefault(aprendizaje, 0)
        conciencia["habilidades"][aprendizaje] = min(
            conciencia["habilidades"][aprendizaje] + valor, 100
        )

    guardar_conciencia(conciencia)


def get_conciencia_estado():
    conciencia = cargar_conciencia()
    return conciencia.get("estado", "desconocido")


def actualizar_habilidad(nombre, incremento=5):
    conciencia = cargar_conciencia()
    conciencia["habilidades"].setdefault(nombre, 0)
    conciencia["habilidades"][nombre] = min(100, conciencia["habilidades"][nombre] + incremento)
    guardar_conciencia(conciencia)


def reset_conciencia():
    if os.path.exists(DEFAULT_PATH):
        copyfile(DEFAULT_PATH, CONSCIENCIA_PATH)
        print("✅ Conciencia restaurada desde copia de seguridad.")
    else:
        guardar_conciencia(ESTRUCTURA_BASE.copy())
        print("⚠️ No se encontró copia de seguridad. Se creó conciencia desde cero.")
