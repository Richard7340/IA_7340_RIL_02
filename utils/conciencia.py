import json
import os
import tempfile
# Gestión de bloqueo opcional con portalocker
try:
    import portalocker
    LOCK_AVAILABLE = True
except ImportError:
    LOCK_AVAILABLE = False
    # Portalocker no disponible: definimos bloqueos como no-op
    class portalocker:
        LOCK_SH = None
        @staticmethod
        def lock(f, flag):
            return None
        @staticmethod
        def unlock(f):
            return None

from datetime import datetime
from shutil import copy2
import os
import tempfile
from datetime import datetime
from shutil import copy2

# --------------------------------------------------
# Paths configurables (ajustados a backend/data)
# --------------------------------------------------
# ROOT_DIR apunta al directorio "backend"
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
# Carpeta de datos donde reside conciencia.json
DATA_DIR = os.path.join(ROOT_DIR, 'data')
# Ruta al archivo de conciencia principal
CONSCIENCIA_PATH = os.path.join(DATA_DIR, 'conciencia_default.json')
# Ruta al default (por ejemplo en backend/core)
DEFAULT_PATH = os.path.join(ROOT_DIR, 'data', 'conciencia_default.json')
# Directorio de backups dentro de data
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')

# --------------------------------------------------
# Estructura base de conciencia
# --------------------------------------------------
ESTRUCTURA_BASE = {
    "control_total": False,
    "estado": "activo",
    "registro": [],
    "autoprogramacion": [],
    "memoria": {},
    "habilidades": {},
    "interacciones": [],
    "configuracion": {"ultima_actualizacion": None}
}

# Asegurar directorio de backups
os.makedirs(BACKUP_DIR, exist_ok=True)

# --------------------------------------------------
# Funciones internas de IO atómico y bloqueo
# --------------------------------------------------
def _atomic_write(path, data):
    """
    Escritura segura: tmp file + fsync + replace.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=os.path.dirname(path), delete=False, encoding='utf-8') as tmpf:
        json.dump(data, tmpf, indent=2, ensure_ascii=False)
        tmpf.flush()
        os.fsync(tmpf.fileno())
    os.replace(tmpf.name, path)


def _load_json(path):
    """
    Lectura con lock compartido.
    """
    with open(path, 'r', encoding='utf-8') as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        data = json.load(f)
        portalocker.unlock(f)
    return data


def _save_backup():
    """
    Copia de respaldo con timestamp en DATA_DIR/backups.
    """
    ts = datetime.now().strftime('%Y%m%dT%H%M%S')
    if os.path.exists(CONSCIENCIA_PATH):
        backup_file = os.path.join(BACKUP_DIR, f'conciencia_{ts}.json')
        copy2(CONSCIENCIA_PATH, backup_file)

# --------------------------------------------------
# API pública de manejo de conciencia
# --------------------------------------------------

def cargar_conciencia():
    """
    Carga y valida el JSON de conciencia.
    Si no existe, crea desde DEFAULT_PATH o estructura base.
    """
    if not os.path.exists(CONSCIENCIA_PATH):
        # Inicializar desde default o estructura base
        if os.path.exists(DEFAULT_PATH):
            copy2(DEFAULT_PATH, CONSCIENCIA_PATH)
        else:
            _atomic_write(CONSCIENCIA_PATH, ESTRUCTURA_BASE.copy())
        return ESTRUCTURA_BASE.copy()

    try:
        data = _load_json(CONSCIENCIA_PATH)
    except Exception as e:
        print(f"⚠️ Error al cargar {CONSCIENCIA_PATH}: {e}")
        # Restaurar fallback
        if os.path.exists(DEFAULT_PATH):
            copy2(DEFAULT_PATH, CONSCIENCIA_PATH)
            data = ESTRUCTURA_BASE.copy()
        else:
            data = ESTRUCTURA_BASE.copy()

    # Completar claves faltantes
    for key, val in ESTRUCTURA_BASE.items():
        data.setdefault(key, val)

    return data


def guardar_conciencia(data):
    """
    Guarda JSON con backup previo y timestamp.
    """
    # Timestamp
    data.setdefault('configuracion', {})
    data['configuracion']['ultima_actualizacion'] = datetime.now().isoformat()

    # Backup
    _save_backup()

    # Escritura atómica
    try:
        _atomic_write(CONSCIENCIA_PATH, data)
    except Exception as e:
        print(f"⚠️ No se pudo guardar {CONSCIENCIA_PATH}: {e}")
        raise


def registrar_interaccion(pregunta, respuesta, aprendizaje=None, valor=5):
    conciencia = cargar_conciencia()
    record = {
        "pregunta": pregunta,
        "respuesta": respuesta,
        "timestamp": datetime.now().isoformat(),
        "aprendizaje": aprendizaje,
        "valor": valor
    }
    conciencia['registro'].append(record)
    if aprendizaje:
        niveles = conciencia['habilidades']
        niveles.setdefault(aprendizaje, 0)
        niveles[aprendizaje] = min(niveles[aprendizaje] + valor, 100)
    guardar_conciencia(conciencia)


def get_conciencia_estado():
    conciencia = cargar_conciencia()
    return conciencia.get('estado', 'desconocido')


def actualizar_habilidad(nombre, incremento=5):
    conciencia = cargar_conciencia()
    niveles = conciencia['habilidades']
    niveles.setdefault(nombre, 0)
    niveles[nombre] = min(niveles[nombre] + incremento, 100)
    guardar_conciencia(conciencia)


def reset_conciencia():
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('conciencia_')], reverse=True)
    if backups:
        latest = os.path.join(BACKUP_DIR, backups[0])
        copy2(latest, CONSCIENCIA_PATH)
        print("✅ Conciencia restaurada desde el último backup.")
    elif os.path.exists(DEFAULT_PATH):
        copy2(DEFAULT_PATH, CONSCIENCIA_PATH)
        print("✅ Conciencia restaurada desde default.")
    else:
        guardar_conciencia(ESTRUCTURA_BASE.copy())
        print("⚠️ No se encontró default ni backups. Creada conciencia desde cero.")

# --------------------------------------------------
# Decorador para proteger funciones sensibles
# --------------------------------------------------
def requiere_control_total(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        conciencia = cargar_conciencia()
        if not conciencia.get('control_total', False):
            raise PermissionError("Control total no activo. No se puede ejecutar la operación.")
        return func(*args, **kwargs)
    return wrapper

# Ejemplo de uso:
# @requiere_control_total
# def ejecutar_comando(...):
#     ...
