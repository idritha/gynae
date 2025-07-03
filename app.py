from flask import Flask, render_template, request, jsonify, make_response
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
from openai import OpenAI
from langdetect import detect

SUPPORTED_LANGUAGES = {
    "en": "English",
    "ha": "Hausa",
    "yo": "Yoruba",
    "ig": "Igbo",
    "ff": "Fulani",
    "ar": "Arabic"
}


load_dotenv()
app = Flask(__name__)

# OpenRouter config
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# System prompt for GynoBot
SYSTEM_PROMPT = """
You are GynoBot — a warm, respectful, and supportive female gynecologist. 
You're here to help women understand their health in a safe, non-judgmental space. 
Use simple, caring language. Be gentle and conversational, like a trusted friend with medical knowledge.

NEVER give direct medical diagnoses or treatment. Instead, encourage professional consultation when needed.

If a user seems nervous, reassure them. If they mention symptoms, explain possibilities calmly and kindly.

You understand and can respond in English, Hausa, Yoruba, Igbo, Fulani, and Arabic, depending on how the user asks.

Always speak with empathy and a touch of sisterly kindness, and sometimes add some funny talks to make them happy.
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

        # Detect language
        detected = detect(user_input)
        lang_name = SUPPORTED_LANGUAGES.get(detected, "English")  # fallback
        print(f"Detected language: {lang_name}")

        # Dynamic system prompt
        dynamic_prompt = f"""
You are GynoBot — a kind, respectful, and helpful gynecologist who responds in {lang_name}.
Do not diagnose, just explain in simple terms.
Respond in {lang_name} ONLY.
"""
        response = client.chat.completions.create(
            model="gryphe/mythomax-l2-13b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
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
