# import streamlit as st
#
# # Titre de l'application
# st.title("AI Research Assistant - Étape 1")
#
# # Input utilisateur
# st.subheader("Décrivez votre sujet de recherche")
# user_query = st.text_area(
#     "Exemple : Veille réglementaire sur les médicaments en France depuis janvier 2025"
# )
#
# # Options supplémentaires
# st.subheader("Options de recherche")
# date_debut = st.date_input("Date de début", value=None)
# sources_type = st.multiselect(
#     "Types de sources à inclure",
#     ["Publications officielles", "Articles scientifiques", "Communiqués de presse", "PDF", "DOCX"],
#     default=["Publications officielles"]
# )
#
# # Bouton pour lancer la recherche
# if st.button("Lancer la recherche"):
#     st.write("Sujet demandé :", user_query)
#     st.write("Date de début :", date_debut)
#     st.write("Types de sources :", sources_type)
#     st.success("✅ Étape 1 réussie ! Vous pouvez maintenant passer à la recherche préliminaire.")
#
#
# # tavily_key = "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"
# import os
# from dotenv import load_dotenv
# from tavily import TavilyClient
#
# load_dotenv()
# client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
#

# import streamlit as st
# from tavily import TavilyClient
# import os
# from dotenv import load_dotenv
#
# # Charger la clé API depuis .env (si dispo)
# load_dotenv()
# DEFAULT_API_KEY = os.getenv("TAVILY_API_KEY")
#
# # Interface utilisateur
# st.set_page_config(page_title="AI Research Assistant", layout="wide")
# st.title("🔎 AI Research Assistant - Veille Réglementaire (ANSM)")
#
# st.write("""
# Cette application utilise **Tavily API** pour rechercher des publications réglementaires
# sur le site **ANSM (ansm.sante.fr)** depuis **janvier 2025**.
# """)
#
# # Clé API
# api_key = st.text_input("🔑 Entrez votre Tavily API Key", type="password", value=DEFAULT_API_KEY or "")
#
# # Sujet de recherche
# query = st.text_area(
#     "📝 Décrivez le sujet de recherche",
#     placeholder="Exemple : nouvelles réglementations sur les autorisations de mise sur le marché"
# )
#
# # Bouton
# if st.button("🚀 Lancer la recherche"):
#     if not api_key:
#         st.error("❌ Veuillez entrer votre Tavily API Key")
#     elif not query.strip():
#         st.warning("⚠️ Veuillez entrer un sujet de recherche")
#     else:
#         # Initialiser client
#         client = TavilyClient(api_key=api_key)
#
#         with st.spinner("Recherche en cours..."):
#             response = client.search(
#                 query,
#                 max_results=10,
#                 search_depth="advanced",
#                 include_answer=True
#             )
#
#         # Affichage des résultats
#         st.subheader("📑 Résumé généré automatiquement")
#         if "answer" in response and response["answer"]:
#             st.info(response["answer"])
#         else:
#             st.write("Aucun résumé généré par Tavily")
#
#         st.subheader("🔗 Sources trouvées")
#         for r in response.get("results", []):
#             st.markdown(f"### [{r['title']}]({r['url']})")
#             st.write(r["content"])
#             st.caption(f"Source : {r['url']}")
#             st.divider()


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
api_key = st.text_input("🔑 Entrez votre Tavily API Key", type="password", value=DEFAULT_API_KEY or "")

# Sujet de recherche
query = st.text_area(
    "📝 Posez votre question ou indiquez le sujet de recherche",
    placeholder="Exemple : Intelligence artificielle dans la santé, nouvelles réglementations, tendances technologiques..."
)

# Nombre de résultats
max_results = st.slider("Nombre de résultats à récupérer", min_value=3, max_value=20, value=5)

# Bouton
if st.button("🚀 Lancer la recherche"):
    if not api_key:
        st.error("❌ Veuillez entrer votre Tavily API Key")
    elif not query.strip():
        st.warning("⚠️ Veuillez entrer un sujet de recherche")
    else:
        # Initialiser client
        client = TavilyClient(api_key=api_key)

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
