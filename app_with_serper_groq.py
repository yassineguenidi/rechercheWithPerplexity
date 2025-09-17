import streamlit as st
import requests
import os
from dotenv import load_dotenv

# ---------------------------
# Charger les clés API
# ---------------------------
load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


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
# Fonction : génération de réponse avec Groq API (GRATUIT)
# ---------------------------
def generate_answer_groq(context, question):
    if not GROQ_API_KEY:
        return "❌ Erreur : Clé Groq API manquante. Ajoutez GROQ_API_KEY dans vos secrets Streamlit."

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        # Construction du prompt optimisé
        system_prompt = """Tu es un assistant IA expert. Réponds aux questions en utilisant UNIQUEMENT les informations du contexte fourni. 
        Sois précis, concis et factuel. Réponds en français. Si le contexte ne contient pas la réponse, dis-le honnêtement."""

        user_prompt = f"""CONTEXTE (sources web):
{context}

QUESTION: {question}

INSTRUCTIONS:
- Réponds exclusivement en français
- Utilise uniquement les informations du contexte fourni
- Sois clair, structuré et concis (max 3 paragraphes)
- Si le contexte est insuffisant, mentionne-le

RÉPONSE:"""

        payload = {
            "model": "llama3-70b-8192",  # Modèle gratuit et très rapide
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.7,
            "stream": False
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            # Fallback: utiliser un modèle alternatif si le premier échoue
            return generate_answer_groq_fallback(context, question, GROQ_API_KEY)

    except Exception as e:
        return f"❌ Erreur technique: {str(e)}"


# Fallback avec un autre modèle Groq
def generate_answer_groq_fallback(context, question, api_key):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        user_prompt = f"Contexte: {context}\n\nQuestion: {question}\n\nRéponds en français:"

        payload = {
            # "model": "mixtral-8x7b-32768",
            "model": "llama-3.3-70b-versatile", # Modèle alternatif
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": 1000,
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"❌ Erreur Groq API: {response.status_code} - {response.text}"

    except Exception as e:
        return f"❌ Erreur fallback: {str(e)}"


# ---------------------------
# Interface Streamlit
# ---------------------------
st.set_page_config(
    page_title="AI Research Assistant - Groq",
    layout="wide",
    page_icon="🔍"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
    }
    .source-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #1E88E5;
        margin-bottom: 10px;
    }
    .answer-box {
        background-color: #e8f5e8;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🔍 AI Research Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Powered by Google Serper + Groq AI (Llama 3)</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info("Recherche web intelligente avec analyse IA")

    # Vérification des clés API
    if not SERPER_API_KEY:
        st.error("❌ Clé Serper API manquante")
    else:
        st.success("✅ Clé Serper API configurée")

    if not GROQ_API_KEY:
        st.error("❌ Clé Groq API manquante")
    else:
        st.success("✅ Clé Groq API configurée")

    st.divider()
    st.markdown("### 🔧 Paramètres")
    num_results = st.slider("Nombre de résultats", 3, 15, 8)

    st.divider()
    st.markdown("### 📊 Statut API")
    st.info("Groq API: Gratuit et rapide")
    st.info("Serper API: 1000 req/mois gratuit")

# Recherche principale
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input(
        "**🎯 Pose ta question :**",
        placeholder="Ex: Quelles sont les dernières avancées en intelligence artificielle en 2024?",
        help="Pose une question sur n'importe quel sujet"
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    search_clicked = st.button("🚀 Rechercher et Analyser", type="primary")

if search_clicked and query:
    with st.spinner("🔎 Recherche en cours..."):
        # 1️⃣ Recherche via Serper
        results = google_search(query, num_results)

        if results:
            # Afficher les sources
            st.subheader("📚 Sources trouvées")
            context_parts = []

            for i, result in enumerate(results, 1):
                with st.expander(f"📖 {result['title']}", expanded=False):
                    st.markdown(f"**🔗 URL:** [{result['link']}]({result['link']})")
                    st.markdown(f"**📝 Extrait:** {result['snippet']}")
                    context_parts.append(f"SOURCE {i}: {result['title']}\n{result['snippet']}\n")

            context = "\n".join(context_parts)

            # 2️⃣ Génération de la réponse avec Groq
            with st.spinner("🤖 Analyse des résultats avec Groq AI..."):
                answer = generate_answer_groq(context, query)

                st.subheader("💡 Réponse Intelligente")
                st.markdown('<div class="answer-box">', unsafe_allow_html=True)
                st.markdown(answer)
                st.markdown('</div>', unsafe_allow_html=True)

            # Section feedback
            st.divider()
            # st.markdown("### 📊 Feedback")
            # col_f1, col_f2, col_f3 = st.columns(3)
            # with col_f1:
            #     if st.button("👍 Excellent", use_container_width=True):
            #         st.success("Merci pour votre feedback !")
            # with col_f2:
            #     if st.button("😐 Moyen", use_container_width=True):
            #         st.info("Nous améliorons continuellement !")
            # with col_f3:
            #     if st.button("👎 Insatisfait", use_container_width=True):
            #         st.warning("Désolé, nous ferons mieux !")

        else:
            st.error("❌ Aucun résultat trouvé. Vérifiez votre clé Serper API.")

# Section d'instructions
# with st.expander("📋 Guide d'installation - GROQ GRATUIT", expanded=True):
#     st.markdown("""
#     ## 🚀 Configuration GRATUITE - Groq API
#
#     ### 1. Obtenir Groq API Key (GRATUIT)
#
#     **👉 [https://console.groq.com](https://console.groq.com)**
#
#     - ✅ Completement gratuit
#     - ✅ Très rapide (modèles Llama 3)
#     - ✅ 1000+ requêtes gratuites
#     - ✅ Pas de carte de crédit requise
#
#     **Steps:**
#     1. Allez sur [console.groq.com](https://console.groq.com)
#     2. Connectez-vous avec Google/GitHub
#     3. Allez dans "API Keys"
#     4. Cliquez "Create API Key"
#     5. Copiez la clé générée
#
#     ### 2. Serper API (GRATUIT)
#
#     **👉 [https://serper.dev](https://serper.dev)**
#
#     - 1000 requêtes/mois gratuit
#     - Clé instantanée après inscription
#
#     ### 3. Déploiement Streamlit Cloud
#
#     **Secrets:**
#     ```toml
#     SERPER_API_KEY = "votre_cle_serper"
#     GROQ_API_KEY = "votre_cle_groq"
#     ```
#
#     **requirements.txt:**
#     ```txt
#     streamlit
#     requests
#     python-dotenv
#     ```
#     """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>✨ Développé avec Streamlit | 🔍 Serper API | 🤖 Groq AI (Llama 3)</p>
    <p>🚀 100% Gratuit et Open Source</p>
    <p> développé par GUENIDI Yassine</p>
</div>
""", unsafe_allow_html=True)