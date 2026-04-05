from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from flask import Flask, jsonify, request

from database import get_leitura_by_id, init_db, insert_leitura
from rules import classify_temperature
from storage import save_leitura_files

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health() -> Any:
    return jsonify({"status": "ok"}), 200


@app.route("/leitura", methods=["POST"])
def receber_leitura() -> Any:
    if not request.is_json:
        return jsonify({"erro": "Corpo da requisição deve ser JSON."}), 400

    payload = request.get_json(silent=True) or {}
    validacao = _validate_payload(payload)
    if validacao is not None:
        return jsonify({"erro": validacao}), 400

    leitura_id = payload["id"]
    sensor_id = payload["sensor_id"].strip()
    temperatura = float(payload["temperatura"])
    timestamp = payload["timestamp"].strip()

    existente = get_leitura_by_id(leitura_id)
    if existente is not None:
        return jsonify(
            {
                "id": existente["id"],
                "sensor_id": existente["sensor_id"],
                "temperatura": existente["temperatura"],
                "status_logico": existente["status_logico"],
                "timestamp": existente["timestamp"],
                "duplicado": True,
                "mensagem": "UUID já processado. Sem nova gravação.",
            }
        ), 200

    status_logico = classify_temperature(temperatura)
    processado_em = datetime.now().isoformat()

    insert_leitura(
        leitura_id=leitura_id,
        sensor_id=sensor_id,
        temperatura=temperatura,
        status_logico=status_logico,
        timestamp=timestamp,
    )

    arquivos = save_leitura_files(
        {
            "id": leitura_id,
            "sensor_id": sensor_id,
            "temperatura": temperatura,
            "status_logico": status_logico,
            "timestamp": timestamp,
            "processado_em": processado_em,
        }
    )

    return jsonify(
        {
            "id": leitura_id,
            "sensor_id": sensor_id,
            "temperatura": temperatura,
            "status_logico": status_logico,
            "timestamp": timestamp,
            "processado_em": processado_em,
            "duplicado": False,
            "mensagem": "Leitura recebida, processada e persistida.",
            "arquivos": arquivos,
        }
    ), 201


def _validate_payload(payload: Dict[str, Any]) -> str | None:
    required_fields = ["id", "sensor_id", "temperatura", "timestamp"]
    for field in required_fields:
        if field not in payload:
            return f"Campo obrigatório ausente: {field}"

    leitura_id = str(payload["id"]).strip()
    sensor_id = str(payload["sensor_id"]).strip()
    timestamp = str(payload["timestamp"]).strip()

    if not leitura_id:
        return "Campo id não pode ser vazio."

    try:
        UUID(leitura_id)
    except ValueError:
        return "Campo id deve ser um UUID válido."

    if not sensor_id:
        return "Campo sensor_id não pode ser vazio."

    try:
        float(payload["temperatura"])
    except (TypeError, ValueError):
        return "Campo temperatura deve ser numérico."

    if not timestamp:
        return "Campo timestamp não pode ser vazio."

    try:
        datetime.fromisoformat(timestamp)
    except ValueError:
        return "Campo timestamp deve estar em formato ISO 8601."

    return None


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
