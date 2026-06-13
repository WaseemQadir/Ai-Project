from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import re
import os

app = Flask(__name__)

client = OpenAI(
    api_key=os.environ.get("API_key"),
    base_url="https://openrouter.ai/api/v1"
)


def explain_prescription(text, want_english=True, want_urdu=True):
    langs = []
    if want_english:
        langs.append("Simple English")
    if want_urdu:
        langs.append("Simple Urdu (اردو)")

    separator = (
        "Separate the two sections with EXACTLY these markers:\n\n"
        "===ENGLISH===\n(English content here)\n\n===URDU===\n(Urdu content here)"
        if want_english and want_urdu else ""
    )

    prompt = f"""You are a compassionate medical assistant helping patients understand their prescriptions.

Explain the prescription below in: {" AND ".join(langs)}.

For EACH medicine include:
- Usage: what it treats
- Timing: when and how to take it
- Precautions: warnings and side effects to watch for

{separator}

Use simple, friendly language. Avoid jargon. Write as if explaining to a patient with no medical background.

Prescription:
{text}"""

    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct:free",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/explain", methods=["POST"])
def explain():
    data         = request.get_json()
    text         = (data.get("text") or "").strip()
    want_english = data.get("english", True)
    want_urdu    = data.get("urdu", True)

    if not text:
        return jsonify({"error": "Please enter your prescription or medicine names."}), 400
    if not want_english and not want_urdu:
        return jsonify({"error": "Please select at least one language."}), 400

    try:
        result       = explain_prescription(text, want_english, want_urdu)
        english_text = ""
        urdu_text    = ""

        if want_english and want_urdu:
            eng_match    = re.search(r"===ENGLISH===\s*([\s\S]*?)(?:===URDU===|$)", result, re.IGNORECASE)
            urd_match    = re.search(r"===URDU===\s*([\s\S]*?)$", result, re.IGNORECASE)
            english_text = eng_match.group(1).strip() if eng_match else result
            urdu_text    = urd_match.group(1).strip() if urd_match else ""
        elif want_urdu:
            urdu_text    = result
        else:
            english_text = result

        return jsonify({"english": english_text, "urdu": urdu_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)