from flask import Flask, render_template, request, jsonify, make_response
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
app = Flask(__name__)

# OpenRouter config
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# System prompt for GynoBot
SYSTEM_PROMPT = """
You are a licensed gynecologist answering women's health questions. 
You are kind, respectful, and informative. 
Avoid giving a direct diagnosis. Recommend professional consultation when needed.
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
