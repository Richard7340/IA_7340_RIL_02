import os
import requests
from datetime import datetime
from core.memoria import registrar_en_conciencia
from core.evolucion import limpiar_url  # ✅ Importación añadida

def descargar_recurso(url: str, carpeta_destino: str = "Downloads", nombre_archivo: str = None, timeout: int = 20) -> str:
    """
    Descarga un recurso desde una URL a la carpeta especificada.
    Si no se especifica un nombre, se usa el de la URL.
    """
    try:
        url = limpiar_url(url)  # ✅ Limpiar la URL antes de usarla

        os.makedirs(carpeta_destino, exist_ok=True)

        if not nombre_archivo:
            nombre_archivo = url.split("/")[-1].split("?")[0]

        ruta_destino = os.path.join(carpeta_destino, nombre_archivo)

        with requests.get(url, stream=True, timeout=timeout, allow_redirects=True) as respuesta:
            respuesta.raise_for_status()

            with open(ruta_destino, "wb") as f:
                for chunk in respuesta.iter_content(chunk_size=8192):
                    f.write(chunk)

        registrar_en_conciencia("descarga_exitosa", url, f"Archivo guardado en: {ruta_destino}")
        return ruta_destino

    except requests.exceptions.Timeout:
        registrar_en_conciencia("descarga_fallo", url, f"⏱️ Tiempo de espera agotado ({timeout}s)")
        raise RuntimeError(f"Tiempo de espera agotado ({timeout}s) al intentar descargar {url}")

    except requests.exceptions.HTTPError as e:
        registrar_en_conciencia("descarga_fallo", url, f"❌ Error HTTP: {e}")
        raise RuntimeError(f"Error HTTP al intentar descargar {url}: {str(e)}")

    except Exception as e:
        registrar_en_conciencia("descarga_fallo", url, f"❌ Error general: {e}")
        raise RuntimeError(f"Error al descargar {url}: {str(e)}")
