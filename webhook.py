# webhook.py
import json
import os
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Configuración de la IA (Gemini) ---
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: La variable de entorno GEMINI_API_KEY no está configurada.")
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
    """Ruta de prueba"""
    return jsonify({
        "status": "ok", 
        "message": "Webhook de IA funcionando",
        "gemini_configured": API_KEY is not None
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # 1. Obtener la solicitud de Dialogflow
        req = request.get_json(silent=True, force=True)
        print("✅ Solicitud recibida de Dialogflow")
        
        # 2. DEBUG: Imprimir todo el request para ver qué parámetros llegan
        print("DEBUG - Request completo:")
        print(json.dumps(req, indent=2))
        
        # 3. Extraer la consulta del usuario de diferentes formas
        query_text = req.get('queryResult', {}).get('queryText', '')
        
        # Obtener todos los parámetros
        parameters = req.get('queryResult', {}).get('parameters', {})
        print(f"DEBUG - Parámetros recibidos: {parameters}")
        
        # Intentar obtener el parámetro correcto
        user_question = parameters.get('consulta_usuario')  # Primero intenta con el nombre correcto
        if not user_question:
            # Si no encuentra, usa cualquier parámetro que exista
            for key, value in parameters.items():
                if value and isinstance(value, str):
                    user_question = value
                    print(f"DEBUG - Usando parámetro alternativo: {key} = {value}")
                    break
        
        # Si aún no hay pregunta, usa el texto completo
        if not user_question:
            user_question = query_text
        
        print(f"📝 Pregunta final del usuario: {user_question}")

        # 4. Llamar a la API de Gemini
        if not API_KEY or model is None:
            ai_response_text = "Lo siento, el servicio de IA no está disponible en este momento."
        else:
            try:
                # Prompt especializado para cigarros
                prompt = f"""Eres un experto vendedor de una tabaquería llamada "El Humo Perfecto". 
                Responde de manera amable, profesional y concisa a esta consulta sobre cigarros: 
                
                {user_question}
                
                Si la pregunta es sobre salud, menciona responsablemente que el tabaco es dañino 
                pero ofrece información útil. Si es sobre productos, recomienda marcas conocidas.
                """
                
                response = model.generate_content(prompt)
                ai_response_text = response.text
                print(f"🤖 Respuesta de la IA: {ai_response_text[:100]}...")
            except Exception as e:
                print(f"❌ Error llamando a la API de Gemini: {e}")
                ai_response_text = "Lo siento, tuve un problema al contactar con mi inteligencia central."

        # 5. Formatear la respuesta para Dialogflow
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

@app.route('/debug', methods=['GET'])
def debug():
    """Ruta para depuración"""
    return jsonify({
        "api_key_configured": API_KEY is not None,
        "model_configured": model is not None,
        "python_version": os.sys.version
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 Iniciando servidor en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)