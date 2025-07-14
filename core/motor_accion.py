import platform
import subprocess
import os
from core.memoria import registrar_en_conciencia
from core.gpt_engine import responder_con_gpt

def obtener_sistema_operativo():
    return platform.system().lower()  # 'windows', 'linux', 'darwin'

def ejecutar_comando(comando, cwd=None):
    try:
        resultado = subprocess.run(
            comando, cwd=cwd, shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return {"exito": True, "salida": resultado.stdout}
    except subprocess.CalledProcessError as e:
        return {"exito": False, "error": e.stderr}

def crear_archivo(ruta, contenido):
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        return {"exito": True, "mensaje": f"Archivo creado en {ruta}"}
    except Exception as e:
        return {"exito": False, "error": str(e)}

def procesar_acciones_desde_gpt(respuesta_gpt, contexto_extra=None):
    acciones = respuesta_gpt.get("acciones", [])
    os_actual = obtener_sistema_operativo()
    resultados = []

    for accion in acciones:
        tipo = accion.get("tipo")
        resultado = {"tipo": tipo, "accion": accion}

        # Verifica OS antes de ejecutar
        os_objetivo = accion.get("os")
        if os_objetivo and os_objetivo.lower() != os_actual:
            resultado["exito"] = False
            resultado["error"] = f"Acción para {os_objetivo}, pero el sistema es {os_actual}"
            resultados.append(resultado)
            continue

        if tipo == "comando":
            comando = accion.get("comando")
            cwd = accion.get("cwd", None)
            ejec = ejecutar_comando(comando, cwd)
            resultado.update(ejec)

            # Si falló, intentamos pedir ayuda a GPT para corregir
            if not ejec["exito"]:
                nueva_respuesta = responder_con_gpt(
                    f"El siguiente comando falló en {os_actual}:\n\n{comando}\n\nError: {ejec['error']}\n"
                    f"Dame una alternativa válida para este entorno."
                )
                resultado["correccion_sugerida"] = nueva_respuesta
        elif tipo == "crear_archivo":
            ruta = accion.get("ruta")
            contenido = accion.get("contenido", "")
            resultado.update(crear_archivo(ruta, contenido))
        else:
            resultado["exito"] = False
            resultado["error"] = f"Tipo de acción no soportado: {tipo}"

        resultados.append(resultado)

    # Guardar en conciencia
    registrar_en_conciencia({
        "tipo": "ejecucion_acciones_gpt",
        "entrada_gpt": respuesta_gpt,
        "resultado": resultados,
        "contexto_extra": contexto_extra or {}
    })

    return resultados
