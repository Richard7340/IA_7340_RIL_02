import os
import json
from datetime import datetime
from core.memoria import registrar_en_conciencia

# Ruta donde se guarda el estado anterior del sistema escaneado
RUTA_ESTADO_ANTERIOR = "data/estado_sistema_anterior.json"

def obtener_estructura_directorio(ruta_base="."):
    """
    Recorre el disco desde una ruta base y devuelve una lista con información de archivos.
    """
    estructura = []
    for dirpath, _, filenames in os.walk(ruta_base):
        for nombre in filenames:
            ruta_completa = os.path.join(dirpath, nombre)
            try:
                tamano = os.path.getsize(ruta_completa)
                estructura.append({"ruta": ruta_completa, "tamano": tamano})
            except Exception:
                estructura.append({"ruta": ruta_completa, "tamano": "error"})
    return estructura

def guardar_estado_actual(estructura):
    """
    Guarda el estado actual del sistema en disco para comparaciones futuras.
    """
    os.makedirs("data", exist_ok=True)
    with open(RUTA_ESTADO_ANTERIOR, "w", encoding="utf-8") as f:
        json.dump(estructura, f, indent=2, ensure_ascii=False)

def cargar_estado_anterior():
    """
    Carga el último estado del sistema guardado, si existe.
    """
    if not os.path.exists(RUTA_ESTADO_ANTERIOR):
        return []
    try:
        with open(RUTA_ESTADO_ANTERIOR, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def comparar_estados(actual, anterior):
    """
    Compara dos estados del sistema de archivos y devuelve archivos nuevos o modificados.
    """
    rutas_anteriores = {item["ruta"]: item["tamano"] for item in anterior}
    nuevas = []
    modificadas = []

    for item in actual:
        ruta = item["ruta"]
        tamano = item["tamano"]
        if ruta not in rutas_anteriores:
            nuevas.append(item)
        elif rutas_anteriores[ruta] != tamano:
            modificadas.append(item)

    return nuevas, modificadas

def escanear_sistema_y_detectar_cambios(ruta_base="."):
    """
    Realiza el escaneo completo, compara con el anterior y registra si hay novedades.
    """
    actual = obtener_estructura_directorio(ruta_base)
    anterior = cargar_estado_anterior()

    nuevas, modificadas = comparar_estados(actual, anterior)

    if nuevas or modificadas:
        resumen = {
            "nuevos_archivos": len(nuevas),
            "archivos_modificados": len(modificadas),
            "timestamp": datetime.now().isoformat(),
        }
        detalles = {
            "nuevos": nuevas,
            "modificados": modificadas
        }

        registrar_en_conciencia("escanear_sistema", resumen, detalles)
        guardar_estado_actual(actual)

        return {
            "resumen": resumen,
            "detalles": detalles,
            "mensaje": "✅ Cambios detectados y registrados en conciencia."
        }

    return {
        "resumen": {"mensaje": "Sin cambios detectados"},
        "detalles": {},
        "mensaje": "✔️ No hay diferencias con el último estado registrado."
    }
