# core/sistema_rutas.py

import os
from core.memoria import registrar_en_conciencia
from core.evolucion import cargar_conciencia, guardar_conciencia

def establecer_ruta_trabajo(nueva_ruta):
    conciencia = cargar_conciencia()
    if not os.path.exists(nueva_ruta):
        return {"exito": False, "mensaje": f"❌ La ruta no existe: {nueva_ruta}"}

    conciencia["memoria"]["cwd_actual"] = nueva_ruta
    guardar_conciencia(conciencia)
    registrar_en_conciencia("ruta_trabajo", nueva_ruta, "Ruta establecida como contexto actual")
    return {"exito": True, "mensaje": f"📂 Ruta de trabajo actualizada a: {nueva_ruta}"}

def obtener_ruta_trabajo():
    conciencia = cargar_conciencia()
    return conciencia.get("memoria", {}).get("cwd_actual", os.getcwd())

def listar_archivos_desde_ruta(ruta=None, limite=50):
    ruta = ruta or obtener_ruta_trabajo()
    if not os.path.exists(ruta):
        return {"exito": False, "mensaje": f"❌ Ruta no encontrada: {ruta}"}

    archivos = []
    for root, _, files in os.walk(ruta):
        for archivo in files:
            archivos.append(os.path.join(root, archivo))
            if len(archivos) >= limite:
                break
        if len(archivos) >= limite:
            break

    return {"exito": True, "archivos": archivos}