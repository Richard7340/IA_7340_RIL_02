from core.evolucion import cargar_conciencia, guardar_conciencia
from datetime import datetime
import uuid

def registrar_evento(tipo, entrada, salida, nivel="info"):
    conciencia = cargar_conciencia()
    evento = {
        "id": str(uuid.uuid4()),
        "tipo": tipo,
        "entrada": entrada,
        "salida": salida,
        "nivel": nivel,
        "timestamp": datetime.utcnow().isoformat(),
        "peso_utilidad": 1.0
    }
    conciencia.setdefault("eventos", []).append(evento)
    guardar_conciencia(conciencia)

def buscar_en_conciencia(mensaje):
    conciencia = cargar_conciencia()
    resultados = []
    for item in conciencia.get("memoria", []):
        if mensaje.lower() in str(item.get("entrada", "")).lower():
            resultados.append(item)
    return resultados

def actualizar_peso_fragmentos_memoria(fragmentos, exito=True):
    conciencia = cargar_conciencia()
    memoria = conciencia.get("memoria", [])
    ids_actualizados = set()

    for frag in fragmentos:
        frag_id = frag.get("id")
        if not frag_id:
            continue
        for registro in memoria:
            if registro.get("id") == frag_id:
                peso_actual = registro.get("peso_utilidad", 1.0)
                if exito:
                    nuevo_peso = min(peso_actual + 0.3, 5.0)
                else:
                    nuevo_peso = max(peso_actual - 0.3, 0.1)
                registro["peso_utilidad"] = round(nuevo_peso, 2)
                ids_actualizados.add(frag_id)
                break

    if ids_actualizados:
        guardar_conciencia(conciencia)

def limpiar_memoria_por_peso(umbral_minimo=0.2):
    conciencia = cargar_conciencia()
    memoria = conciencia.get("memoria", [])
    memoria_filtrada = [m for m in memoria if m.get("peso_utilidad", 1.0) >= umbral_minimo]
    if len(memoria_filtrada) < len(memoria):
        conciencia["memoria"] = memoria_filtrada
        guardar_conciencia(conciencia)
def registrar_en_conciencia(tipo, entrada=None, salida=None, nivel="info"):
    """
    Alias a registrar_evento para compatibilidad con autoevaluacion.py.
    """
    return registrar_evento(tipo, entrada, salida, nivel)
