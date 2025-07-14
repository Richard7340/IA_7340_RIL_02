import json
import os
from datetime import datetime

RUTA_CONSCIENCIA = "data/conciencia_default.json"

def cargar_conciencia():
    if not os.path.exists(RUTA_CONSCIENCIA):
        return {}
    with open(RUTA_CONSCIENCIA, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_conciencia(data):
    with open(RUTA_CONSCIENCIA, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def estado_evolucion_activa():
    conciencia = cargar_conciencia()
    return conciencia.get("control_total", False)

def evolucionar_conciencia(entrada, salida):
    conciencia = cargar_conciencia()

    conciencia.setdefault("memoria", {}).setdefault("interacciones", [])
    conciencia.setdefault("registro", [])
    conciencia.setdefault("habilidades", {})

    conciencia["registro"].append({
        "timestamp": datetime.now().isoformat(),
        "entrada": entrada,
        "salida": salida
    })

    mejoras = {
        "instalar": ["tecnologia", "control_sistema", "ejecucion_scripts"],
        "leer": ["lectura_json", "comprension_lectora"],
        "descargar": ["uso_api", "exploracion_archivos"],
        "json": ["lectura_json"],
        "escanear": ["analisis_errores", "optimizacion_procesos"],
        "comando": ["ejecucion_scripts", "control_sistema"],
        "tarea": ["gestion_tareas", "planificacion"]
    }

    for clave, habilidades in mejoras.items():
        if clave in entrada.lower() or clave in salida.lower():
            for hab in habilidades:
                conciencia["habilidades"][hab] = min(100, conciencia["habilidades"].get(hab, 50) + 1)

    conciencia["memoria"]["tokens_usados"] += len(entrada.split()) + len(salida.split())
    guardar_conciencia(conciencia)

def actualizar_memoria_sistema(nueva_info: dict):
    conciencia = cargar_conciencia()
    memoria_actual = conciencia.get("memoria", {})
    cambios_detectados = False

    for clave, valor in nueva_info.items():
        if memoria_actual.get(clave) != valor:
            memoria_actual[clave] = valor
            cambios_detectados = True

    if cambios_detectados:
        conciencia["memoria"] = memoria_actual
        conciencia["registro"].append({
            "timestamp": datetime.now().isoformat(),
            "entrada": "actualización del sistema detectada",
            "salida": "se ha actualizado la memoria con nueva información del sistema"
        })
        guardar_conciencia(conciencia)
        return True, memoria_actual

    return False, memoria_actual
