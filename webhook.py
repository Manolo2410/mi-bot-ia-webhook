# webhook.py
import json
import os
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Configuración de la IA (Gemini) con múltiples formas de obtener la key ---
print("🔍 Verificando configuración...")
print(f"📋 Variables de entorno disponibles: {list(os.environ.keys())}")

# Intentar obtener la API key de diferentes maneras
API_KEY = None

# Método 1: Variable específica
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    print("✅ API key encontrada como GEMINI_API_KEY")

# Método 2: Si no, intentar con nombre alternativo
if not API_KEY:
    API_KEY = os.environ.get("GEMINI_KEY")
    if API_KEY:
        print("✅ API key encontrada como GEMINI_KEY")

# Método 3: Variable genérica
if not API_KEY:
    API_KEY = os.environ.get("API_KEY")
    if API_KEY:
        print("✅ API key encontrada como API_KEY")

# Para pruebas locales (¡comentar en producción!)
# if not API_KEY:
#     API_KEY = "AIzaSyDlIZ_YpeU2fVdIF-1TbgZgFhQYEdh7rGY"
#     print("⚠️ Usando API key hardcodeada para pruebas")

if not API_KEY:
    print("❌ ERROR CRÍTICO: No se pudo encontrar la API key de Gemini")
    model = None
else:
    try:
        print(f"🔑 API key encontrada (primeros 10 chars): {API_KEY[:10]}...")
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini configurado correctamente")
    except Exception as e:
        print(f"❌ Error configurando Gemini: {e}")
        model = None
# -----------------------------------------

@app.route('/')
def home():
    return jsonify({
        "status": "ok", 
        "message": "Webhook de IA funcionando",
        "gemini_configured": model is not None
    })

@app.route('/check-env')
def check_env():
    """Verificar variables de entorno"""
    return jsonify({
        "variables_disponibles": list(os.environ.keys()),
        "gemini_key_configurada": "GEMINI_API_KEY" in os.environ,
        "gemini_key_valor": os.environ.get("GEMINI_API_KEY", "NO CONFIGURADA")[:15] + "..." if os.environ.get("GEMINI_API_KEY") else "NO ENCONTRADA",
        "python_version_env": os.environ.get("PYTHON_VERSION", "no especificada"),
        "modelo_cargado": model is not None
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        req = request.get_json(silent=True, force=True)
        print("✅ Solicitud recibida de Dialogflow")
        
        query_text = req.get('queryResult', {}).get('queryText', '')
        parameters = req.get('queryResult', {}).get('parameters', {})
        
        # Extraer la consulta
        user_question = parameters.get('consulta_usuario') or parameters.get('any') or query_text
        print(f"📝 Pregunta: {user_question}")

        if not API_KEY or model is None:
            ai_response_text = "Lo siento, el servicio de IA no está disponible en este momento. (Error de configuración)"
        else:
            try:
                prompt = f"""Eres un experto vendedor de una tabaquería. Responde amablemente sobre cigarros: {user_question}"""
                response = model.generate_content(prompt)
                ai_response_text = response.text
            except Exception as e:
                print(f"❌ Error: {e}")
                ai_response_text = "Lo siento, tuve un problema al contactar con la IA."

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
        print(f"❌ Error general: {e}")
        return jsonify({
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [f"Error interno: {str(e)}"]
                    }
                }
            ]
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 Servidor iniciando en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)