def escanear_codigo_mock(path="."):
    return {
        "proyecto": path,
        "errores": 2,
        "warnings": 5,
        "criticidad": "media",
        "resumen": "Análisis simulado. Integrar SonarQube real si se desea."
    }