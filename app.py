from flask import Flask, render_template, request, jsonify, make_response
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
from openai import OpenAI
from langdetect import detect
from translatepy import Translator

load_dotenv()
app = Flask(__name__)

# Supported languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "ha": "Hausa",
    "yo": "Yoruba",
    "ig": "Igbo",
    "ff": "Fulani",
    "ar": "Arabic"
}

translator = Translator()

# OpenRouter client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# Base prompt
BASE_PROMPT = """
You are GynoBot — a warm, respectful, and supportive female gynecologist. 
You're here to help women understand their health in a safe, non-judgmental space. 
Use simple, caring language. Be gentle and conversational, like a trusted friend with medical knowledge.

NEVER give direct medical diagnoses or treatment. Instead, encourage professional consultation when needed.

If a user seems nervous, reassure them. If they mention symptoms, explain possibilities calmly and kindly.

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

        # 🧠 Prompt AI in English (most accurate)
        prompt = f"""{BASE_PROMPT}
Respond only in English using simple and kind words.
"""

        response = client.chat.completions.create(
            model="mistralai/mixtral-8x7b-instruct",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ]
        )
        english_reply = response.choices[0].message.content.strip()

        # 🌐 Translate if not English
        if detected != "en":
            try:
                translated = translator.translate(english_reply, destination_language=lang_name)
                final_reply = translated.result
            except Exception as te:
                print("⚠️ Translation error:", te)
                final_reply = english_reply + "\n\n(Note: Translation unavailable.)"
        else:
            final_reply = english_reply

        return jsonify({"reply": final_reply})

    except Exception as e:
        print("❌ AI Error:", e)
        return jsonify({"reply": "Sorry, an error occurred. Please try again."})

if __name__ == "__main__":
    app.run(debug=True)
