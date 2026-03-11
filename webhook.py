import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- MÉTODO SUPER ROBUSTO PARA OBTENER LA API KEY ---
def get_api_key():
    """Intenta obtener la API key de múltiples fuentes"""
    
    # Fuente 1: Variable de entorno normal
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        print("✅ Key encontrada en GEMINI_API_KEY")
        return key
    
    # Fuente 2: Variable con otro nombre
    key = os.environ.get("GEMINI_KEY")
    if key:
        print("✅ Key encontrada en GEMINI_KEY")
        return key
    
    # Fuente 3: Variable genérica
    key = os.environ.get("API_KEY")
    if key:
        print("✅ Key encontrada en API_KEY")
        return key
    
    # Fuente 4: Archivo de configuración (para debugging)
    try:
        with open('api_key.txt', 'r') as f:
            key = f.read().strip()
            print("✅ Key encontrada en archivo api_key.txt")
            return key
    except:
        pass
    
    # Fuente 5: VALOR HARCODEADO (solo para pruebas)
    # ¡COMENTAR EN PRODUCCIÓN!
    key = "AIzaSyDlIZ_YpeU2fVdIF-1TbgZgFhQYEdh7rGY"
    print("⚠️ USANDO KEY HARCODEADA - SOLO PARA PRUEBAS")
    return key

# Obtener la API key
API_KEY = get_api_key()

if not API_KEY:
    print("❌ ERROR CRÍTICO: No se pudo encontrar la API key")
    model = None
else:
    try:
        print(f"🔑 Configurando Gemini con key: {API_KEY[:10]}...")
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini configurado correctamente")
    except Exception as e:
        print(f"❌ Error configurando Gemini: {e}")
        model = None

# Rutas de prueba
@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "Webhook funcionando",
        "modelo_listo": model is not None
    })

@app.route('/debug-env')
def debug_env():
    """Muestra información de depuración"""
    import sys
    return jsonify({
        "variables_entorno": list(os.environ.keys()),
        "api_key_encontrada": API_KEY is not None,
        "api_key_preview": API_KEY[:10] + "..." if API_KEY else None,
        "modelo_listo": model is not None,
        "python_version": sys.version
    })

# Webhook principal
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        req = request.get_json(silent=True, force=True)
        
        # Extraer consulta
        query_text = req.get('queryResult', {}).get('queryText', '')
        parameters = req.get('queryResult', {}).get('parameters', {})
        user_question = parameters.get('consulta_usuario') or query_text
        
        if not API_KEY or model is None:
            respuesta = "Lo siento, la IA no está configurada. (Error de configuración)"
        else:
            try:
                prompt = f"Responde como experto en cigarros: {user_question}"
                response = model.generate_content(prompt)
                respuesta = response.text
            except Exception as e:
                respuesta = f"Error con la IA: {str(e)}"
        
        return jsonify({
            "fulfillmentMessages": [
                {"text": {"text": [respuesta]}}
            ]
        })
        
    except Exception as e:
        return jsonify({
            "fulfillmentMessages": [
                {"text": {"text": [f"Error: {str(e)}"]}}
            ]
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
