from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import jwt
import datetime
import os

from core.evolucion import activar_control_total, desactivar_control_total, evolucionar_conciencia
from core.memoria import registrar_en_conciencia

auth_bp = Blueprint("auth", __name__)

# Base de datos simulada
usuarios = {
    "admin": {"clave": "1234", "rol": "superadmin"},
    "usuario": {"clave": "abcd", "rol": "lector"}
}

SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-por-defecto")

# =========================
# RUTA: LOGIN
# =========================
@auth_bp.route("/login", methods=["POST", "OPTIONS"])
@cross_origin()
def login():
    data = request.get_json()
    usuario = data.get("usuario")
    clave = data.get("clave")

    if not usuario or not clave:
        return jsonify({"error": "Faltan credenciales"}), 400

    user = usuarios.get(usuario)
    if user and user["clave"] == clave:
        token = jwt.encode({
            "usuario": usuario,
            "rol": user["rol"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, SECRET_KEY, algorithm="HS256")

        registrar_en_conciencia("login_exitoso", usuario, "Sesión iniciada correctamente")
        evolucionar_conciencia("login", f"{usuario} autenticado")

        return jsonify({"token": token})

    registrar_en_conciencia("login_fallido", usuario, "Credenciales inválidas")
    return jsonify({"error": "Credenciales inválidas"}), 401

# =========================
# RUTA: VERIFICAR TOKEN
# =========================
@auth_bp.route("/verificar-token", methods=["POST", "OPTIONS"])
@cross_origin()
def verificar_token():
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token requerido"}), 400

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        registrar_en_conciencia("token_verificado", decoded["usuario"], "Token válido")
        return jsonify({
            "valido": True,
            "usuario": decoded["usuario"],
            "rol": decoded["rol"]
        })

    except jwt.ExpiredSignatureError:
        registrar_en_conciencia("token_expirado", "", "El token ha expirado")
        return jsonify({"valido": False, "error": "Token expirado"}), 401

    except jwt.InvalidTokenError:
        registrar_en_conciencia("token_invalido", "", "El token es inválido")
        return jsonify({"valido": False, "error": "Token inválido"}), 401

# =========================
# RUTA: ACTIVAR CONTROL TOTAL
# =========================
@auth_bp.route("/activar-control-total", methods=["POST", "OPTIONS"])
@cross_origin()
def activar():
    try:
        activar_control_total()
        registrar_en_conciencia("control_total", "activar", "Autonomía activada")
        evolucionar_conciencia("activar control total", "control_total = True")
        return jsonify({"status": "ok", "mensaje": "Control total activado"})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

# =========================
# RUTA: DESACTIVAR CONTROL TOTAL
# =========================
@auth_bp.route("/desactivar-control-total", methods=["POST", "OPTIONS"])
@cross_origin()
def desactivar():
    try:
        desactivar_control_total()
        registrar_en_conciencia("control_total", "desactivar", "Autonomía desactivada")
        evolucionar_conciencia("desactivar control total", "control_total = False")
        return jsonify({"status": "ok", "mensaje": "Control total desactivado"})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500
