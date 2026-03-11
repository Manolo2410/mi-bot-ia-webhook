# webhook.py
import json
import os
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Configuración de la IA (Gemini) ---
# Usando Gemini 2.0 Flash (sucesor de 1.5-flash)
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: La variable de entorno GEMINI_API_KEY no está configurada.")
    model = None
else:
    try:
        genai.configure(api_key=API_KEY)
        # CAMBIO IMPORTANTE: Usar gemini-2.0-flash en lugar de 1.5-flash
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("✅ Gemini 2.0 Flash configurado correctamente")
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
        "modelo": "gemini-2.0-flash",
        "gemini_configured": model is not None
    })

@app.route('/debug-env')
def debug_env():
    """Verificar configuración"""
    return jsonify({
        "api_key_configured": API_KEY is not None,
        "model_configured": model is not None,
        "model_name": "gemini-2.0-flash"
    })

@app.route('/list-models')
def list_models():
    """Listar modelos disponibles (útil para depuración)"""
    try:
        if not API_KEY:
            return jsonify({"error": "API key no configurada"})
        
        genai.configure(api_key=API_KEY)
        models = genai.list_models()
        available_models = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                available_models.append({
                    "name": m.name,
                    "display_name": m.display_name
                })
        return jsonify({"models": available_models})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # 1. Obtener la solicitud de Dialogflow
        req = request.get_json(silent=True, force=True)
        print("✅ Solicitud recibida de Dialogflow")
        
        # 2. Extraer la consulta del usuario
        query_text = req.get('queryResult', {}).get('queryText', '')
        parameters = req.get('queryResult', {}).get('parameters', {})
        user_question = parameters.get('consulta_usuario') or query_text
        
        print(f"📝 Pregunta del usuario: {user_question}")

        # 3. Llamar a la API de Gemini 2.0
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
                ai_response_text = f"Error con la IA: {str(e)}"

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
                        "text": [f"Error interno: {str(e)}"]
                    }
                }
            ]
        }
        return jsonify(error_reply)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Iniciando servidor en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
