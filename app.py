from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import requests
import os

app = Flask(__name__)
CORS(app)

# Clave de Groq desde variables de entorno (Railway)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@app.route("/analizar", methods=["POST"])
def analizar():
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

        # Prompt profesional para Eat & Burn
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

Donde "TARJETA ESTILO B" debe ser una tabla visual moderna con flechas, así:

╔══════════════════════════════════════════════╗
║ 🔥  Calorías estimadas: XXX kcal             ║
╠══════════════════════════════════════════════╣
║ 🚶‍♂️  Caminar        →     XX min             ║
║ 🏃‍♂️  Correr         →     XX min             ║
║ 🚴‍♂️  Bicicleta      →     XX min             ║
║ 🏊‍♂️  Natación       →     XX min             ║
║ 💪   Gimnasio        →     XX min             ║
╚══════════════════════════════════════════════╝

- Usa calorías PRECISAS (no rangos).
- Ajusta los tiempos según las calorías detectadas.
- No añadas texto fuera del JSON.
"""

        data = {
            "model": "llama-3.2-11b-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": f"data:image/jpeg;base64,{imagen_b64}"}
                    ]
                }
            ],
            "max_tokens": 800
        }

        respuesta = requests.post(url, headers=headers, json=data)
        resultado = respuesta.json()

        # Extraer contenido
        contenido = resultado["choices"][0]["message"]["content"]

        # Convertir a JSON
        try:
            import json
            contenido_json = json.loads(contenido)
        except:
            return jsonify({"error": "El modelo devolvió un formato inesperado", "raw": contenido})

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
