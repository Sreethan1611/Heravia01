from flask import Flask, render_template, request, session, redirect, url_for
import requests
import os

app = Flask(__name__)
app.secret_key = 'change-this-secret'
SERPER_API_KEY = os.environ.get('SERPER_API_KEY')
GROQ_API_KEY = os.environ.get('GROQ_AI_API')

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
                results.append({
                    "title": item["title"],
                    "url": item["link"],
                    "snippet": item["snippet"]
                })
        return results
def ask_groq_mistral(question, snippets):
        context = "\n".join([f"{i+1}. {s['snippet']}" for i, s in enumerate(snippets)])
        prompt = f"""Given the web information below, answer the user's question clearly and concisely. Dont use any text formatting. If the information is not available, say "I could not find the website you are looking for". Do not make up answers. If the question is not related to the web information, say "I cannot answer that question". If possible mention the pro's and con's of the website. Compare the website with other websites if possible. Don't make answers confusing to humans.
    Question: {question}
    Web info:
    {context}
    Answer:"""
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-saba-24b",
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 256
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error: {response.status_code} — {response.text}"
def ask_groq_lama(question, snippets):
    context = "\n".join([f"{i+1}. {s['snippet']}" for i, s in enumerate(snippets)])
    prompt = f"""Given the web information below, answer the user's question clearly and concisely. Dont use any text formatting. If the information is not available, say "I could not find the website you are looking for". Do not make up answers. If the question is not related to the web information, say "I cannot answer that question". If possible mention the pro's and con's of the website. Compare the website with other websites if possible. Don't make answers confusing to humans.
Question: {question}
Web info:
{context}
Answer:"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256
    }
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload
    )
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} — {response.text}"
@app.route("/", methods=["GET", "POST"])
def index():
    mode = session.get('mode', 'light')
    if request.method == "POST":
        if "toggle_mode" in request.form:
            session['mode'] = 'dark' if mode == 'light' else 'light'
            return redirect(url_for("index"))
        question = request.form.get("question", "")
        snippets, answer = [], ""
        if question.strip():
            snippets = serper_search(question)
            if snippets:
                answer1 = ask_groq_mistral(question, snippets)
                answer2 = ask_groq_lama(question, snippets)
                answer = f"🔹 Mistral:\n{answer1.strip()}\n\n🔸 LLaMA 3:\n{answer2.strip()}"
            else:
                answer = "No search results found."
        return render_template("index.html", answer=answer, snippets=snippets, mode=session.get('mode', 'light'), question=question)
    return render_template("index.html", answer=None, snippets=[], mode=mode, question="")

if __name__ == "__main__":
        app.run(debug=True)