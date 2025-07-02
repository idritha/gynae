from flask import Flask, render_template, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_sessions.db'
db = SQLAlchemy(app)

# OpenRouter API via OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# Chat model
class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100))
    user_msg = db.Column(db.Text)
    ai_reply = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# System prompt
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
    session_id = request.cookies.get('session_id') or str(uuid.uuid4())

    try:
        response = client.chat.completions.create(
            model="openrouter/meta-llama/llama-3-8b-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ]
        )
        answer = response.choices[0].message.content.strip()

        # Save chat
        new_entry = ChatSession(session_id=session_id, user_msg=user_input, ai_reply=answer)
        db.session.add(new_entry)
        db.session.commit()

        return jsonify({"reply": answer})
    except Exception as e:
        print("❌", e)
        return jsonify({"reply": f"❌ Error: {str(e)}"}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
