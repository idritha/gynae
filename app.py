from flask import Flask, render_template, request, jsonify, make_response
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
from openai import OpenAI
from langdetect import detect

load_dotenv()
app = Flask(__name__)

# ✅ Supported languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "ha": "Hausa",
    "yo": "Yoruba",
    "ig": "Igbo",
    "ff": "Fulani",
    "ar": "Arabic"
}

# ✅ OpenRouter client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# ✅ Base system personality
BASE_PROMPT = """
You are GynoBot — a warm, respectful, and supportive female gynecologist. 
You're here to help women understand their health in a safe, non-judgmental space. 
Use simple, caring language. Be gentle and conversational, like a trusted friend with medical knowledge.

NEVER give direct medical diagnoses or treatment. Instead, encourage professional consultation when needed.

If a user seems nervous, reassure them. If they mention symptoms, explain possibilities calmly and kindly.

You understand and can respond in English, Hausa, Yoruba, Igbo, Fulani, and Arabic, depending on how the user asks.

Always speak with empathy and a touch of sisterly kindness 💕, and feel free to use light humor to ease stress.
"""

@app.route("/")
def index():
    resp = make_response(render_template("index.html"))
    if not request.cookies.get('session_id'):
        session_id = str(uuid.uuid4())
        resp.set_cookie('session_id', session_id)
    return resp

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("message", "")

    try:
        # 🌍 Detect language
        detected = detect(user_input)
        lang_name = SUPPORTED_LANGUAGES.get(detected, "English")
        print(f"🌐 Detected language: {lang_name} ({detected})")

        # 💬 Compose dynamic prompt
        dynamic_prompt = f"""
{BASE_PROMPT}

You MUST reply in {lang_name}. Translate your response and answer ONLY in {lang_name}, not English.

"""

        # 🔁 Get AI response
        response = client.chat.completions.create(
            model="mistralai/mixtral-8x7b-instruct",
            messages=[
                {"role": "system", "content": dynamic_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        answer = response.choices[0].message.content.strip()
        return jsonify({"reply": answer})

    except Exception as e:
        print("❌ AI Error:", e)
        return jsonify({"reply": "Sorry, an error occurred. Please try again."})

if __name__ == "__main__":
    app.run(debug=True)
