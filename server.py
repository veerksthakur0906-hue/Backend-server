from flask import Flask, request, jsonify
import os
import requests
from google import genai

app = Flask(__name__)

# ==========================================
# SECURE MULTI-API KEY VAULT (3 Gemini & 2 Groq)
# ==========================================
GEMINI_KEYS = [
    os.environ.get("GEMINI_KEY_1", "YAHAN_GEMINI_KEY_1_DALE"),
    os.environ.get("GEMINI_KEY_2", "YAHAN_GEMINI_KEY_2_DALE"),
    os.environ.get("GEMINI_KEY_3", "YAHAN_GEMINI_KEY_3_DALE"),
]

GROQ_KEYS = [
    os.environ.get("GROQ_KEY_1", "YAHAN_GROQ_KEY_1_DALE"),
    os.environ.get("GROQ_KEY_2", "YAHAN_GROQ_KEY_2_DALE"),
]

# Khaali keys filter kar dete hain
GEMINI_KEYS = [k for k in GEMINI_KEYS if k and "YAHAN_" not in k]
GROQ_KEYS = [k for k in GROQ_KEYS if k and "YAHAN_" not in k]

gemini_index = 0
groq_index = 0

def call_server_ai(system_instruction, user_prompt, preferred_model="gemini"):
    global gemini_index, groq_index
    
    # Agar model groq manga hai ya gemini khatam ho gaya
    if preferred_model == "groq" and GROQ_KEYS:
        attempts = 0
        while attempts < len(GROQ_KEYS):
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_KEYS[groq_index]}", "Content-Type": "application/json"}
                data = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt}
                    ]
                }
                res = requests.post(url, json=data, headers=headers, timeout=15)
                if res.status_code == 200:
                    return res.json()['choices'][0]['message']['content']
            except Exception:
                pass
            groq_index = (groq_index + 1) % len(GROQ_KEYS)
            attempts += 1

    # Default Gemini Rotation (3 Keys)
    if GEMINI_KEYS:
        attempts = 0
        while attempts < len(GEMINI_KEYS):
            try:
                client = genai.Client(api_key=GEMINI_KEYS[gemini_index])
                res = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=[system_instruction, user_prompt]
                )
                if res.text:
                    return res.text
            except Exception as e:
                pass
            gemini_index = (gemini_index + 1) % len(GEMINI_KEYS)
            attempts += 1

    # Fallback agar sab fail ho jayein
    if GROQ_KEYS:
        return call_server_ai(system_instruction, user_prompt, preferred_model="groq")
    
    return "Error: All API keys exhausted or invalid."

@app.route('/api/generate', methods=['POST'])
def generate_endpoint():
    data = request.json or {}
    prompt = data.get("prompt", "")
    system_instruction = data.get("system_instruction", "You are a helpful AI assistant.")
    model_type = data.get("model", "gemini")

    if not prompt:
        return jsonify({"status": "error", "message": "Prompt is required"}), 400

    response_text = call_server_ai(system_instruction, prompt, preferred_model=model_type)
    return jsonify({"status": "success", "response": response_text})

if __name__ == '__main__':
    print("🚀 Central Backend API Server Running on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
