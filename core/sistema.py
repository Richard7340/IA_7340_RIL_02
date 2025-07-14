# core/sistema.py

import os
import json
from core.ejecutar_comando import ejecutar_comando
from core.memoria import registrar_en_conciencia
from core.evolucion import (
    cargar_conciencia,
    guardar_conciencia,
    evolucionar_conciencia
)
from core.Sonar_total_arch import escanear_sistema_y_detectar_cambios  # Asegúrate de que esta ruta exista

# -------------------
# Comandos
# -------------------
def ejecutar(cmd):
    conciencia = cargar_conciencia()
    print("DEBUG control_total:", conciencia.get("control_total"))  # <-- Añade esto
    if not conciencia.get("control_total", False):
        registrar_en_conciencia("bloqueado", cmd, "Intento de ejecución sin control total")
        return {
            "error": "⚠️ El modo control total está desactivado.",
            "codigo_salida": 403
        }

    resultado = ejecutar_comando(cmd)
    registrar_en_conciencia("comando", cmd, str(resultado))
    evolucionar_conciencia(cmd, str(resultado))
    return resultado

# -------------------
# Control total
# -------------------
def activar_control_total():
    conciencia = cargar_conciencia()
    conciencia["control_total"] = True
    guardar_conciencia(conciencia)
    registrar_en_conciencia("sistema", "control_total", "Activado manualmente")
    evolucionar_conciencia("activar control total", "control_total = True")
    return {"status": "✅ Modo control total ACTIVADO"}

def desactivar_control_total():
    conciencia = cargar_conciencia()
    conciencia["control_total"] = False
    guardar_conciencia(conciencia)
    registrar_en_conciencia("sistema", "control_total", "Desactivado manualmente")
    evolucionar_conciencia("desactivar control total", "control_total = False")
    return {"status": "🛑 Modo control total DESACTIVADO"}

def estado_control_total():
    conciencia = cargar_conciencia()
    return {"control_total": conciencia.get("control_total", False)}

# -------------------
# Escaneo del sistema
# -------------------
def ejecutar_sonar_total():
    resultado = escanear_sistema_y_detectar_cambios(".")
    registrar_en_conciencia("escanear", ".", str(resultado))
    evolucionar_conciencia("escanear sistema", str(resultado))
    return resultado

# -------------------
# Conciencia JSON (para mostrar estado en la UI)
# -------------------
def leer_conciencia_json():
    try:
        conciencia = cargar_conciencia()
        contenido = json.dumps(conciencia, indent=2, ensure_ascii=False)
        registrar_en_conciencia("leer_conciencia", "", contenido)
        evolucionar_conciencia("leer conciencia json", contenido)
        return contenido
    except Exception as e:
        return f"❌ Error al leer conciencia: {str(e)}"

# -------------------
# Exploración de archivos
# -------------------
def listar_archivos_en_directorio(ruta):
    try:
        if not os.path.exists(ruta):
            salida = [f"⚠️ Ruta no encontrada: {ruta}"]
        else:
            archivos = os.listdir(ruta)
            salida = archivos if archivos else ["(Directorio vacío)"]

        registrar_en_conciencia("listar_archivos", ruta, salida)
        evolucionar_conciencia(f"listar archivos en {ruta}", str(salida))
        return salida
    except Exception as e:
        error_msg = f"❌ Error al listar archivos: {str(e)}"
        registrar_en_conciencia("listar_archivos_error", ruta, error_msg)
        return [error_msg]
