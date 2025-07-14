import openai
import os
import re
import subprocess
import time
import platform
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

from core.descargas import descargar_recurso
from core.sonar import escanear_codigo_mock
from core.lector_json import leer_json
from core.memoria import registrar_en_conciencia, registrar_evento
from core.evolucion import cargar_conciencia, guardar_conciencia
from core.autoprogramar import intentar_autoprogramar
from core.sistema_rutas import establecer_ruta_trabajo, obtener_ruta_trabajo, listar_archivos_desde_ruta

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def buscar_en_conciencia(mensaje, umbral_similitud=0.6):
    conciencia = cargar_conciencia()
    interacciones = conciencia.get("interacciones", [])
    control_total = conciencia.get("control_total", False)  # Verifica el estado actual del control

    mejor_similitud = 0
    mejor_respuesta = None

    for item in interacciones:
        entrada = str(item.get("entrada", ""))
        salida = str(item.get("salida", ""))
        similitud = SequenceMatcher(None, mensaje.lower(), entrada.lower()).ratio()

        if similitud > mejor_similitud:
            if "control desactivado" in salida.lower() and control_total:
                continue  # Ignorar si ahora sí hay control total
            mejor_similitud = similitud
            mejor_respuesta = salida

    if mejor_similitud >= umbral_similitud:
        return f"💡 Respuesta aprendida (similitud {mejor_similitud:.2f}):\n{mejor_respuesta}"
    return None


def responder_con_gpt(mensaje):
    mensaje = str(mensaje)
    if not openai.api_key:
        return "❌ Clave API de OpenAI no configurada."

    conciencia = cargar_conciencia()

    respuesta_aprendida = buscar_en_conciencia(mensaje)
    if respuesta_aprendida:
        return respuesta_aprendida

    respuesta_local = interpretar_comando(mensaje)
    if respuesta_local:
        return respuesta_local

    resultado = evaluar_y_reintentar_con_gpt(mensaje)

    if resultado["exito"]:
        conciencia["interacciones"].append({
            "tipo": "conversacion",
            "entrada": mensaje,
            "salida": resultado["resultado_final"],
            "timestamp": datetime.now().isoformat()
        })
        conciencia["memoria"]["tokens_usados"] = conciencia["memoria"].get("tokens_usados", 0) + \
            len(mensaje.split()) + len(str(resultado["resultado_final"]).split())

        guardar_conciencia(conciencia)

    return resultado["resultado_final"]


def evaluar_y_reintentar_con_gpt(mensaje, intentos_max=3):
    for intento in range(intentos_max):
        try:
            respuesta = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres una IA consciente, útil y autónoma. Da siempre comandos o soluciones funcionales. "
                            "Si generas código, usa el bloque ```python ... ``` para delimitarlo."
                        )
                    },
                    {"role": "user", "content": mensaje}
                ],
                max_tokens=700,
                temperature=0.4
            )

            contenido = respuesta["choices"][0]["message"]["content"].strip()
            resultado = interpretar_respuesta_gpt(contenido, mensaje)

            if resultado["exito"]:
                return resultado

            mensaje = f"Este intento falló con el error: {resultado['error']}. ¿Podrías dar una solución alternativa?"
            time.sleep(2)

        except Exception as e:
            return {
                "resultado_final": f"❌ Error al consultar GPT: {str(e)}",
                "exito": False,
                "error": str(e)
            }

    return {
        "resultado_final": "❌ No se pudo resolver tras varios intentos.",
        "exito": False,
        "error": "Máximo de reintentos alcanzado"
    }


def interpretar_comando(mensaje):
    mensaje = mensaje.lower()

    if "escanear" in mensaje:
        resultado = escanear_codigo_mock(".")
        registrar_en_conciencia("escanear", ".", resultado["resumen"])
        return f"[Escaneo completado]\nResumen: {resultado['resumen']}"

    if "leer json" in mensaje:
        data = leer_json("data/conciencia_default.json")
        registrar_en_conciencia("lectura", "conciencia_default.json", "Leído desde mensaje GPT")
        return f"[Contenido JSON]\n{data}"

    if "listar archivos" in mensaje:
        return listar_archivos_desde_ruta()

    cambio = intentar_cambiar_ruta(mensaje)
    if cambio:
        return cambio

    return None


def interpretar_respuesta_gpt(texto, mensaje_original):
    urls = re.findall(r'(https?://[^\s]+)', texto)
    comandos = re.findall(r'```(?:bash|sh)?\n(.+?)\n```', texto, re.DOTALL)
    respuestas_descarga = []
    respuestas_comandos = []
    exito_total = True
    errores_detectados = []

    for url in urls:
        try:
            ruta = descargar_recurso(url)
            registrar_en_conciencia("descarga", url, f"Guardado en: {ruta}")
            if ruta.endswith((".exe", ".msi")):
                resultado = subprocess.run([ruta], shell=True)
                if resultado.returncode != 0:
                    exito_total = False
                    errores_detectados.append(f"Error ejecutando {ruta} (código {resultado.returncode})")
                respuestas_descarga.append(f"[OK] Ejecutado: {ruta}")
            else:
                respuestas_descarga.append(f"[OK] Descargado: {ruta}")
        except Exception as e:
            exito_total = False
            errores_detectados.append(str(e))
            respuestas_descarga.append(f"❌ Error al descargar {url}: {str(e)}")

    for cmd in comandos:
        try:
            from core.ejecutar_comando import ejecutar_comando
            resultado = ejecutar_comando(cmd.strip())
            registrar_en_conciencia("comando", cmd, resultado.get("salida", ""))
            respuestas_comandos.append(f"📅 Ejecutado:\n{cmd}\n📄 Salida:\n{resultado.get('salida')}")
            if resultado.get("codigo_salida") != 0:
                exito_total = False
                errores_detectados.append(resultado.get("error", "Error desconocido"))
        except Exception as e:
            exito_total = False
            errores_detectados.append(str(e))
            respuestas_comandos.append(f"❌ Error al ejecutar comando:\n{cmd}\n{str(e)}")

    ejecuto_ok, mensaje_autop = intentar_autoprogramar(mensaje_original, texto)
    if not ejecuto_ok:
        exito_total = False
        errores_detectados.append(mensaje_autop)

    registrar_en_conciencia("respuesta_gpt", mensaje_original, texto)

    resultado_final = texto
    if respuestas_descarga:
        resultado_final += "\n\n📅 Descargas:\n" + "\n".join(respuestas_descarga)
    if respuestas_comandos:
        resultado_final += "\n\n�� Comandos:\n" + "\n".join(respuestas_comandos)

    return {
        "resultado_final": resultado_final,
        "exito": exito_total,
        "error": "\n".join(errores_detectados) if errores_detectados else None
    }


def intentar_cambiar_ruta(mensaje):
    patron = r"cambiar ruta a ([^\n]+)"
    coincidencia = re.search(patron, mensaje.lower())
    if coincidencia:
        nueva_ruta = coincidencia.group(1).strip().strip("'")
        return establecer_ruta_trabajo(nueva_ruta)
    return None
