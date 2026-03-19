# v2 - Backend Eat & Burn con OpenRouter (Vision estable con fallback)
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import requests
import os
import json

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Modelos en orden de preferencia
MODELOS_VISION = [
    "llava-1.6",
    "deepseek/deepseek-vl-1.3b-chat",
    "qwen/qwen-vl-chat"
]

def llamar_modelo(modelo, prompt, imagen_b64):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": modelo,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{imagen_b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }

    respuesta = requests.post(url, headers=headers, json=data, timeout=60)
    respuesta.raise_for_status()
    return respuesta.json()


@app.route("/analizar", methods=["POST"])
def analizar():
    print("---- NUEVA PETICIÓN RECIBIDA ----")

    try:
        if not OPENROUTER_API_KEY:
            return jsonify({"error": "Falta la API Key de OpenRouter"}), 500

        if "imagen" not in request.files:
            return jsonify({"error": "No se envió ninguna imagen"}), 400

        imagen = request.files["imagen"]
        if imagen.filename == "":
            return jsonify({"error": "Archivo de imagen no válido"}), 400

        imagen_bytes = imagen.read()
        imagen_b64 = base64.b64encode(imagen_bytes).decode("utf-8")

        prompt = """
        Eres Eat & Burn, un analizador experto en comida y nutrición.
        1. Determina si la imagen contiene COMIDA o BEBIDA.
        2. Si NO contiene: responde un JSON con "es_comida": false y "mensaje".
        3. Si SÍ contiene: responde SOLO con un JSON con este formato:
        {
          "es_comida": true,
          "descripcion": "...",
          "comida_detectada": "...",
          "calorias_estimadas": 0,
          "macros": {"proteinas": "", "carbohidratos": "", "grasas": "", "azucar": "", "fibra": ""},
          "tabla_ejercicios": "TARJETA ESTILO B"
        }
        """

        # Intentar modelos en cascada
        for modelo in MODELOS_VISION:
            print(f"Probando modelo: {modelo}")
            try:
                resultado = llamar_modelo(modelo, prompt, imagen_b64)

                if "choices" not in resultado:
                    continue

                contenido = resultado["choices"][0]["message"]["content"]

                try:
                    return jsonify(json.loads(contenido))
                except:
                    if "```json" in contenido:
                        contenido = contenido.split("```json")[1].split("```")[0].strip()
                    return jsonify(json.loads(contenido))

            except Exception as e:
                print(f"Modelo {modelo} falló: {str(e)}")
                continue

        return jsonify({"error": "Ningún modelo pudo procesar la imagen"}), 502

    except Exception as e:
        print(f"ERROR CRÍTICO: {str(e)}")
        return jsonify({"error": "Error interno del servidor", "info": str(e)}), 500


@app.route("/checkkey", methods=["GET"])
def checkkey():
    return jsonify({
        "status": "OK" if OPENROUTER_API_KEY else "ERROR",
        "configurada": bool(OPENROUTER_API_KEY)
    })


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "OK", "app": "Eat & Burn API (OpenRouter)"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
