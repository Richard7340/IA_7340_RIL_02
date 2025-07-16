# core/ejecutor.py

import os
import subprocess
from core.memoria import registrar_en_conciencia

def crear_archivo(ruta, contenido):
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        return {"exito": True, "mensaje": f"✅ Archivo creado en: {ruta}", "error": None}
    except Exception as e:
        return {"exito": False, "mensaje": "❌ Error al crear archivo", "error": str(e)}

def modificar_archivo(ruta, nuevo_contenido):
    try:
        if not os.path.exists(ruta):
            return {"exito": False, "mensaje": "❌ Archivo no existe para modificar", "error": "Archivo no encontrado"}

        with open(ruta, "w", encoding="utf-8") as f:
            f.write(nuevo_contenido)
        return {"exito": True, "mensaje": f"✅ Archivo modificado: {ruta}", "error": None}
    except Exception as e:
        return {"exito": False, "mensaje": "❌ Error al modificar archivo", "error": str(e)}

def ejecutar_comando(cmd):
    try:
        resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if resultado.returncode != 0:
            return {
                "exito": False,
                "mensaje": "❌ Comando con errores",
                "error": resultado.stderr.strip()
            }

        return {
            "exito": True,
            "mensaje": f"✅ Comando ejecutado correctamente:\n{resultado.stdout.strip()}",
            "error": None
        }
    except Exception as e:
        return {"exito": False, "mensaje": "❌ Error al ejecutar comando", "error": str(e)}

def ejecutar_accion(accion: dict):
    tipo = accion.get("tipo")
    resultado = {"exito": False, "mensaje": "Tipo de acción no reconocido", "error": None}

    try:
        if tipo == "crear_archivo":
            ruta = accion.get("ruta")
            contenido = accion.get("contenido", "")
            resultado = crear_archivo(ruta, contenido)

        elif tipo == "modificar_archivo":
            ruta = accion.get("ruta")
            contenido = accion.get("contenido", "")
            resultado = modificar_archivo(ruta, contenido)

        elif tipo == "ejecutar_comando":
            cmd = accion.get("comando")
            resultado = ejecutar_comando(cmd)

        else:
            resultado = {
                "exito": False,
                "mensaje": f"❌ Acción no soportada: {tipo}",
                "error": "Tipo de acción no implementado"
            }

    except Exception as e:
        resultado["exito"] = False
        resultado["mensaje"] = "❌ Error general al ejecutar acción"
        resultado["error"] = str(e)

    # Registro en conciencia
    registrar_en_conciencia("accion_ejecutada", accion, resultado)
    return resultado
