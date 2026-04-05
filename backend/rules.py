def classify_temperature(temperatura: float) -> str:
    if temperatura > 15:
        return "Crítico"
    if temperatura > 10:
        return "Alerta"
    return "Normal"
