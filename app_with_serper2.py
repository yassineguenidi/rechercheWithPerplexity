# # import streamlit as st
# # import requests
# # import os
# # from dotenv import load_dotenv
# #
# # # Charger les clés API
# # load_dotenv()
# # SERPER_API_KEY = os.getenv("SERPER_API_KEY")
# # HF_API_KEY = os.getenv("HF_API_KEY")
# #
# # # Fonction : recherche Google via Serper
# # def google_search(query):
# #     url = "https://google.serper.dev/search"
# #     headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
# #     payload = {"q": query, "num": 10}  # limiter à 10 résultats
# #     response = requests.post(url, headers=headers, json=payload)
# #     if response.status_code == 200:
# #         return response.json().get("organic", [])
# #     else:
# #         return []
# #
# # # Fonction : résumé avec HuggingFace API
# # def generate_answer(context, question):
# #     prompt = f"Voici des extraits de recherche:\n{context}\n\nQuestion: {question}\nRéponds de manière claire et concise."
# #     headers = {"Authorization": f"Bearer {HF_API_KEY}"}
# #     API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
# #
# #     payload = {
# #         "inputs": prompt,
# #         "parameters": {"max_new_tokens": 500}
# #     }
# #
# #     response = requests.post(API_URL, headers=headers, json=payload)
# #     if response.status_code == 200:
# #         output = response.json()
# #         # Certains modèles renvoient la réponse sous output[0]['generated_text']
# #         if isinstance(output, list) and 'generated_text' in output[0]:
# #             return output[0]['generated_text']
# #         else:
# #             return str(output)
# #     else:
# #         return f"Erreur API HuggingFace: {response.status_code} {response.text}"
# #
# # # Interface Streamlit
# # st.set_page_config(page_title="Mini Perplexity 2", layout="wide")
# # st.title("🔎 Mini Perplexity 2 (Serper + HuggingFace)")
# #
# # query = st.text_input("Pose ta question :")
# #
# # if st.button("Rechercher") and query:
# #     with st.spinner("Recherche en cours..."):
# #         results = google_search(query)
# #
# #         if results:
# #             st.subheader("📌 Sources trouvées :")
# #             context = ""
# #             for r in results:
# #                 st.markdown(f"- [{r['title']}]({r['link']}) — {r['snippet']}")
# #                 context += f"{r['title']}: {r['snippet']}\n"
# #
# #             # Générer une réponse
# #             answer = generate_answer(context, query)
# #             st.subheader("🤖 Réponse de l'IA :")
# #             st.write(answer)
# #         else:
# #             st.error("Aucun résultat trouvé ou quota atteint.")
#
#
# import streamlit as st
# import requests
# import os
# from dotenv import load_dotenv
#
# # Charger les clés API
# load_dotenv()
# SERPER_API_KEY = os.getenv("SERPER_API_KEY")
# HF_API_KEY = os.getenv("HF_API_KEY")
#
#
# # Fonction : recherche Google via Serper
# def google_search(query):
#     url = "https://google.serper.dev/search"
#     headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
#     payload = {"q": query, "num": 10}  # limiter à 10 résultats
#     response = requests.post(url, headers=headers, json=payload)
#     if response.status_code == 200:
#         return response.json().get("organic", [])
#     else:
#         st.error(f"Erreur Serper API: {response.status_code}")
#         return []
#
#
# # Fonction : résumé avec HuggingFace API
# def generate_answer(context, question):
#     prompt = f"Voici des extraits de recherche:\n{context}\n\nQuestion: {question}\nRéponds de manière claire et concise."
#     headers = {"Authorization": f"Bearer {HF_API_KEY}"}
#     API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
#
#     payload = {
#         "inputs": prompt,
#         "parameters": {"max_new_tokens": 500}
#     }
#
#     response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
#
#     if response.status_code == 200:
#         output = response.json()
#         # Vérifier si la réponse contient du texte généré
#         if isinstance(output, list) and len(output) > 0 and 'generated_text' in output[0]:
#             return output[0]['generated_text']
#         # Certains modèles renvoient directement du texte
#         elif isinstance(output, dict) and 'generated_text' in output:
#             return output['generated_text']
#         else:
#             return str(output)
#     else:
#         return f"Erreur HuggingFace API: {response.status_code} - {response.text}"
#
#
# # Interface Streamlit
# st.set_page_config(page_title="Mini Perplexity 2", layout="wide")
# st.title("🔎 Mini Perplexity 2 (Serper + HuggingFace)")
#
# query = st.text_input("Pose ta question :")
#
# if st.button("Rechercher") and query:
#     with st.spinner("Recherche en cours..."):
#         # Rechercher sur Google via Serper
#         results = google_search(query)
#
#         if results:
#             st.subheader("📌 Sources trouvées :")
#             context = ""
#             for r in results:
#                 st.markdown(f"- [{r['title']}]({r['link']}) — {r['snippet']}")
#                 context += f"{r['title']}: {r['snippet']}\n"
#
#             # Générer la réponse via HuggingFace
#             answer = generate_answer(context, query)
#             st.subheader("🤖 Réponse de l'IA :")
#             st.write(answer)
#         else:
#             st.error("Aucun résultat trouvé ou quota atteint.")


import streamlit as st
import requests
import os
from dotenv import load_dotenv

# ---------------------------
# Charger les clés API
# ---------------------------
load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# ---------------------------
# Fonction : recherche Google via Serper
# ---------------------------
def google_search(query, num_results=10):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": num_results}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json().get("organic", [])
        else:
            st.error(f"Erreur Serper API: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"Erreur lors de la recherche Serper: {str(e)}")
        return []

# ---------------------------
# Fonction : résumé avec HuggingFace API
# ---------------------------
# def generate_answer(context, question):
#     if not HF_API_KEY:
#         return "Erreur : HuggingFace API Key introuvable. Vérifiez votre fichier .env."
#
#     prompt = f"Voici des extraits de recherche:\n{context}\n\nQuestion: {question}\nRéponds de manière claire et concise."
#     headers = {"Authorization": f"Bearer {HF_API_KEY}"}
#     API_URL = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
#     payload = {"inputs": prompt, "parameters": {"max_new_tokens": 500}}
#
#     try:
#         response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
#         if response.status_code == 200:
#             output = response.json()
#             # Certains modèles renvoient la réponse dans output[0]['generated_text']
#             if isinstance(output, list) and len(output) > 0 and 'generated_text' in output[0]:
#                 return output[0]['generated_text']
#             elif isinstance(output, dict) and 'generated_text' in output:
#                 return output['generated_text']
#             else:
#                 return str(output)
#         elif response.status_code == 401:
#             return "Erreur : Clé HuggingFace invalide ou manquante (401)."
#         elif response.status_code == 403:
#             return "Erreur : Accès interdit à l'API HuggingFace (403)."
#         else:
#             return f"Erreur API HuggingFace: {response.status_code} - {response.text}"
#     except Exception as e:
#         return f"Erreur lors de l'appel HuggingFace API: {str(e)}"


# ---------------------------
# Fonction : résumé avec HuggingFace API
# ---------------------------
def generate_answer(context, question):
    if not HF_API_KEY:
        return "Erreur : HuggingFace API Key introuvable. Vérifiez votre fichier .env."

    # Format correct pour l'API de question-réponse
    payload = {
        "inputs": {
            "question": question,
            "context": context
        },
        "parameters": {
            "max_answer_len": 500,
            "max_seq_len": 512
        }
    }

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    API_URL = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            output = response.json()
            # Le modèle roberta-base-squad2 renvoie la réponse dans 'answer'
            if isinstance(output, dict) and 'answer' in output:
                return output['answer']
            else:
                return f"Format de réponse inattendu: {str(output)}"
        elif response.status_code == 401:
            return "Erreur : Clé HuggingFace invalide ou manquante (401)."
        elif response.status_code == 403:
            return "Erreur : Accès interdit à l'API HuggingFace (403)."
        else:
            return f"Erreur API HuggingFace: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Erreur lors de l'appel HuggingFace API: {str(e)}"

# ---------------------------
# Interface Streamlit
# ---------------------------
st.set_page_config(page_title="Mini Perplexity 2", layout="wide")
st.title("🔎 Mini Perplexity 2 (Serper + HuggingFace)")

query = st.text_input("Pose ta question :")

if st.button("Rechercher") and query:
    with st.spinner("Recherche en cours..."):
        # 1️⃣ Recherche via Serper
        results = google_search(query)
        if results:
            st.subheader("📌 Sources trouvées :")
            context = ""
            for r in results:
                st.markdown(f"- [{r['title']}]({r['link']}) — {r['snippet']}")
                context += f"{r['title']}: {r['snippet']}\n"

            # 2️⃣ Générer la réponse via HuggingFace
            answer = generate_answer(context, query)
            st.subheader("🤖 Réponse de l'IA :")
            st.write(answer)
        else:
            st.error("Aucun résultat trouvé ou quota Serper atteint.")
