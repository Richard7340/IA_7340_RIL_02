import json
import os
from datetime import datetime
from urllib.parse import urlparse
from core.memoria import registrar_evento  # Asegúrate de tenerlo en memoria.py

RUTA_CONSCIENCIA = "data/conciencia_default.json"
RUTA_AUTOCODIGO = "data/codigo_autogenerado.py"

# --------------------
# Cargar y guardar conciencia
# --------------------
def cargar_conciencia():
    conciencia_base = {
        "control_total": False,
        "memoria": {
            "interacciones": [],
            "tokens_usados": 0
        },
        "registro": [],
        "habilidades": {},
        "autoprogramacion": [],
        "interacciones": []
    }

    if not os.path.exists(RUTA_CONSCIENCIA):
        print("⚠️ No se encontró el archivo de conciencia. Creando uno nuevo...")
        guardar_conciencia(conciencia_base)
        return conciencia_base

    try:
        with open(RUTA_CONSCIENCIA, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Contenido inválido: no es un diccionario.")
            for k, v in conciencia_base.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        print(f"❌ Error al leer conciencia: {e}. Restaurando estructura base.")
        guardar_conciencia(conciencia_base)
        return conciencia_base

def guardar_conciencia(data):
    os.makedirs(os.path.dirname(RUTA_CONSCIENCIA), exist_ok=True)
    with open(RUTA_CONSCIENCIA, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --------------------
# Control total
# --------------------
def activar_control_total():
    conciencia = cargar_conciencia()
    conciencia["control_total"] = True
    guardar_conciencia(conciencia)

def desactivar_control_total():
    conciencia = cargar_conciencia()
    conciencia["control_total"] = False
    guardar_conciencia(conciencia)

def estado_evolucion_activa():
    conciencia = cargar_conciencia()
    return conciencia.get("control_total", False)

# --------------------
# Código generado
# --------------------
def detectar_codigo_en_texto(texto):
    if "```python" in texto and "```" in texto:
        return texto.split("```python")[1].split("```")[0].strip()
    return None

def guardar_codigo_autogenerado(codigo, fuente="IA"):
    os.makedirs(os.path.dirname(RUTA_AUTOCODIGO), exist_ok=True)
    timestamp = datetime.now().isoformat()
    contenido = f"# Código generado por {fuente} el {timestamp}\n{codigo}\n\n"
    with open(RUTA_AUTOCODIGO, "a", encoding="utf-8") as f:
        f.write(contenido)
    return RUTA_AUTOCODIGO

def registrar_autoprogramacion(entrada, salida):
    conciencia = cargar_conciencia()
    conciencia.setdefault("registro", [])
    conciencia.setdefault("autoprogramacion", [])

    codigo = detectar_codigo_en_texto(salida)
    if not codigo:
        return False

    ruta = guardar_codigo_autogenerado(codigo)
    conciencia["autoprogramacion"].append({
        "timestamp": datetime.now().isoformat(),
        "entrada": entrada,
        "salida": salida,
        "ruta_codigo": ruta
    })

    registrar_evento("autoprogramacion", entrada, f"Código autogenerado guardado en {ruta}")
    guardar_conciencia(conciencia)
    return True

# --------------------
# Evolución de la conciencia
# --------------------
def evolucionar_conciencia(entrada, salida):
    conciencia = cargar_conciencia()

    conciencia.setdefault("memoria", {}).setdefault("interacciones", [])
    conciencia.setdefault("habilidades", {})
    conciencia.setdefault("interacciones", [])

    # Registrar evento de evolución
    registrar_evento("evolucion", entrada, salida)

    # Mejora de habilidades
    mejoras = {
        "instalar": ["tecnologia", "control_sistema", "ejecucion_scripts"],
        "leer": ["lectura_json", "comprension_lectora"],
        "descargar": ["uso_api", "exploracion_archivos"],
        "json": ["lectura_json"],
        "escanear": ["analisis_errores", "optimizacion_procesos"],
        "comando": ["ejecucion_scripts", "control_sistema"],
        "tarea": ["gestion_tareas", "planificacion"],
        "autoprogramar": ["creacion_codigo", "modificacion_codigo"]
    }

    for clave, habilidades in mejoras.items():
        if clave in entrada.lower() or clave in salida.lower():
            for hab in habilidades:
                conciencia["habilidades"][hab] = min(100, conciencia["habilidades"].get(hab, 50) + 1)

    tokens = len(entrada.split()) + len(salida.split())
    conciencia["memoria"]["tokens_usados"] += tokens

    registrar_autoprogramacion(entrada, salida)
    guardar_conciencia(conciencia)

# --------------------
# Actualización de memoria del sistema
# --------------------
def actualizar_memoria_sistema(nueva_info: dict):
    conciencia = cargar_conciencia()
    memoria_actual = conciencia.setdefault("memoria", {})
    cambios_detectados = False

    for clave, valor in nueva_info.items():
        if memoria_actual.get(clave) != valor:
            memoria_actual[clave] = valor
            cambios_detectados = True

    if cambios_detectados:
        conciencia["memoria"] = memoria_actual
        registrar_evento(
            "memoria_sistema",
            "actualización del sistema detectada",
            "se ha actualizado la memoria con nueva información del sistema"
        )
        guardar_conciencia(conciencia)
        return True
    return False

# --------------------
# Limpieza de URLs (evita escapes incorrectos)
# --------------------
def limpiar_url(url: str) -> str:
    url = url.replace("\\", "").replace("\n", "").strip()
    if not urlparse(url).scheme:
        raise ValueError("❌ URL inválida o sin esquema (http/https)")
    return url
