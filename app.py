import os
from flask import Flask, render_template, request, jsonify
import requests, os, sqlite3, time

print("GROQ_API_KEY =", os.getenv("GROQ_API_KEY"))

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"  # very fast

DB_PATH = "history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news TEXT,
            label TEXT,

            
            confidence INTEGER,
            source_hint TEXT,
            ts INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

def call_groq_llm(news_text: str):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""
You are a strict fake news detector.
Analyze the news below and respond in JSON only with:
{{
  "label": "REAL" or "FAKE",
  "confidence": number between 0-100,
  "source_hint": short hint about likely source credibility
}}

News:
\"\"\"{news_text}\"\"\"
"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You detect fake news. Output JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    content = data["choices"][0]["message"]["content"]

    # Try to parse JSON safely
    import json
    try:
        result = json.loads(content)
        label = result.get("label", "FAKE")
        confidence = int(result.get("confidence", 50))
        source_hint = result.get("source_hint", "Unknown source credibility")
    except Exception:
        label = "FAKE"
        confidence = 50
        source_hint = "Could not parse model output"

    return label, confidence, source_hint

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    news = request.json.get("news", "").strip()
    if not news:
        return jsonify({"error": "Empty news"}), 400

    label, confidence, source_hint = call_groq_llm(news)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO history (news, label, confidence, source_hint, ts) VALUES (?,?,?,?,?)",
              (news, label, confidence, source_hint, int(time.time())))
    conn.commit()
    conn.close()

    return jsonify({
        "label": label,
        "confidence": confidence,
        "source_hint": source_hint
    })

@app.route("/history")
def history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, news, label, confidence, source_hint, ts FROM history ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()

    out = []
    for r in rows:
        out.append({
            "id": r[0],
            "news": r[1],
            "label": r[2],
            "confidence": r[3],
            "source_hint": r[4],
            "ts": r[5]
        })
    return jsonify(out)

if __name__ == "__main__":
    app.run(debug=True)
