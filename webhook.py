# webhook.py con OpenRouter (Grok)
import json
import os
from flask import Flask, request, jsonify
import openai  # pip install openai

app = Flask(__name__)

# --- Configuración de OpenRouter ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Si no encuentra la variable de entorno, usa este valor directo (solo para pruebas)
# OPENROUTER_API_KEY = "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"

if not OPENROUTER_API_KEY:
    print("❌ ERROR: Variable OPENROUTER_API_KEY no configurada")
    client = None
else:
    try:
        # Configurar el cliente de OpenRouter
        client = openai.Client(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "https://mi-bot-ia-webhook.onrender.com",
                "X-Title": "Chatbot de Cigarros El Humo Perfecto"
            }
        )
        print("✅ OpenRouter configurado correctamente")
        print(f"🔑 API Key: {OPENROUTER_API_KEY[:10]}...")
    except Exception as e:
        print(f"❌ Error configurando OpenRouter: {e}")
        client = None
# --------------------------------------

@app.route('/')
def home():
    """Página de inicio para verificar que el servidor funciona"""
    return jsonify({
        "status": "ok",
        "message": "Webhook con Grok funcionando",
        "modelo": "Grok 3 Mini (vía OpenRouter)",
        "client_configurado": client is not None
    })

@app.route('/debug')
def debug():
    """Ruta de depuración para verificar configuración"""
    return jsonify({
        "api_key_configurada": OPENROUTER_API_KEY is not None,
        "primeros_digitos": OPENROUTER_API_KEY[:10] + "..." if OPENROUTER_API_KEY else "No hay",
        "client_configurado": client is not None,
        "variables_entorno": list(os.environ.keys())
    })

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
        
        # Intentar obtener el parámetro consulta_usuario, si no, usar el texto completo
        user_question = parameters.get('consulta_usuario')
        if not user_question:
            user_question = query_text
            
        print(f"📝 Pregunta del usuario: {user_question}")

        # 3. Verificar que el cliente está configurado
        if not client:
            ai_response_text = "Lo siento, el servicio de IA no está disponible en este momento (error de configuración)."
        else:
            try:
                # 4. Llamar a Grok 3 Mini vía OpenRouter
                print("🔄 Llamando a Grok 3 Mini...")
                
                # Prompt del sistema (personalidad del bot)
                system_prompt = """Eres un experto vendedor de una tabaquería llamada "El Humo Perfecto". 
                Responde de manera amable, profesional y concisa a consultas sobre cigarros, puros, tabaco y productos relacionados.
                Si la pregunta es sobre salud, menciona responsablemente que el tabaco es dañino.
                Si es sobre productos, recomienda marcas conocidas de manera objetiva.
                Mantén respuestas informativas pero no promuevas el consumo excesivo."""
                
                # Llamada a la API
                response = client.chat.completions.create(
                    model="x-ai/grok-3-mini-beta",  # Modelo económico
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_question}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                # Extraer la respuesta
                ai_response_text = response.choices[0].message.content
                print(f"🤖 Respuesta de Grok: {ai_response_text[:100]}...")
                
                # Mostrar uso de tokens (opcional)
                if hasattr(response, 'usage'):
                    print(f"💰 Tokens usados: {response.usage.total_tokens}")
                    
            except Exception as e:
                print(f"❌ Error llamando a Grok: {e}")
                ai_response_text = f"Error al contactar con Grok: {str(e)}"

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