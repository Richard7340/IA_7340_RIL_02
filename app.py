from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from routes.sistema import sistema_bp
from routes.utilidades import utilidades_bp
from routes.auth import auth_bp
from routes.conversar import conversar_bp
import os
from datetime import datetime
import json  # Añadido para manejar JSON base

# Core imports
from routes.control import control_bp  # si lo pones en routes/control.py
from core.autoprogramar import registrar_autoprogramacion
from core.Sonar_total_arch import escanear_sistema_y_detectar_cambios  # Verifica el nombre del archivo si da error
from core.evolucion import actualizar_memoria_sistema, guardar_conciencia, cargar_conciencia

# Crear instancia de la app Flask
app = Flask(__name__)
app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "secret!")

# CORS y WebSockets
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Registrar rutas (blueprints)
app.register_blueprint(sistema_bp)
app.register_blueprint(utilidades_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(conversar_bp)
app.register_blueprint(control_bp)

# Ruta principal
@app.route("/")
def index():
    return {"status": "✅ Backend activo y funcionando correctamente."}

# Endpoint de escaneo total del sistema
@app.route("/escanear-total", methods=["GET"])
def escanear_total():
    try:
        resultado = escanear_sistema_y_detectar_cambios()
        cambios_detectados = resultado.get("resumen", {})

        conciencia = cargar_conciencia()
        conciencia.setdefault("registro", []).append({
            "timestamp": datetime.now().isoformat(),
            "tipo": "sonar_total",
            "cambios": cambios_detectados
        })
        guardar_conciencia(conciencia)

        return jsonify({
            "estado": "✅ Escaneo completado",
            "cambios": cambios_detectados,
            "reporte": resultado
        }), 200

    except Exception as e:
        return jsonify({"error": f"❌ Error en escaneo total: {str(e)}"}), 500

# Endpoint para activar/desactivar control total (POST, flippea el estado)
@app.route('/activar-control-total', methods=['POST'])
def activar_control_total():
    try:
        conciencia = cargar_conciencia()
        current = conciencia.get('control_total', False)
        conciencia['control_total'] = not current  # Flip: activa si estaba off, y viceversa
        guardar_conciencia(conciencia)
        status = "activado" if conciencia['control_total'] else "desactivado"
        print(f"Control total {status} exitosamente.")  # Log para depuración
        return jsonify({"mensaje": f"Control total {status}", "control_total": conciencia['control_total']}), 200
    except Exception as e:
        print(f"Error al flippear control total: {str(e)}")  # Log error
        return jsonify({"error": f"❌ Error al cambiar control total: {str(e)}"}), 500

# Endpoint para obtener el estado de control total (GET)
@app.route('/get-control-total', methods=['GET'])
def get_control_total():
    try:
        conciencia = cargar_conciencia()
        # Si no existe el JSON, crea base con control_total: false
        if not conciencia:
            conciencia = {"control_total": False, "eventos": [], "memoria": []}  # Estructura base
            guardar_conciencia(conciencia)
            print("conciencia_default.json creado con base: control_total=False")
        status = conciencia.get("control_total", False)
        print(f"Estado control total consultado: {status}")  # Log para depuración
        return jsonify({"control_total": status}), 200
    except Exception as e:
        print(f"Error al obtener control total: {str(e)}")  # Log error
        return jsonify({"error": f"❌ Error al obtener control total: {str(e)}"}), 500

# WebSocket para logs
@socketio.on("log")
def handle_log(data):
    print(f"[LOG EVENT]: {data['message']}")

# Inicio del servidor
if __name__ == "__main__":
    print("Iniciando backend IA Consciente...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
