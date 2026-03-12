# webhook.py con OpenRouter (versión compatible)
import json
import os
import requests  # Necesario para las llamadas HTTP directas
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Configuración de OpenRouter ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Para pruebas locales, puedes descomentar esto:
# OPENROUTER_API_KEY = "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"

if not OPENROUTER_API_KEY:
    print("❌ ERROR: Variable OPENROUTER_API_KEY no configurada")
    api_key_valida = False
else:
    api_key_valida = True
    print(f"✅ API Key configurada: {OPENROUTER_API_KEY[:10]}...")
# --------------------------------------

def llamar_grok(pregunta):
    """Función para llamar a Grok vía OpenRouter usando requests directamente"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://mi-bot-ia-webhook.onrender.com",
        "X-Title": "Chatbot de Cigarros"
    }
    
    data = {
        "model": "x-ai/grok-3-mini-beta",  # Modelo económico
        "messages": [
            {
                "role": "system",
                "content": """Eres un experto vendedor de una tabaquería llamada "El Humo Perfecto". 
                Responde de manera amable, profesional y concisa a consultas sobre cigarros.
                Si la pregunta es sobre salud, menciona responsablemente que el tabaco es dañino.
                Si es sobre productos, recomienda marcas conocidas de manera objetiva."""
            },
            {
                "role": "user",
                "content": pregunta
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"📡 Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            resultado = response.json()
            respuesta = resultado['choices'][0]['message']['content']
            
            # Mostrar uso de tokens si está disponible
            if 'usage' in resultado:
                print(f"💰 Tokens usados: {resultado['usage']['total_tokens']}")
            
            return respuesta
        else:
            error_msg = f"Error {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            return f"Lo siento, tuve un problema técnico. Código: {response.status_code}"
            
    except Exception as e:
        print(f"❌ Excepción en llamada a OpenRouter: {e}")
        return f"Error de conexión: {str(e)}"

@app.route('/')
def home():
    """Página de inicio"""
    return jsonify({
        "status": "ok",
        "message": "Webhook con Grok funcionando",
        "modelo": "Grok 3 Mini (vía OpenRouter)",
        "api_key_valida": api_key_valida
    })

@app.route('/debug')
def debug():
    """Ruta de depuración"""
    return jsonify({
        "api_key_configurada": api_key_valida,
        "primeros_digitos": OPENROUTER_API_KEY[:10] + "..." if OPENROUTER_API_KEY else "No hay",
        "variables_entorno": list(os.environ.keys())
    })

@app.route('/probar-grok')
def probar_grok():
    """Ruta para probar Grok directamente"""
    if not api_key_valida:
        return jsonify({"error": "API key no configurada"})
    
    respuesta = llamar_grok("¿Qué tipos de cigarros recomiendas para un principiante?")
    return jsonify({"respuesta": respuesta})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Ruta principal que llama Dialogflow"""
    try:
        # 1. Obtener la solicitud de Dialogflow
        req = request.get_json(silent=True, force=True)
        print("✅ Solicitud recibida de Dialogflow")
        
        # 2. Extraer la consulta del usuario
        query_text = req.get('queryResult', {}).get('queryText', '')
        parameters = req.get('queryResult', {}).get('parameters', {})
        
        # Intentar obtener el parámetro consulta_usuario
        user_question = parameters.get('consulta_usuario')
        if not user_question:
            user_question = query_text
            
        print(f"📝 Pregunta del usuario: {user_question}")

        # 3. Verificar API key
        if not api_key_valida:
            ai_response_text = "Lo siento, el servicio de IA no está configurado correctamente."
        else:
            # 4. Llamar a Grok
            ai_response_text = llamar_grok(user_question)

        # 5. Formatear respuesta para Dialogflow
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
        print(f"❌ Error general en webhook: {e}")
        return jsonify({
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [f"Error interno del servidor: {str(e)}"]
                    }
                }
            ]
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Servidor iniciando en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)