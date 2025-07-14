from flask import Blueprint, request, jsonify
from core import sistema

sistema_bp = Blueprint("sistema", __name__)

@sistema_bp.route("/estado-control", methods=["GET"])
def estado_control():
    return jsonify(sistema.estado_control_total())

@sistema_bp.route("/activar-control", methods=["POST"])
def activar_control():
    return jsonify(sistema.activar_control_total())

@sistema_bp.route("/desactivar-control", methods=["POST"])
def desactivar_control():
    return jsonify(sistema.desactivar_control_total())

@sistema_bp.route("/leer-conciencia", methods=["GET"])
def leer_conciencia():
    return jsonify({"conciencia": sistema.leer_conciencia_json()})

@sistema_bp.route("/listar-archivos", methods=["POST"])
def listar_archivos():
    data = request.get_json()
    ruta = data.get("ruta", ".")
    return jsonify({"archivos": sistema.listar_archivos_en_directorio(ruta)})

@sistema_bp.route("/sonar-total", methods=["POST"])
def sonar_total():
    resultado = sistema.ejecutar_sonar_total()
    return jsonify({"resultado": resultado})

@sistema_bp.route("/ejecutar", methods=["POST"])
def ejecutar_comando():
    data = request.get_json()
    cmd = data.get("comando", "").strip()
    if not cmd:
        return jsonify({"error": "❌ Comando vacío"}), 400
    resultado = sistema.ejecutar(cmd)
    return jsonify({"resultado": resultado}), 200
