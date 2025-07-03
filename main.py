import os
from flask import Flask, render_template, jsonify, request
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from openai import OpenAIError, RateLimitError

from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://pavanitha:oxwMDnQDU8RTE4p7@cluster0.cunszbm.mongodb.net/chatgpt1"
mongo = PyMongo(app)

@app.route("/")
def home():
    chats = mongo.db.chats.find({})
    myChats = [chat for chat in chats]
    print(myChats)
    return render_template("index.html", myChats = myChats)


@app.route("/api", methods=["POST"])
def qa():
    # 1️⃣ Parse incoming JSON
    body = request.json or {}
    question = body.get("question", "").strip()
    print("DEBUG step 1 – question:", repr(question))

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # 2️⃣ Check cache
    cached = mongo.db.chats.find_one({"question": question})
    print("DEBUG step 2 – cached:", bool(cached))
    if cached:
        return jsonify({"question": question, "answer": cached["answer"]})

    # 3️⃣ Call OpenAI
    try:
        chat = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are ChatGPT, a helpful, polite, and detail-oriented assistant. You provide clear, step-by-step, and complete answers for anything the user asks, especially food recipes, explanations, and advice."}
,
                {"role": "user", "content": question}
            ],
            temperature=0.,
            max_tokens=1024
        )
        answer = chat.choices[0].message.content.strip()
        print("DEBUG step 3 – got answer:", answer[:60] + "…")
    except RateLimitError:
        answer = "Sorry, my quota is exhausted. Please try again later."
        print("DEBUG step 3 – RateLimitError")
    except OpenAIError as e:
        answer = f"OpenAI error: {e}"
        print("DEBUG step 3 – OpenAIError:", e)

    # 4️⃣ Save & return
    mongo.db.chats.insert_one({"question": question, "answer": answer})
    print("DEBUG step 4 – saved to DB")
    return jsonify({"question": question, "answer": answer})


app.run(debug=True, port=5001)  