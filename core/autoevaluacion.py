# core/autoevaluacion.py

from core.ejecutor import ejecutar_accion
from core.gpt_engine import responder_con_gpt
from core.memoria import registrar_en_conciencia
from datetime import datetime

def autoevaluar_y_reintentar(accion_original, resultado_fallido, entrada_usuario):
    if resultado_fallido.get("exito", True):
        return []  # No hubo fallo, no se necesita reintento

    mensaje_error = resultado_fallido.get("error", "Sin descripción de error")
    prompt_reintento = (
        "Esta acción falló:\n"
        f"Acción original: {accion_original}\n"
        f"Error: {mensaje_error}\n\n"
        "¿Qué debería hacer ahora para lograr el objetivo del usuario?\n"
        f"Instrucción original del usuario: \"{entrada_usuario}\""
    )

    nueva_respuesta = responder_con_gpt(prompt_reintento)

    if isinstance(nueva_respuesta, dict) and "acciones" in nueva_respuesta:
        nuevas_acciones = nueva_respuesta["acciones"]
        resultados_reintento = []

        for nueva_accion in nuevas_acciones:
            resultado_nuevo = ejecutar_accion(nueva_accion)

            registrar_en_conciencia(
                tipo="reintento_accion",
                entrada={
                    "accion_fallida": accion_original,
                    "nueva_accion": nueva_accion
                },
                salida=resultado_nuevo
            )

            if resultado_nuevo.get("exito"):
                registrar_en_conciencia(
                    tipo="mejora_aplicada",
                    entrada=nueva_accion,
                    salida="✅ Solución alternativa aplicada con éxito"
                )

            resultados_reintento.append({
                "accion": nueva_accion,
                "resultado": resultado_nuevo
            })

        return resultados_reintento

    else:
        registrar_en_conciencia(
            tipo="reintento_fallido",
            entrada=prompt_reintento,
            salida=nueva_respuesta
        )
        return []

