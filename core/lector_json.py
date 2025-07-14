import json
import os

def leer_json(path):
    if not os.path.exists(path):
        return {"error": "Archivo no encontrado"}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)