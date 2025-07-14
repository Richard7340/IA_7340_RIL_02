import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Blueprint, request, jsonify
from core.embedding_memoria import buscar_por_embedding

embedding_bp = Blueprint("embedding", __name__)

@embedding_bp.route("/buscar-semanticamente", methods=["POST"])
def buscar_semanticamente():
    data = request.get_json()
    texto = data.get("texto", "").strip()

    if not texto:
        return jsonify({"error": "❌ No se proporcionó texto para buscar."}), 400

    resultado = buscar_por_embedding(texto)

    if resultado:
        return jsonify({"resultado": resultado}), 200
    else:
        return jsonify({"resultado": "🤷 No se encontraron respuestas similares."}), 200
