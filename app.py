# v5
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import requests
import os
import json

app = Flask(__name__)
CORS(app)

# Clave de Groq desde variables de entorno (Railway)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@app.route("/analizar", methods=["POST"])
def analizar():

    print("---- NUEVA PETICIÓN ----")
    print("FILES:", request.files)
    print("FORM:", request.form)
    print("CLAVE:", GROQ_API_KEY)

    try:
        # Validar imagen
        if "imagen" not in request.files:
            return jsonify({"error": "No se envió ninguna imagen"}), 400

        imagen = request.files["imagen"]
        imagen_bytes = imagen.read()
        imagen_b64 = base64.b64encode(imagen_bytes).decode("utf-8")

        # Endpoint de Groq
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        # Prompt profesional
        prompt = """
Eres Eat & Burn, un analizador experto en comida y nutrición.

1. Primero, determina si la imagen contiene COMIDA o BEBIDA.
2. Si NO contiene comida ni bebida:
   Responde SOLO con:
   {
     "es_comida": false,
     "mensaje": "Parece que la imagen no muestra comida ni bebida. Eat & Burn solo analiza alimentos."
   }

3. Si SÍ contiene comida o bebida:
   Responde SOLO con un JSON con este formato EXACTO:

{
  "es_comida": true,
  "descripcion": "...",
  "comida_detectada": "...",
  "calorias_estimadas": 0,
  "macros": {
    "proteinas": "",
    "carbohidratos": "",
    "grasas": "",
    "azucar": "",
    "fibra": ""
  },
  "tabla_ejercicios": "TARJETA ESTILO B"
}
"""

        # FORMATO CORRECTO PARA GROQ
        data = {
            "model": "llama-3.2-11b-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{imagen_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 800,
            "response_format": {"type": "json_object"}
        }

        respuesta = requests.post(url, headers=headers, json=data)
        resultado = respuesta.json()

        # Extraer contenido
        contenido = resultado["choices"][0]["message"]["content"]

        # Limpieza por si Groq devuelve ```json ... ```
        if "```json" in contenido:
            contenido = contenido.split("```json")[1].split("```")[0].strip()
        elif "```" in contenido:
            contenido = contenido.split("```")[1].split("```")[0].strip()

        # Convertir a JSON
        contenido_json = json.loads(contenido)

        return jsonify(contenido_json)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/checkkey", methods=["GET"])
def checkkey():
    if GROQ_API_KEY:
        return jsonify({"status": "OK", "message": "Clave configurada"})
    else:
        return jsonify({"status": "ERROR", "message": "Clave no configurada"})


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "OK", "message": "Backend funcionando"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
