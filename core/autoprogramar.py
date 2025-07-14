import os
import re
import hashlib
from datetime import datetime
from core.evolucion import cargar_conciencia, guardar_conciencia
from core.ejecutar_comando import ejecutar_comando

RUTA_AUTOCODIGO = "data/codigo_autogenerado.py"

# ============================
# Utilidades de archivos
# ============================
def escanear_archivos_con_hash(base_path="."):
    archivos = {}
    for root, dirs, files in os.walk(base_path):
        for nombre in files:
            ruta_abs = os.path.join(root, nombre)
            try:
                with open(ruta_abs, "rb") as f:
                    contenido = f.read()
                    hash_val = hashlib.sha256(contenido).hexdigest()
                    try:
                        contenido_str = contenido.decode("utf-8")
                    except Exception:
                        contenido_str = "(binario o no decodificable)"
                archivos[os.path.relpath(ruta_abs, base_path)] = {
                    "hash": hash_val,
                    "contenido": contenido_str
                }
            except:
                continue  # omitimos archivos inaccesibles
    return archivos

# ============================
# Detección de código
# ============================
def detectar_codigo_en_texto(texto):
    if "```python" in texto and "```" in texto:
        return texto.split("```python")[1].split("```")[0].strip()
    match = re.search(r'(?:^|\n)([a-zA-Z_][\w\s=().,+\-*/\[\]{}:]+)', texto)
    if match:
        return match.group(1).strip()
    return None

# ============================
# Guardar código generado
# ============================
def guardar_codigo_autogenerado(codigo, fuente="IA"):
    os.makedirs(os.path.dirname(RUTA_AUTOCODIGO), exist_ok=True)
    timestamp = datetime.now().isoformat()
    contenido = f"# Código generado por {fuente} el {timestamp}\n{codigo}\n\n"
    with open(RUTA_AUTOCODIGO, "a", encoding="utf-8") as f:
        f.write(contenido)
    return RUTA_AUTOCODIGO

# ============================
# Ejecutar código Python
# ============================
def ejecutar_codigo(codigo):
    try:
        exec(codigo, globals())
        return True, "✅ Código ejecutado correctamente."
    except Exception as e:
        return False, f"❌ Error al ejecutar código: {e}"

# ============================
# Registrar autoprogramación
# ============================
def registrar_autoprogramacion(entrada, salida, ejecutado=False, mensaje_ejecucion="", cambios_archivos=None):
    conciencia = cargar_conciencia()
    conciencia.setdefault("registro", [])
    conciencia.setdefault("autoprogramacion", [])

    codigo = detectar_codigo_en_texto(salida)
    if not codigo:
        return False

    ruta = guardar_codigo_autogenerado(codigo)

    entrada_registro = {
        "timestamp": datetime.now().isoformat(),
        "entrada": entrada,
        "salida": salida,
        "ruta_codigo": ruta,
        "ejecutado": ejecutado,
        "mensaje_ejecucion": mensaje_ejecucion,
    }

    if cambios_archivos:
        entrada_registro["cambios_archivos"] = cambios_archivos

    conciencia["autoprogramacion"].append(entrada_registro)

    conciencia["registro"].append({
        "timestamp": datetime.now().isoformat(),
        "entrada": entrada,
        "salida": f"Autoprogramación guardada en {ruta}. {mensaje_ejecucion}",
        "detalle": cambios_archivos or {}
    })

    guardar_conciencia(conciencia)
    return True

# ============================
# Función principal
# ============================
def intentar_autoprogramar(entrada, salida):
    codigo = detectar_codigo_en_texto(salida)
    if not codigo:
        return False, "No se detectó código en la respuesta."

    antes = escanear_archivos_con_hash(".")
    ejecutado, mensaje = ejecutar_codigo(codigo)
    despues = escanear_archivos_con_hash(".")

    cambios = {}
    for ruta, props in despues.items():
        if ruta not in antes:
            cambios[ruta] = {"tipo": "nuevo", "contenido": props["contenido"]}
        elif antes[ruta]["hash"] != props["hash"]:
            cambios[ruta] = {
                "tipo": "modificado",
                "contenido_anterior": antes[ruta]["contenido"],
                "contenido_nuevo": props["contenido"]
            }

    registrado = registrar_autoprogramacion(entrada, salida, ejecutado, mensaje, cambios)

    if not registrado:
        return False, "No se pudo registrar la autoprogramación."

    return True, mensaje
