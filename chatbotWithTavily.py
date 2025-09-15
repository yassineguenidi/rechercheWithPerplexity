import streamlit as st
from tavily import TavilyClient
import os
from dotenv import load_dotenv

# Charger la clé API depuis un fichier .env (sécurité)
load_dotenv()
API_KEY = os.getenv("TAVILY_API_KEY")

# Initialiser le client Tavily
client = TavilyClient(api_key=API_KEY)

# Config Streamlit
st.set_page_config(page_title="Chatbot avec Tavily", layout="wide")
st.title("🤖 Chatbot intelligent (Tavily + IA)")

# Historique de conversation
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Afficher l’historique
for msg in st.session_state["messages"]:
    role, text = msg
    with st.chat_message(role):
        st.markdown(text)

# Entrée utilisateur
if prompt := st.chat_input("Posez-moi une question..."):
    # Ajouter la question dans l’historique
    st.session_state["messages"].append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # Réponse provisoire
    with st.chat_message("assistant"):
        with st.spinner("Recherche en cours..."):
            try:
                # Appel Tavily
                results = client.search(query=prompt, max_results=3)

                # Construire la réponse avec sources
                response = "Voici ce que j’ai trouvé :\n\n"
                for r in results["results"]:
                    title = r.get("title", "Sans titre")
                    content = r.get("content", "Pas de résumé")
                    url = r.get("url", "")
                    response += f"- **{title}** : {content} ([source]({url}))\n"

            except Exception as e:
                response = f"⚠️ Erreur : {e}"

            st.markdown(response)
            st.session_state["messages"].append(("assistant", response))
