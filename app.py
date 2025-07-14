from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from routes.sistema import sistema_bp
from routes.utilidades import utilidades_bp
from routes.auth import auth_bp
from routes.conversar import conversar_bp
import os
from datetime import datetime

# Core imports
from core.autoprogramar import registrar_autoprogramacion
from core.Sonar_total_arch import escanear_sistema_y_detectar_cambios  # ← Corrección real del import
from core.evolucion import actualizar_memoria_sistema, guardar_conciencia, cargar_conciencia

# Crear instancia de la app Flask
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "secret!")

# CORS y WebSockets
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Registrar rutas (blueprints)
app.register_blueprint(sistema_bp)
app.register_blueprint(utilidades_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(conversar_bp)

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

# WebSocket para logs
@socketio.on("log")
def handle_log(data):
    print(f"[LOG EVENT]: {data['message']}")

# Inicio del servidor
if __name__ == "__main__":
    print("Iniciando backend IA Consciente...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
