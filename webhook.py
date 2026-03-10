# webhook.py
import json
import os
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Configuración de la IA (Gemini) ---
# ¡IMPORTANTE! En un proyecto real, usa variables de entorno.
# Por ahora, para pruebas locales, puedes poner tu API KEY aquí.
# API_KEY = "YOUR_GEMINI_API_KEY"  # <-- PON TU API KEY AQUÍ
# Es mejor usar una variable de entorno por seguridad.
API_KEY = os.environ.get("AIzaSyDlIZ_YpeU2fVdIF-1TbgZgFhQYEdh7rGY")
if not API_KEY:
    print("ERROR: La variable de entorno GEMINI_API_KEY no está configurada.")
    # En un despliegue, esto fallaría. Para pruebas locales, puedes hardcodearla temporalmente.
    # API_KEY = "AIza..." # Descomenta y pega tu key SOLO PARA PRUEBAS LOCALES.

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Modelo gratuito y rápido
# -----------------------------------------

# Ruta principal que Dialogflow llamará
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # 1. Obtener la solicitud de Dialogflow
        req = request.get_json(silent=True, force=True)
        print("Solicitud recibida de Dialogflow:") # Para depurar
        # print(json.dumps(req, indent=2)) # Descomenta para ver el JSON completo

        # 2. Extraer la consulta del usuario
        query_text = req.get('queryResult', {}).get('queryText', '')
        # Si configuraste un parámetro, puedes extraerlo para más precisión:
        # user_question = req['queryResult']['parameters']['consulta_usuario']
        # Por simplicidad, usaremos todo el texto de la consulta.
        user_question = query_text
        print(f"Pregunta del usuario: {user_question}")

        # 3. Llamar a la API de Gemini (o la que elijas)
        if not API_KEY:
            ai_response_text = "Lo siento, la IA no está configurada correctamente."
        else:
            try:
                # Instrucción de sistema para darle un poco de personalidad/contexto al bot
                prompt = f"Eres un asistente amigable y servicial. Responde a la siguiente pregunta de un cliente de cigarros: {user_question}"
                response = model.generate_content(prompt)
                ai_response_text = response.text
                print(f"Respuesta de la IA: {ai_response_text}")
            except Exception as e:
                print(f"Error llamando a la API de Gemini: {e}")
                ai_response_text = "Lo siento, tuve un problema al contactar con mi inteligencia central."

        # 4. Formatear la respuesta para Dialogflow
        # Dialogflow espera un JSON específico.
        reply = {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [ai_response_text]
                    }
                }
            ]
        }

        # 5. Enviar la respuesta de vuelta a Dialogflow
        return jsonify(reply)

    except Exception as e:
        print(f"Error en el webhook: {e}")
        # Enviar un mensaje de error genérico de vuelta a Dialogflow
        error_reply = {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": ["Lo siento, ocurrió un error interno en el bot."]
                    }
                }
            ]
        }
        return jsonify(error_reply)

# Punto de entrada para ejecutar la app localmente
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))