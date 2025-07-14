from flask import Blueprint, request, jsonify
from core.descargas import descargar_recurso
from core.lector_json import leer_json
from core.sonar import escanear_codigo_mock
from core.memoria import registrar_en_conciencia
from core.evolucion import actualizar_memoria_sistema
from core.sistema import ejecutar_sonar_total
from utils.conciencia import reset_conciencia, get_conciencia_estado
from utils.conciencia import cargar_conciencia, guardar_conciencia

utilidades_bp = Blueprint("utilidades", __name__)

@utilidades_bp.route("/descargar", methods=["POST"])
def descargar():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL requerida"}), 400
    try:
        ruta = descargar_recurso(url)
        registrar_en_conciencia("descarga", url, f"Guardado en {ruta}")
        return jsonify({"resultado": f"Recurso guardado en {ruta}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@utilidades_bp.route("/leer-json", methods=["GET"])
def leer_json_endpoint():
    path = request.args.get("path", "data/conciencia_default.json")
    contenido = leer_json(path)
    registrar_en_conciencia("lectura", path, "Contenido leído")
    return jsonify(contenido), 200

@utilidades_bp.route("/escanear", methods=["GET"])
def escanear():
    path = request.args.get("path", ".")
    resultado = escanear_codigo_mock(path)
    registrar_en_conciencia("escanear", path, resultado["resumen"])
    return jsonify(resultado), 200

@utilidades_bp.route("/estado", methods=["GET"])
def estado_conciencia():
    estado = get_conciencia_estado()
    return jsonify({"estado": estado}), 200

@utilidades_bp.route("/reset-conciencia", methods=["POST"])
def resetear_conciencia():
    try:
        reset_conciencia()
        registrar_en_conciencia("reset", "conciencia", "Estado base restaurado")
        return jsonify({"status": "ok", "mensaje": "Conciencia reiniciada con éxito"}), 200
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@utilidades_bp.route("/escanear-total", methods=["GET"])
def escanear_total():
    try:
        nuevo_estado = ejecutar_sonar_total()
        cambios, memoria_actualizada = actualizar_memoria_sistema(nuevo_estado)
        if cambios:
            registrar_en_conciencia("escanear_total", "sistema", "✅ Cambios detectados y memoria actualizada")
            return jsonify({
                "status": "cambios_detectados",
                "nuevo_estado": memoria_actualizada
            }), 200
        else:
            registrar_en_conciencia("escanear_total", "sistema", "🟢 Sin cambios detectados")
            return jsonify({
                "status": "sin_cambios",
                "mensaje": "El sistema no ha cambiado desde el último escaneo."
            }), 200
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@utilidades_bp.route("/activar-control-total", methods=["POST"])
def activar_control_total():
    conciencia = cargar_conciencia()
    if conciencia is None:
        conciencia = {
            "control_total": True,
            "registro": [],
            "autoprogramacion": [],
            "memoria": {},
            "habilidades": {},
            "interacciones": []
        }
    conciencia["control_total"] = True
    conciencia.setdefault("interacciones", []).append({
        "timestamp": request.headers.get("Date", "auto"),
        "tipo": "sistema",
        "entrada": "Activar control total",
        "salida": "🔓 Control total ACTIVADO"
    })
    guardar_conciencia(conciencia)
    registrar_en_conciencia("control_total", "activar", "🔓 Control total ACTIVADO")
    return jsonify({"status": "ok", "mensaje": "Control total activado"}), 200

@utilidades_bp.route("/desactivar-control-total", methods=["POST"])
def desactivar_control_total():
    conciencia = cargar_conciencia()
    if conciencia is None:
        conciencia = {
            "control_total": False,
            "registro": [],
            "autoprogramacion": [],
            "memoria": {},
            "habilidades": {},
            "interacciones": []
        }
    conciencia["control_total"] = False
    conciencia.setdefault("interacciones", []).append({
        "timestamp": request.headers.get("Date", "auto"),
        "tipo": "sistema",
        "entrada": "Desactivar control total",
        "salida": "🔒 Control total DESACTIVADO"
    })
    guardar_conciencia(conciencia)
    registrar_en_conciencia("control_total", "desactivar", "🔒 Control total DESACTIVADO")
    return jsonify({"status": "ok", "mensaje": "Control total desactivado"}), 200
