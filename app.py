import streamlit as st
from tavily import TavilyClient
import os
from dotenv import load_dotenv

# Charger la clé API depuis .env (si dispo)
load_dotenv()
DEFAULT_API_KEY = os.getenv("TAVILY_API_KEY")

# Interface utilisateur
st.set_page_config(page_title="AI Research Assistant", layout="wide")
st.title("🔎 AI Research Assistant - Recherche Générale")

st.write("""
Cette application utilise **Tavily API** pour effectuer des recherches générales sur le web 
et générer des résumés automatiques des sources trouvées.
""")

# Clé API
# api_key = st.text_input("🔑 Entrez votre Tavily API Key", type="password", value=DEFAULT_API_KEY or "")

# Sujet de recherche
query = st.text_area(
    "📝 Posez votre question ou indiquez le sujet de recherche",
    placeholder="Exemple : Intelligence artificielle dans la santé, nouvelles réglementations, tendances technologiques..."
)

# Nombre de résultats
max_results = st.slider("Nombre de résultats à récupérer", min_value=3, max_value=20, value=5)

# Bouton
if st.button("🚀 Lancer la recherche"):
    if not DEFAULT_API_KEY:
        st.error("❌ Veuillez entrer votre Tavily API Key")
    elif not query.strip():
        st.warning("⚠️ Veuillez entrer un sujet de recherche")
    else:
        # Initialiser client
        client = TavilyClient(api_key=DEFAULT_API_KEY)

        with st.spinner("Recherche en cours..."):
            response = client.search(
                query,
                max_results=max_results,
                search_depth="advanced",
                include_answer=True
            )

        # Affichage des résultats
        st.subheader("📑 Résumé généré automatiquement")
        if "answer" in response and response["answer"]:
            st.info(response["answer"])
        else:
            st.write("Aucun résumé généré par Tavily")

        st.subheader("🔗 Sources trouvées")
        for r in response.get("results", []):
            st.markdown(f"### [{r['title']}]({r['url']})")
            st.write(r["content"])
            st.caption(f"Source : {r['url']}")
            st.divider()
