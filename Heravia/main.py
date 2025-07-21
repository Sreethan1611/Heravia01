from flask import Flask, render_template, request, session, redirect, url_for
import requests
import openai
import os

app = Flask(__name__)
app.secret_key = 'change-this-secret'
SERPER_API_KEY = os.environ.get('SERPER_API_KEY')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

def serper_search(query):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, json={"q": query})
    results = []
    if resp.status_code == 200:
        json_data = resp.json()
        for item in json_data.get("organic", [])[:3]:
            results.append({"title": item["title"], "url": item["link"], "snippet": item["snippet"]})
    return results

def ask_groq_llm(question, snippets):
    context = "\n".join([f"{i+1}. {s['snippet']}" for i, s in enumerate(snippets)])
    prompt = f"""Given the web information below, answer the user's question clearly and concisely. Cite sources if possible.

Question: {question}

Web info:
{context}

Answer:"""
    openai.api_key = GROQ_API_KEY
    completion = openai.chatcompletion.create(
        model="mixtral-8x7b-32768",
        base_url="https://api.groq.com/openai/v1",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=256
    )
    return completion['choices'][0]['message']['content']

@app.route("/", methods=["GET", "POST"])
def index():
    mode = session.get('mode', 'light')
    if request.method == "POST":
        if "toggle_mode" in request.form:
            session['mode'] = 'dark' if mode == 'light' else 'light'
            return redirect(url_for("index"))
        question = request.form.get("question")
        snippets, answer = [], ""
        if question:
            snippets = serper_search(question)
            answer = ask_groq_llm(question, snippets) if snippets else "No search results found."
        return render_template("index.html", answer=answer, snippets=snippets, mode=session.get('mode', 'light'), question=question)
    return render_template("index.html", answer=None, snippets=[], mode=mode, question="")

if __name__ == "__main__":
    app.run(debug=True)