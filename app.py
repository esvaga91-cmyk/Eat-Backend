from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import requests
import os

app = Flask(__name__)
CORS(app)

# Clave de Groq desde variables de entorno en Render
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@app.route("/analizar", methods=["POST"])
def analizar():
    try:
        # Recibir imagen
        if "imagen" not in request.files:
            return jsonify({"error": "No se envió ninguna imagen"}), 400

        imagen = request.files["imagen"]
        imagen_bytes = imagen.read()
        imagen_b64 = base64.b64encode(imagen_bytes).decode("utf-8")

        # Llamada a Groq
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.2-11b-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "Analiza esta imagen y describe lo que ves."},
                        {"type": "input_image", "image_url": f"data:image/jpeg;base64,{imagen_b64}"}
                    ]
                }
            ],
            "max_tokens": 300
        }

        respuesta = requests.post(url, headers=headers, json=data)
        resultado = respuesta.json()

        texto = resultado["choices"][0]["message"]["content"]

        return jsonify({"resultado": texto})

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
