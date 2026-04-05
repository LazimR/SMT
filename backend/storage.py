import json
from pathlib import Path
from typing import Dict

import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage" / "leituras"


def _status_color(status: str) -> tuple[int, int, int]:
    status_normalizado = (status or "").strip().lower()
    if "crít" in status_normalizado or "critico" in status_normalizado:
        return (61, 61, 255)
    if "alerta" in status_normalizado:
        return (107, 203, 255)
    return (102, 230, 0)


def _render_leitura_image(payload: Dict) -> np.ndarray:
    width = 960
    height = 540
    image = np.full((height, width, 3), (18, 22, 30), dtype=np.uint8)

    header_color = _status_color(payload.get("status_logico", ""))

    cv2.rectangle(image, (28, 28), (width - 28, height - 28), (42, 46, 62), 2)
    cv2.rectangle(image, (28, 28), (width - 28, 110), header_color, -1)

    cv2.putText(
        image,
        "LEITURA PROCESSADA",
        (52, 78),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    lines = [
        f"ID: {payload.get('id', '-')}",
        f"Sensor: {payload.get('sensor_id', '-')}",
        f"Temperatura: {payload.get('temperatura', 0.0):+.2f} C",
        f"Status: {payload.get('status_logico', '-')}",
        f"Timestamp: {payload.get('timestamp', '-')}",
        f"Processado em: {payload.get('processado_em', '-')}",
    ]

    y = 165
    for line in lines:
        cv2.putText(
            image,
            line,
            (58, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.82,
            (232, 236, 244),
            2,
            cv2.LINE_AA,
        )
        y += 54

    cv2.circle(image, (860, 190), 68, header_color, -1)
    cv2.circle(image, (860, 190), 40, (18, 22, 30), -1)

    return image


def save_leitura_files(payload: Dict) -> Dict[str, str]:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    leitura_id = payload["id"]
    json_path = STORAGE_DIR / f"{leitura_id}.json"
    png_path = STORAGE_DIR / f"{leitura_id}.png"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    leitura_image = _render_leitura_image(payload)
    if not cv2.imwrite(str(png_path), leitura_image):
        raise RuntimeError("Falha ao salvar a imagem PNG da leitura.")

    return {
        "json_file": str(json_path),
        "png_file": str(png_path),
    }
