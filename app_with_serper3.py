import streamlit as st
import requests
import os
from dotenv import load_dotenv

# ---------------------------
# Charger les clés API
# ---------------------------
load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


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
# Fonction : génération de réponse avec DeepSeek API
# ---------------------------
def generate_answer_deepseek(context, question):
    if not DEEPSEEK_API_KEY:
        return "❌ Erreur : Clé DeepSeek API manquante. Ajoutez DEEPSEEK_API_KEY dans vos secrets Streamlit."

    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        # Construction du prompt optimisé
        system_prompt = """Tu es un assistant IA expert. Réponds aux questions en utilisant UNIQUEMENT les informations du contexte fourni. 
        Sois précis, concis et factuel. Si le contexte ne contient pas la réponse, dis-le honnêtement."""

        user_prompt = f"""CONTEXTE:
{context}

QUESTION: {question}

INSTRUCTIONS:
- Réponds en français
- Utilise exclusivement les informations du contexte
- Sois clair et structuré
- Maximum 3 paragraphes

RÉPONSE:"""

        payload = {
            "model": "deepseek-chat",
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
            return f"❌ Erreur DeepSeek API: {response.status_code} - {response.text}"

    except Exception as e:
        return f"❌ Erreur technique: {str(e)}"


# ---------------------------
# Interface Streamlit
# ---------------------------
st.set_page_config(
    page_title="AI Research Assistant - DeepSeek",
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
st.markdown('<p class="sub-header">Powered by Google Serper + DeepSeek AI</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info("Recherche web intelligente avec analyse IA")

    # Vérification des clés API
    if not SERPER_API_KEY:
        st.error("❌ Clé Serper API manquante")
    else:
        st.success("✅ Clé Serper API configurée")

    if not DEEPSEEK_API_KEY:
        st.error("❌ Clé DeepSeek API manquante")
    else:
        st.success("✅ Clé DeepSeek API configurée")

    st.divider()
    st.markdown("### 🔧 Paramètres")
    num_results = st.slider("Nombre de résultats", 3, 15, 8)
    temperature = st.slider("Créativité IA", 0.1, 1.0, 0.7)

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

            # 2️⃣ Génération de la réponse avec DeepSeek
            with st.spinner("🤖 Analyse des résultats avec DeepSeek AI..."):
                answer = generate_answer_deepseek(context, query)

                st.subheader("💡 Réponse Intelligente")
                st.markdown('<div class="answer-box">', unsafe_allow_html=True)
                st.markdown(answer)
                st.markdown('</div>', unsafe_allow_html=True)

            # Section feedback
            st.divider()
            st.markdown("### 📊 Feedback")
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                if st.button("👍 Excellent", use_container_width=True):
                    st.success("Merci pour votre feedback !")
            with col_f2:
                if st.button("😐 Moyen", use_container_width=True):
                    st.info("Nous améliorons continuellement !")
            with col_f3:
                if st.button("👎 Insatisfait", use_container_width=True):
                    st.warning("Désolé, nous ferons mieux !")

        else:
            st.error("❌ Aucun résultat trouvé. Vérifiez :")
            st.info("1. Votre clé Serper API est-elle valide ?")
            st.info("2. Avez-vous assez de crédits Serper ?")
            st.info("3. Essayez avec une autre requête")

# Section d'instructions
with st.expander("📋 Guide d'installation et configuration", expanded=False):
    st.markdown("""
    ## 🚀 Comment configurer l'application

    ### 1. Obtenir les clés API gratuites

    **🔍 Serper API** (1000 requêtes/mois gratuit) :
    - 👉 [https://serper.dev](https://serper.dev)
    - Créez un compte gratuit
    - Allez dans "API Key" pour récupérer votre clé

    **🤖 DeepSeek API** (Gratuit pendant la bêta) :
    - 👉 [https://platform.deepseek.com](https://platform.deepseek.com)
    - Inscrivez-vous avec votre email
    - Allez dans "API Keys" pour créer une nouvelle clé
    - Modèle: `deepseek-chat`

    ### 2. Déploiement sur Streamlit Cloud

    **Secrets Streamlit** (dans le dashboard de votre app) :
    ```toml
    SERPER_API_KEY = "votre_cle_serper_ici"
    DEEPSEEK_API_KEY = "votre_cle_deepseek_ici"
    ```

    **Fichier requirements.txt** :
    ```txt
    streamlit
    requests
    python-dotenv
    ```

    ### 3. Développement local

    Créez un fichier `.env` à la racine :
    ```env
    SERPER_API_KEY=votre_cle_serper
    DEEPSEEK_API_KEY=votre_cle_deepseek
    ```
    """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>✨ Développé avec Streamlit | 🔍 Serper API | 🤖 DeepSeek AI</p>
    <p>📧 Support: votre-email@exemple.com</p>
</div>
""", unsafe_allow_html=True)

# Message si aucune clé configurée
if not SERPER_API_KEY or not DEEPSEEK_API_KEY:
    st.warning("""
    ⚠️ **Configuration requise**

    Pour utiliser cette application, vous devez configurer :
    - Clé Serper API (recherche web)
    - Clé DeepSeek API (intelligence artificielle)

    Voir le guide d'installation ci-dessus pour les obtenir gratuitement.
    """)