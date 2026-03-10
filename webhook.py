# webhook.py
import json
import os
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Configuración de la IA (Gemini) ---
# Para producción (Render): Usa variable de entorno
API_KEY = os.environ.get("GEMINI_API_KEY")

# Para pruebas locales: Descomenta la siguiente línea y comenta la de arriba
# API_KEY = "AIzaSyDlIZ_YpeU2fVdIF-1TbgZgFhQYEdh7rGY"

if not API_KEY:
    print("ERROR: La variable de entorno GEMINI_API_KEY no está configurada.")
    print("La aplicación continuará pero la IA no funcionará.")
    model = None
else:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini configurado correctamente")
    except Exception as e:
        print(f"❌ Error configurando Gemini: {e}")
        model = None
# -----------------------------------------

@app.route('/')
def home():
    """Ruta de prueba para verificar que el servidor funciona"""
    return jsonify({
        "status": "ok", 
        "message": "Webhook de IA funcionando",
        "gemini_configured": API_KEY is not None
    })

# Ruta principal que Dialogflow llamará
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # 1. Obtener la solicitud de Dialogflow
        req = request.get_json(silent=True, force=True)
        print("✅ Solicitud recibida de Dialogflow")
        
        # 2. Extraer la consulta del usuario
        query_text = req.get('queryResult', {}).get('queryText', '')
        
        # Intentar obtener el parámetro específico si existe
        parameters = req.get('queryResult', {}).get('parameters', {})
        user_question = parameters.get('consulta_usuario', query_text)
        
        print(f"📝 Pregunta del usuario: {user_question}")

        # 3. Llamar a la API de Gemini
        if not API_KEY or model is None:
            ai_response_text = "Lo siento, la IA no está configurada correctamente."
        else:
            try:
                prompt = f"Eres un asistente amigable y servicial. Responde a la siguiente pregunta de un cliente de cigarros: {user_question}"
                response = model.generate_content(prompt)
                ai_response_text = response.text
                print(f"🤖 Respuesta de la IA: {ai_response_text[:100]}...")
            except Exception as e:
                print(f"❌ Error llamando a la API de Gemini: {e}")
                ai_response_text = "Lo siento, tuve un problema al contactar con mi inteligencia central."

        # 4. Formatear la respuesta para Dialogflow
        reply = {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [ai_response_text]
                    }
                }
            ]
        }

        return jsonify(reply)

    except Exception as e:
        print(f"❌ Error en el webhook: {e}")
        error_reply = {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [f"Lo siento, ocurrió un error interno: {str(e)}"]
                    }
                }
            ]
        }
        return jsonify(error_reply)

# Punto de entrada para ejecutar la app localmente
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 Iniciando servidor en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)