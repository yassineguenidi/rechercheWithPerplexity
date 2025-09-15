import streamlit as st
import requests
import os
from dotenv import load_dotenv
import subprocess

# Charger la clé API
load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Fonction : recherche Google via Serper
def google_search(query):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": 10}  # limiter à 5 résultats
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get("organic", [])
    else:
        return []

# Fonction : résumé avec Ollama (Mistral ou LLaMA)
def generate_answer(context, question):
    # Appel à Ollama en ligne de commande (si modèle installé via `ollama pull mistral`)
    prompt = f"Voici des extraits de recherche:\n{context}\n\nQuestion: {question}\nRéponds de manière claire et concise."
    result = subprocess.run(
        ["ollama", "run", "mistral"],
        input=prompt.encode("utf-8"),
        capture_output=True
    )
    return result.stdout.decode("utf-8")

# Interface Streamlit
st.set_page_config(page_title="Mini Perplexity", layout="wide")
st.title("🔎 Mini Perplexity (Serper + Ollama)")

query = st.text_input("Pose ta question :")

if st.button("Rechercher") and query:
    with st.spinner("Recherche en cours..."):
        results = google_search(query)

        if results:
            st.subheader("📌 Sources trouvées :")
            context = ""
            for r in results:
                st.markdown(f"- [{r['title']}]({r['link']}) — {r['snippet']}")
                context += f"{r['title']}: {r['snippet']}\n"

            # Générer une réponse
            answer = generate_answer(context, query)
            st.subheader("🤖 Réponse de l'IA :")
            st.write(answer)
        else:
            st.error("Aucun résultat trouvé ou quota atteint.")
