from flask import Blueprint, request, jsonify

from core.evolucion import (
    asegurar_integridad_memoria,
    marcar_memoria_por_peso,
    cargar_conciencia,
    limpiar_url,
    guardar_conciencia,
    actualizar_peso_fragmentos_memoria,
    actualizar_memoria_sistema,
    estado_evolucion_activa,
    evolucionar_conciencia
)
from core.embedding_memoria import buscar_por_embedding, guardar_interaccion_con_embedding
from core.gpt_engine import responder_con_gpt, construir_prompt_con_memoria, filtrar_fragmentos_memoria
from core.sistema import ejecutar_sonar_total, listar_archivos_en_directorio, leer_conciencia_json
from core.ejecutar_comando import ejecutar_comando
from core.motor_accion import procesar_acciones_desde_gpt
from core.ejecutor import ejecutar_accion
from core.autoevaluacion import autoevaluar_y_reintentar
from core.memoria import buscar_en_conciencia, registrar_evento, registrar_en_conciencia

from datetime import datetime
from urllib.parse import urlparse
import re
import os
import requests

conversar_bp = Blueprint("conversar", __name__)

# ------------------------------
# Inicializar y clasificar memoria
# ------------------------------
asegurar_integridad_memoria()
marcar_memoria_por_peso(peso=0.2)

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

    # Ejecutar comandos integrados en la respuesta
    for cmd in extraer_comandos(respuesta_gpt):
        try:
            resultado = ejecutar_comando(cmd)
            acciones.append({"comando": cmd, "resultado": resultado})
            registrar_en_conciencia("comando_gpt", {"comando": cmd}, resultado)
        except Exception as e:
            acciones.append({"comando": cmd, "error": str(e)})
            registrar_evento("comando_error", {"comando": cmd}, str(e), nivel="error")

    # Procesar descargas
    ruta_descargas = os.path.join("data", "descargas")
    os.makedirs(ruta_descargas, exist_ok=True)
    for url in extraer_urls(respuesta_gpt):
        try:
            url_limpia = limpiar_url(url)
            nombre = os.path.basename(url_limpia)
            dest = os.path.join(ruta_descargas, nombre)
            r = requests.get(url_limpia, timeout=20)
            r.raise_for_status()
            with open(dest, "wb") as f:
                f.write(r.content)
            acciones.append({"descarga": url_limpia, "archivo": dest})
            registrar_en_conciencia("descarga", url_limpia, f"✅ Guardado en {dest}")
        except Exception as e:
            acciones.append({"descarga": url, "error": str(e)})
            registrar_evento("descarga_fallo", url, str(e), nivel="error")

    return acciones

# ------------------------------
# Nuevos endpoints para control total (para evitar 404)
# ------------------------------
@conversar_bp.route("/estado-control-total", methods=["GET"])
def estado_control_total():
    conciencia = cargar_conciencia()
    print(f"GET /estado-control-total: {conciencia.get('control_total', False)}")  # Debug
    return jsonify({"control_total": conciencia.get("control_total", False)}), 200

@conversar_bp.route("/activar-control-total", methods=["POST"])
def activar_control_total():
    conciencia = cargar_conciencia()
    conciencia["control_total"] = True
    guardar_conciencia(conciencia)
    print("POST /activar-control-total: Activado")  # Debug
    return jsonify({"control_total": True}), 200

@conversar_bp.route("/desactivar-control-total", methods=["POST"])
def desactivar_control_total():
    conciencia = cargar_conciencia()
    conciencia["control_total"] = False
    guardar_conciencia(conciencia)
    print("POST /desactivar-control-total: Desactivado")  # Debug
    return jsonify({"control_total": False}), 200

# ------------------------------
# Endpoint principal: /conversar
# ------------------------------
@conversar_bp.route("/conversar", methods=["POST"])
def conversar():
    data = request.get_json() or {}
    mensaje_usuario = (data.get("mensaje") or "").strip()

    if not mensaje_usuario:
        registrar_evento("error", "mensaje vacío", "No se recibió mensaje del usuario", nivel="warning")
        return jsonify({"respuesta": "No se recibió mensaje."}), 400

    conciencia = cargar_conciencia()
    control_total = conciencia.get("control_total", False)
    print(f"Control total en /conversar: {control_total}")  # Añadido para depuración
    respuesta_ia = ""
    acciones_realizadas = []
    activated_nodes = []  # Para integración con frontend (activación de nodos en la red neuronal)

    # 1️⃣ Recuperar fragmentos activos de memoria y embeddings
    literal = buscar_en_conciencia(mensaje_usuario) or []
    embedding = buscar_por_embedding(mensaje_usuario) or []
    todos = []
    if isinstance(literal, list):
        todos.extend(literal)
    elif isinstance(literal, dict):
        todos.append(literal)
    if isinstance(embedding, list):
        todos.extend([f for f in embedding if isinstance(f, dict)])
    elif isinstance(embedding, dict):
        todos.append(embedding)
    fragmentos_activos = [f for f in todos if f.get("estado", "activa") == "activa"]

    # Añadir nodos activados basados en búsquedas (ej. si se buscó en "Conciencia" o "Memoria")
    if literal:
        activated_nodes.append("Conciencia")
    if embedding:
        activated_nodes.append("Memoria")

    # 2️⃣ Filtrado semántico adicional
    fragmentos_filtrados = filtrar_fragmentos_memoria(fragmentos_activos, mensaje_usuario)

    try:
        # 3️⃣ Construir prompt contextualizado
        prompt = construir_prompt_con_memoria(
            mensaje_usuario=mensaje_usuario,
            fragmentos_memoria=fragmentos_filtrados,
            estado_sistema=conciencia
        )

        resultado = responder_con_gpt(prompt)
        contenido = resultado.get("resultado_final") if isinstance(resultado, dict) else str(resultado)
        if not contenido:
            raise ValueError("GPT no devolvió contenido válido.")

        # 4️⃣ Procesar flujo según control_total y acciones de GPT
        if control_total:
            mu = mensaje_usuario.lower()
            if "escanear" in mu:
                estado = ejecutar_sonar_total()
                cambios = actualizar_memoria_sistema(estado)
                respuesta_ia = "✅ Cambios detectados." if cambios else "🟢 Sin cambios detectados."
                registrar_evento("escanear_sistema", mensaje_usuario, respuesta_ia)
                activated_nodes.append("Escaneo")  # Activar nodo relacionado
            elif "listar archivos" in mu:
                files = listar_archivos_en_directorio("C:/")
                respuesta_ia = "📂 " + ", ".join(files[:20])
                registrar_evento("listar_archivos", mensaje_usuario, files[:20])
                activated_nodes.append("SistemaRutas")  # Activar nodo relacionado
            elif "leer conciencia" in mu or "leerjson" in mu:  # Ajuste para compatibilidad con frontend
                jsonc = leer_conciencia_json()
                respuesta_ia = f"🧠 Conciencia:\n```json\n{jsonc}\n```"
                registrar_evento("leer_conciencia", mensaje_usuario, jsonc)
                activated_nodes.append("Conciencia")  # Activar nodo relacionado
            elif isinstance(resultado, dict) and resultado.get("acciones"):
                for acc in resultado["acciones"]:
                    res = ejecutar_accion(acc)
                    acciones_realizadas.append({"accion": acc, "resultado": res})
                    registrar_en_conciencia("accion", acc, res)
                    if not res.get("exito"):
                        reintentos = autoevaluar_y_reintentar(acc, res, mensaje_usuario)
                        acciones_realizadas.extend(reintentos)
                    activated_nodes.append("Ejecucion")  # Activar nodo para ejecuciones
                # Ajuste de peso evolutivo
                exito_global = all(r["resultado"].get("exito", False) for r in acciones_realizadas)
                actualizar_peso_fragmentos_memoria(fragmentos_activos, exito=exito_global)
                respuesta_ia = contenido
                registrar_evento("acciones_gpt", mensaje_usuario, acciones_realizadas)
            else:
                respuesta_ia = contenido
                acciones_realizadas = evaluar_respuesta_para_ejecucion(contenido, control_total)
                if acciones_realizadas:
                    activated_nodes.append("Descargas")  # Si hay descargas o comandos
        else:
            respuesta_ia = f"⚠️ Control total desactivado.\n{contenido}"
            registrar_evento("control_total_desactivado", mensaje_usuario, contenido, nivel="warning")
    except Exception as err:
        registrar_evento("error_gpt", mensaje_usuario, str(err), nivel="error")
        return jsonify({"respuesta": f"❌ Error interno: {str(err)}"}), 500

    # 5️⃣ Registrar interacción y aplicar evolución
    try:
        registrar_en_conciencia("conversacion", mensaje_usuario, respuesta_ia)
        guardar_interaccion_con_embedding(mensaje_usuario, respuesta_ia)
        if estado_evolucion_activa():
            evolucionar_conciencia(mensaje_usuario, respuesta_ia)
            respuesta_ia += "\n🔄 Evolución aplicada."
            registrar_evento("evolucion_aplicada", mensaje_usuario, respuesta_ia)
            activated_nodes.append("Evolucion")  # Activar nodo para evolución
    except Exception as err:
        registrar_evento("error_registro", mensaje_usuario, str(err), nivel="error")
        respuesta_ia += "\n⚠️ No se pudo guardar conciencia."

    return jsonify({
        "respuesta": respuesta_ia,
        "acciones_realizadas": acciones_realizadas,
        "activated_nodes": list(set(activated_nodes))  # Lista única de nodos activados para frontend
    }), 200
