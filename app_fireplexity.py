# import streamlit as st
# import os
# from dotenv import load_dotenv
# import requests
#
# # Charger la clé API
# load_dotenv()
# DEFAULT_API_KEY = os.getenv("FIRECRAWL_API_KEY")
#
# st.set_page_config(page_title="AI Research Assistant (avec Fireplexity)", layout="wide")
# st.title("🔍 AI Research Assistant via Fireplexity / Firecrawl")
#
# st.write("""
# Cette application utilise **Firecrawl / Fireplexity** pour effectuer des recherches web et générer des résumés automatiques avec citations.
# """)
#
# api_key = st.text_input("🔑 Entrez votre Firecrawl API Key", type="password", value=DEFAULT_API_KEY or "")
#
# query = st.text_area(
#     "📝 Posez votre question ou indiquez le sujet de recherche",
#     placeholder="Exemple : Intelligence artificielle dans la santé, tendances technologiques..."
# )
#
# max_results = st.slider("Nombre de résultats à récupérer", min_value=3, max_value=20, value=5)
#
# if st.button("🚀 Lancer la recherche avec Fireplexity"):
#     if not api_key:
#         st.error("❌ Veuillez entrer votre Firecrawl API Key")
#     elif not query.strip():
#         st.warning("⚠️ Veuillez entrer un sujet de recherche")
#     else:
#         with st.spinner("Recherche en cours..."):
#             # Exemple d'appel à l'API Firecrawl /extract ou /search selon la documentation
#             # Attention : les noms d'endpoints peuvent varier
#             headers = {
#                 "Authorization": f"Bearer {api_key}",
#                 "Content-Type": "application/json"
#             }
#             payload = {
#                 "query": query,
#                 "num_results": max_results
#                 # d'autres paramètres éventuels selon l'API : langue, profondeur, etc.
#             }
#             response = requests.post(
#                 "https://api.firecrawl.dev/search",  # ou endpoint /search ou /deep-research
#                 headers=headers,
#                 json=payload
#             )
#             if response.status_code != 200:
#                 st.error(f"Erreur API : {response.status_code} — {response.text}")
#             else:
#                 data = response.json()
#                 # Supposons que la réponse ait une clé "answer" ou "summary" + "results"
#                 answer = data.get("answer") or data.get("summary")
#                 results = data.get("results", [])
#
#                 st.subheader("📑 Résumé généré automatiquement")
#                 if answer:
#                     st.info(answer)
#                 else:
#                     st.write("Aucun résumé généré automatiquement")
#
#                 st.subheader("🔗 Sources trouvées")
#                 for r in results:
#                     title = r.get("title")
#                     url = r.get("url")
#                     content = r.get("snippet") or r.get("content") or ""
#                     if title and url:
#                         st.markdown(f"### [{title}]({url})")
#                         st.write(content)
#                         st.caption(f"Source : {url}")
#                         st.divider()



import streamlit as st
import os
from dotenv import load_dotenv
import requests

load_dotenv()
DEFAULT_API_KEY = os.getenv("FIRECRAWL_API_KEY")

st.set_page_config(page_title="AI Research Assistant (avec Fireplexity)", layout="wide")
st.title("🔍 AI Research Assistant via Fireplexity / Firecrawl")

api_key = st.text_input("🔑 Entrez votre Firecrawl API Key", type="password", value=DEFAULT_API_KEY or "")

query = st.text_area(
    "📝 Posez votre question ou indiquez le sujet de recherche",
    placeholder="Exemple : Intelligence artificielle dans la santé, tendances technologiques..."
)

max_results = st.slider("Nombre de résultats à récupérer", min_value=3, max_value=20, value=5)

if st.button("🚀 Lancer la recherche avec Fireplexity"):
    if not api_key:
        st.error("❌ Veuillez entrer votre Firecrawl API Key")
    elif not query.strip():
        st.warning("⚠️ Veuillez entrer un sujet de recherche")
    else:
        with st.spinner("Recherche en cours..."):
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "query": query,
                "limit": max_results,
                "scrapeOptions": {
                    "formats": [
                        {"type": "markdown"}
                    ],
                    "onlyMainContent": True
                }
            }
            resp = requests.post(
                "https://api.firecrawl.dev/v2/search",
                headers=headers,
                json=payload
            )
            if resp.status_code != 200:
                st.error(f"Erreur API : {resp.status_code} — {resp.text}")
            else:
                data = resp.json()
                # Exemple: data might have keys like "data" or "results"
                # D'après la doc, les résultats de /v2/search sont dans `data` ou `results`
                results = data.get("data", [])  # ou .get("results")
                # L'answer/synthèse peut venir d'un champ summary ou answer selon impl
                answer = data.get("answer") or data.get("summary")

                st.subheader("📑 Résumé généré automatiquement")
                if answer:
                    st.info(answer)
                else:
                    st.write("Aucun résumé généré automatiquement")

                st.subheader("🔗 Sources trouvées")
                for r in results:
                    if isinstance(r, dict):  # cas normal JSON structuré
                        title = r.get("title", "Sans titre")
                        url = r.get("url", "#")
                        content = r.get("markdown") or r.get("snippet") or r.get("content", "")
                        st.markdown(f"### [{title}]({url})")
                        st.write(content)
                        st.caption(f"Source : {url}")
                        st.divider()
                    elif isinstance(r, str):  # cas où Firecrawl renvoie une simple chaîne (markdown brut)
                        st.write(r)
                        st.divider()
                    else:
                        st.write("⚠️ Format de résultat inconnu :", r)
