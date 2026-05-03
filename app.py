# from flask import Flask, render_template, request
# from openai import OpenAI

# app = Flask(__name__)


# client = OpenAI(
#     api_key="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",
#     base_url="https://openrouter.ai/api/v1"
# )

# # client = OpenAI(api_key="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")


# def explain_medicine(text):
#     prompt = f"""
# You are a medical assistant AI.

# Explain the following prescription in:
# 1. Simple English
# 2. Simple Urdu

# For each medicine include:
# - Usage
# - Timing
# - Precautions

# Prescription:
# {text}
# """

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": prompt}]
#     )

#     return response.choices[0].message.content


# @app.route("/", methods=["GET", "POST"])
# def home():
#     result = ""

#     if request.method == "POST":
#         text = request.form.get("text")

#         if text:
#             result = explain_medicine(text)

#     return render_template("index.html", result=result)


# if __name__ == "__main__":
#     app.run(debug=True)




# Put your Anthropic API key here OR set it as an environment variable
# ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "sk-ant-api03-YOUR-KEY-HERE")

# client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import re
import os

app = Flask(__name__)

client = OpenAI(
    api_key=os.environ.get("openrouter_key"),
    base_url="https://openrouter.ai/api/v1"
)

# client = OpenAI(
#     api_key="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",
#     base_url="https://openrouter.ai/api/v1"
# )


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
        model="gpt-4o-mini",
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


# Updated ✅
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)