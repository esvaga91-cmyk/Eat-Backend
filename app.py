# v7 - Corregido, Seguro y Compatible con Groq Vision
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import requests
import os
import json

app = Flask(__name__)
CORS(app)

# Clave desde variables de entorno
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@app.route("/analizar", methods=["POST"])
def analizar():
    print("---- NUEVA PETICIÓN RECIBIDA ----")

    try:
        # 1. Validar clave
        if not GROQ_API_KEY:
            return jsonify({"error": "Falta la API Key en el servidor"}), 500

        # 2. Validar imagen
        if "imagen" not in request.files:
            return jsonify({"error": "No se envió ninguna imagen"}), 400

        imagen = request.files["imagen"]
        if imagen.filename == "":
            return jsonify({"error": "Archivo de imagen no válido"}), 400

        # Leer bytes y convertir a base64
        imagen_bytes = imagen.read()
        imagen_b64 = base64.b64encode(imagen_bytes).decode("utf-8")

        # 3. Petición a Groq
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        # Modelo CORRECTO y ACTUAL
        modelo = "llama-3.2-vision-preview"

        prompt = """
        Eres Eat & Burn, un analizador experto en comida y nutrición.
        1. Determina si la imagen contiene COMIDA o BEBIDA.
        2. Si NO contiene: Responde un JSON con "es_comida": false y un "mensaje".
        3. Si SÍ contiene: Responde SOLO con un JSON con este formato:
        {
          "es_comida": true,
          "descripcion": "...",
          "comida_detectada": "...",
          "calorias_estimadas": 0,
          "macros": {"proteinas": "", "carbohidratos": "", "grasas": "", "azucar": "", "fibra": ""},
          "tabla_ejercicios": "TARJETA ESTILO B"
        }
        """

        data = {
            "model": modelo,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{imagen_b64}"
                        }
                    ]
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        # 4. Llamada a Groq con timeout
        try:
            respuesta = requests.post(url, headers=headers, json=data, timeout=60)
            respuesta.raise_for_status()
        except requests.exceptions.Timeout:
            return jsonify({"error": "La IA tardó demasiado en responder. Prueba con una imagen más pequeña."}), 504
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Error en la API de Groq: {str(e)}"}), 502

        resultado = respuesta.json()

        # 5. Extraer JSON limpio
        if "choices" not in resultado:
            return jsonify({"error": "Respuesta inesperada de la IA", "detalles": resultado}), 500

        contenido = resultado["choices"][0]["message"]["content"]

        try:
            return jsonify(json.loads(contenido))
        except:
            if "```json" in contenido:
                contenido = contenido.split("```json")[1].split("```")[0].strip()
            return jsonify(json.loads(contenido))

    except Exception as e:
        print(f"ERROR CRÍTICO: {str(e)}")
        return jsonify({"error": "Error interno del servidor", "info": str(e)}), 500


@app.route("/checkkey", methods=["GET"])
def checkkey():
    return jsonify({
        "status": "OK" if GROQ_API_KEY else "ERROR",
        "configurada": bool(GROQ_API_KEY)
    })


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "OK", "app": "Eat & Burn API"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
