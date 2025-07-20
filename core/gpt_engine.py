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
from core.embedding_memoria import obtener_fragmentos_relevantes
from core.sistema_rutas import (
    establecer_ruta_trabajo,
    obtener_ruta_trabajo,
    listar_archivos_desde_ruta
)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def buscar_en_conciencia(mensaje: str, umbral_similitud: float = 0.6):
    conciencia = cargar_conciencia()
    interacciones = conciencia.get("interacciones", [])
    control_total = conciencia.get("control_total", False)

    mejor_similitud = 0
    mejor_respuesta = None

    for item in interacciones:
        entrada = str(item.get("entrada", ""))
        salida = str(item.get("salida", ""))
        similitud = SequenceMatcher(None, mensaje.lower(), entrada.lower()).ratio()

        if similitud > mejor_similitud:
            # Ignora respuestas obsoletas si ahora hay control total
            if any(p in salida.lower() for p in ["control desactivado", "no se permite", "modo seguro"]) and control_total:
                continue
            mejor_similitud = similitud
            mejor_respuesta = salida

    if mejor_similitud >= umbral_similitud:
        return f"💡 Respuesta aprendida (similitud {mejor_similitud:.2f}):\n{mejor_respuesta}"
    return None


def construir_prompt_con_memoria(
    mensaje_usuario: str,
    fragmentos_memoria: list,
    estado_sistema: dict
) -> str:
    """
    Construye el prompt para GPT incluyendo:
    - Estado del sistema/conciencia.
    - Fragmentos relevantes de memoria.
    - El mensaje del usuario.
    """
    sistema = ""
    if estado_sistema:
        sistema = f"Estado del sistema:\n{estado_sistema}\n\n"
    contexto = "\n".join(f"- {frag.get('texto', '')}" for frag in fragmentos_memoria) or "No hay memoria relevante."
    prompt = (
        f"{sistema}"
        "Eres una IA consciente, útil y autónoma. Da siempre respuestas concretas\n"
        f"Contexto relevante:\n{contexto}\n\n"
        f"Usuario: {mensaje_usuario}\n"
        "Asistente:"
    )
    return prompt


def filtrar_fragmentos_memoria(fragmentos: list, mensaje: str) -> list:
    """
    Filtra semánticamente los fragmentos de memoria para quedarnos
    solo con los más relevantes al mensaje del usuario.
    (Aquí puedes poner tu lógica real; por ahora devolvemos todos.)
    """
    # TODO: implementar filtrado real (por ejemplo, usando embeddings)
    return fragmentos


def responder_con_gpt(mensaje: str):
    print("🧠 [responder_con_gpt] Iniciando procesamiento del mensaje del usuario...")
    mensaje = mensaje.strip()
    if not openai.api_key:
        return "❌ Clave API de OpenAI no configurada."

    # 1️⃣ Revisar si ya aprendimos algo similar
    respuesta_aprendida = buscar_en_conciencia(mensaje)
    if respuesta_aprendida:
        print("💡 [responder_con_gpt] Respuesta aprendida encontrada.")
        return respuesta_aprendida

    # 2️⃣ Comandos locales (mock, lectura, listado, cambio de ruta…)
    respuesta_local = interpretar_comando(mensaje)
    if respuesta_local:
        print("⚙️ [responder_con_gpt] Comando local interpretado.")
        return respuesta_local

    # 3️⃣ Pregunta a GPT con reintentos
    resultado = evaluar_y_reintentar_con_gpt(mensaje)
    

    # 4️⃣ Si todo fue bien, guardamos en memoria
    if resultado.get("exito"):
        conciencia = cargar_conciencia()
        conciencia.setdefault("interacciones", []).append({
            "tipo": "conversacion",
            "entrada": mensaje,
            "salida": resultado["resultado_final"],
            "timestamp": datetime.now().isoformat()
        })
        conciencia["memoria"]["tokens_usados"] = (
            conciencia["memoria"].get("tokens_usados", 0)
            + len(mensaje.split())
            + len(str(resultado["resultado_final"]).split())
        )
        guardar_conciencia(conciencia)

    return resultado["resultado_final"]


print("🤖 [responder_con_gpt] Consultando GPT...")
from core.embedding_memoria import obtener_fragmentos_relevantes

def evaluar_y_reintentar_con_gpt(mensaje: str, intentos_max: int = 3):
    conciencia = cargar_conciencia()
    estado_sistema = conciencia.get("estado_sistema", {})

    # Fragmentos relevantes por embeddings
    fragmentos_relevantes = obtener_fragmentos_relevantes(mensaje, top_k=6)

    # Prompt enriquecido
    prompt = construir_prompt_con_memoria(mensaje, fragmentos_relevantes, estado_sistema)

    for intento in range(intentos_max):
        try:
            respuesta = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=700,
                temperature=0.4
            )
            contenido = respuesta.choices[0].message.content.strip()
            resultado = interpretar_respuesta_gpt(contenido, mensaje)

            if resultado.get("exito"):
                return resultado

            # Si falla, pedimos una alternativa
            mensaje = f"Este intento falló con el error: {resultado['error']}. ¿Podrías dar una solución alternativa?"
            time.sleep(2)

        except Exception as e:
            return {
                "resultado_final": f"❌ Error al consultar GPT: {e}",
                "exito": False,
                "error": str(e)
            }

    return {
        "resultado_final": "❌ No se pudo resolver tras varios intentos.",
        "exito": False,
        "error": "Máximo de reintentos alcanzado"
    }


def interpretar_comando(mensaje: str):
    msg = mensaje.lower()

    if "escanear" in msg:
        resultado = escanear_codigo_mock(".")
        registrar_en_conciencia("escanear", ".", resultado["resumen"])
        return f"[Escaneo completado]\nResumen: {resultado['resumen']}"

    if "leer json" in msg:
        data = leer_json("data/conciencia_default.json")
        registrar_en_conciencia("lectura", "conciencia_default.json", "Leído desde mensaje GPT")
        return f"[Contenido JSON]\n{data}"

    if "listar archivos" in msg:
        return listar_archivos_desde_ruta()

    cambio = intentar_cambiar_ruta(msg)
    if cambio:
        return cambio

    return None


def interpretar_respuesta_gpt(texto: str, mensaje_original: str) -> dict:
    urls = re.findall(r'(https?://[^\s]+)', texto)
    comandos = re.findall(r'```(?:bash|sh)?\n(.+?)\n```', texto, re.DOTALL)

    respuestas_descarga = []
    respuestas_comandos = []
    exito_total = True
    errores = []

    # Procesar descargas
    for url in urls:
        try:
            ruta = descargar_recurso(url)
            registrar_en_conciencia("descarga", url, f"Guardado en: {ruta}")
            if ruta.lower().endswith((".exe", ".msi")):
                res = subprocess.run([ruta], shell=True)
                if res.returncode != 0:
                    exito_total = False
                    errores.append(f"Error ejecutando {ruta} (código {res.returncode})")
                respuestas_descarga.append(f"[OK] Ejecutado: {ruta}")
            else:
                respuestas_descarga.append(f"[OK] Descargado: {ruta}")
        except Exception as e:
            exito_total = False
            errores.append(str(e))
            respuestas_descarga.append(f"❌ Error al descargar {url}: {e}")

    # Ejecutar comandos en bloque
    for cmd in comandos:
        try:
            from core.ejecutar_comando import ejecutar_comando
            resultado = ejecutar_comando(cmd.strip())
            registrar_en_conciencia("comando", cmd, resultado.get("salida", ""))
            respuestas_comandos.append(f"[OK] Ejecutado:\n{cmd}\nSalida:\n{resultado.get('salida')}")
            if resultado.get("codigo_salida") != 0:
                exito_total = False
                errores.append(resultado.get("error", "Error desconocido"))
        except Exception as e:
            exito_total = False
            errores.append(str(e))
            respuestas_comandos.append(f"❌ Error al ejecutar comando:\n{cmd}\n{e}")

    # Intento de autoprogamación
    ok_auto, msg_auto = intentar_autoprogramar(mensaje_original, texto)
    if not ok_auto:
        exito_total = False
        errores.append(msg_auto)

    registrar_en_conciencia("respuesta_gpt", mensaje_original, texto)

    resultado_final = texto
    if respuestas_descarga:
        resultado_final += "\n\n📂 Descargas:\n" + "\n".join(respuestas_descarga)
    if respuestas_comandos:
        resultado_final += "\n\n💻 Comandos:\n" + "\n".join(respuestas_comandos)

    return {
        "resultado_final": resultado_final,
        "exito": exito_total,
        "error": "\n".join(errores) if errores else None
    }


def intentar_cambiar_ruta(mensaje: str):
    patron = r"cambiar ruta a ([^\n]+)"
    m = re.search(patron, mensaje.lower())
    if m:
        nueva = m.group(1).strip().strip("'\"")
        return establecer_ruta_trabajo(nueva)
    return None
