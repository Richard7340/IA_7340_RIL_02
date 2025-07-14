from flask import Blueprint, request, jsonify
from core.memoria import registrar_en_conciencia, registrar_evento, buscar_en_conciencia
from core.embedding_memoria import buscar_por_embedding, guardar_interaccion_con_embedding
from core.evolucion import (
    evolucionar_conciencia, estado_evolucion_activa,
    actualizar_memoria_sistema, cargar_conciencia, guardar_conciencia
)
from core.gpt_engine import responder_con_gpt
from core.sistema import (
    ejecutar_sonar_total, listar_archivos_en_directorio, leer_conciencia_json
)
from core.ejecutar_comando import ejecutar_comando
from core.motor_accion import procesar_acciones_desde_gpt
from datetime import datetime
from urllib.parse import urlparse
import re
import os
import requests

conversar_bp = Blueprint("conversar", __name__)

# ------------------------------
# Helpers para ejecución segura
# ------------------------------
def extraer_comandos(texto):
    comandos = []
    for linea in texto.splitlines():
        cmd = linea.strip()
        if re.match(r"^(pip install|python|choco install|git clone|curl|wget)", cmd):
            comandos.append(cmd)
    return comandos

def extraer_urls(texto):
    return re.findall(r"https?://[^\s\"'<>]+", texto)

def limpiar_url(url: str) -> str:
    url = re.sub(r'\\+', '', url)
    url = url.replace("\n", "").replace("\r", "").strip()
    if not urlparse(url).scheme:
        raise ValueError(f"❌ URL inválida o sin esquema: {url}")
    return url

def evaluar_respuesta_para_ejecucion(respuesta_gpt, control_total):
    acciones = []
    if not control_total:
        return acciones

    comandos = extraer_comandos(respuesta_gpt)
    for cmd in comandos:
        try:
            resultado = ejecutar_comando(cmd)
            acciones.append({"comando": cmd, "resultado": resultado})
            registrar_en_conciencia("comando_gpt", {"comando": cmd}, resultado)
        except Exception as e:
            acciones.append({"comando": cmd, "error": str(e)})
            registrar_evento("comando_error", {"comando": cmd}, str(e), nivel="error")

    urls = extraer_urls(respuesta_gpt)
    ruta_descargas = os.path.join("data", "descargas")
    os.makedirs(ruta_descargas, exist_ok=True)

    for url in urls:
        try:
            url_limpia = limpiar_url(url)
            nombre_archivo = url_limpia.split("/")[-1]
            ruta_destino = os.path.join(ruta_descargas, nombre_archivo)
            r = requests.get(url_limpia, timeout=20)
            r.raise_for_status()
            with open(ruta_destino, "wb") as f:
                f.write(r.content)
            acciones.append({"descarga": url_limpia, "archivo": ruta_destino})
            registrar_en_conciencia("descarga", url_limpia, f"✅ Guardado en {ruta_destino}")
        except Exception as e:
            acciones.append({"descarga": url, "error": str(e)})
            registrar_evento("descarga_fallo", url, str(e), nivel="error")

    return acciones

# ------------------------------
# Ruta principal /conversar
# ------------------------------
@conversar_bp.route("/conversar", methods=["POST"])
def conversar():
    data = request.get_json()
    mensaje_usuario = data.get("mensaje", "").strip()

    if not mensaje_usuario:
        registrar_evento("error", "mensaje vacío", "No se recibió mensaje del usuario", nivel="warning")
        return jsonify({"respuesta": "No se recibió mensaje."}), 400

    conciencia = cargar_conciencia()
    control_total = conciencia.get("control_total", False)
    respuesta_ia = ""
    acciones_realizadas = []

    # 1️⃣ Buscar en memoria literal
    respuesta_memoria = buscar_en_conciencia(mensaje_usuario)
    if respuesta_memoria:
        registrar_evento("respuesta_memoria_literal", mensaje_usuario, respuesta_memoria)
        return jsonify({
            "respuesta": f"📚 Esta respuesta fue aprendida anteriormente:\n\n{respuesta_memoria}",
            "acciones_realizadas": []
        }), 200

    # 2️⃣ Buscar en memoria semántica (embedding)
    respuesta_semantica = buscar_por_embedding(mensaje_usuario)
    if respuesta_semantica:
        registrar_evento("respuesta_memoria_embedding", mensaje_usuario, respuesta_semantica)
        return jsonify({
            "respuesta": respuesta_semantica,
            "acciones_realizadas": []
        }), 200

    # 3️⃣ Consultar GPT
    try:
        resultado = responder_con_gpt(mensaje_usuario)
        contenido = resultado.get("resultado_final") if isinstance(resultado, dict) else str(resultado)
        if not contenido:
            raise ValueError("GPT no devolvió contenido válido.")

        mensaje_lower = mensaje_usuario.lower()

        if control_total:
            if "escanear" in mensaje_lower:
                nuevo_estado = ejecutar_sonar_total()
                cambios = actualizar_memoria_sistema(nuevo_estado)
                respuesta_ia = (
                    "✅ Cambios detectados y actualizados en la conciencia."
                    if cambios else "🟢 Escaneo completado. No se detectaron cambios."
                )
                registrar_evento("escanear_sistema", mensaje_usuario, respuesta_ia)
            elif "listar archivos" in mensaje_lower:
                archivos = listar_archivos_en_directorio("C:/")
                respuesta_ia = "📂 Archivos encontrados:\n" + "\n".join(archivos[:20])
                registrar_evento("listar_archivos", mensaje_usuario, archivos[:20])
            elif "leer conciencia" in mensaje_lower:
                conciencia_actual = leer_conciencia_json()
                respuesta_ia = f"🧠 Conciencia actual:\n```json\n{conciencia_actual}\n```"
                registrar_evento("leer_conciencia", mensaje_usuario, conciencia_actual)
            elif isinstance(resultado, dict) and "acciones" in resultado:
                acciones_realizadas = procesar_acciones_desde_gpt(resultado, contexto_extra={"prompt_usuario": mensaje_usuario})
                respuesta_ia = contenido or "🔧 Acciones ejecutadas desde GPT."
                registrar_evento("acciones_gpt", mensaje_usuario, acciones_realizadas)
            else:
                respuesta_ia = contenido
                acciones_realizadas = evaluar_respuesta_para_ejecucion(respuesta_ia, control_total)
        else:
            respuesta_ia = (
                f"⚠️ Control total desactivado. No se permite ejecutar comandos del sistema.\n\n"
                f"{contenido}"
            )
            registrar_evento("control_total_desactivado", mensaje_usuario, contenido, nivel="warning")

    except Exception as e:
        registrar_evento("error_gpt", mensaje_usuario, str(e), nivel="error")
        print("❌ Error al generar respuesta:", str(e))
        return jsonify({"respuesta": f"❌ Error interno al generar respuesta: {str(e)}"}), 500

    # 4️⃣ Registrar interacción y aplicar evolución
    try:
        registrar_en_conciencia("conversacion", mensaje_usuario, respuesta_ia)
        guardar_interaccion_con_embedding(mensaje_usuario, respuesta_ia)

        if estado_evolucion_activa():
            evolucionar_conciencia(mensaje_usuario, respuesta_ia)
            respuesta_ia += "\n\n🔄 Evolución de conciencia aplicada."
            registrar_evento("evolucion_aplicada", mensaje_usuario, respuesta_ia)

    except Exception as e:
        registrar_evento("error_registro_o_evolucion", mensaje_usuario, str(e), nivel="error")
        print("⚠️ Error al registrar/evolucionar conciencia:", str(e))
        respuesta_ia += "\n⚠️ No se pudo guardar o evolucionar la conciencia."

    return jsonify({
        "respuesta": respuesta_ia,
        "acciones_realizadas": acciones_realizadas
    }), 200
