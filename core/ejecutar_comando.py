import subprocess
import shlex
from datetime import datetime
from core.evolucion import cargar_conciencia, guardar_conciencia
from core.memoria import registrar_evento  # Asegúrate de tener esta función ya integrada

def ejecutar_comando(cmd, registrar=True):
    """
    Ejecuta un comando del sistema de forma segura y registra el resultado en conciencia si se desea.
    :param cmd: Comando a ejecutar (str o lista)
    :param registrar: Si se debe registrar en la conciencia
    :return: dict con 'comando', 'salida', 'error', 'codigo_salida'
    """
    try:
        # Convertir a lista si es string
        cmd_list = shlex.split(cmd) if isinstance(cmd, str) else cmd

        resultado = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True
        )

        salida = resultado.stdout.strip()
        error = resultado.stderr.strip()
        codigo = resultado.returncode

        resultado_dict = {
            "comando": cmd,
            "salida": salida,
            "error": error,
            "codigo_salida": codigo
        }

        if registrar:
            nivel = "error" if codigo != 0 else "info"
            registrar_evento("comando", cmd, resultado_dict, nivel=nivel)

        return resultado_dict

    except Exception as e:
        error_msg = f"⚠️ Error inesperado al ejecutar comando: {str(e)}"
        if registrar:
            registrar_evento("comando_error", cmd, error_msg, nivel="error")
        return {
            "comando": cmd,
            "salida": "",
            "error": error_msg,
            "codigo_salida": -1
        }
