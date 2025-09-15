# # # Chatbot Streamlit avancé
# # # Fichier : chatbot_tavily_streamlit.py
# # # Description : Chatbot hybride (small-talk + base interne + Tavily)
# # # - Recherche en temps réel via Tavily
# # # - Reformulation / synthèse via OpenAI (GPT)
# # # - Upload de documents (PDF/TXT) -> recherche interne (TF-IDF)
# # # - Cache simple, fallback si Tavily lent
# # # - Interface Streamlit moderne (sidebar, paramètres, historique)
# #
# # import os
# # import time
# # import json
# # import sqlite3
# # from typing import List, Optional, Tuple
# #
# # import streamlit as st
# # from dotenv import load_dotenv
# #
# # # --- Optional libs (try to import, degrade gracefully) ---
# # try:
# #     from tavily import TavilyClient
# # except Exception:
# #     TavilyClient = None
# #
# # try:
# #     from openai import OpenAI
# # except Exception:
# #     OpenAI = None
# #
# # # For PDF reading
# # try:
# #     import PyPDF2
# # except Exception:
# #     PyPDF2 = None
# #
# # # For internal search (TF-IDF)
# # try:
# #     from sklearn.feature_extraction.text import TfidfVectorizer
# #     from sklearn.metrics.pairwise import linear_kernel
# # except Exception:
# #     TfidfVectorizer = None
# #     linear_kernel = None
# #
# # # -------------------- Helpers --------------------
# #
# # load_dotenv()
# #
# # TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
# # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# #
# # # Initialize clients lazily
# # def init_tavily_client():
# #     if TavilyClient is None:
# #         return None
# #     key = TAVILY_API_KEY or st.session_state.get("TAVILY_API_KEY")
# #     if not key:
# #         return None
# #     return TavilyClient(api_key=key)
# #
# # def init_openai_client():
# #     if OpenAI is None:
# #         return None
# #     key = OPENAI_API_KEY or st.session_state.get("OPENAI_API_KEY")
# #     if not key:
# #         return None
# #     return OpenAI(api_key=key)
# #
# # # Simple small-talk detector
# # SMALL_TALK = {
# #     "hello": "👋 Hello ! Comment puis-je vous aider aujourd'hui ?",
# #     "hi": "👋 Hi ! How can I help you today?",
# #     "salut": "👋 Salut ! Comment puis-je vous aider aujourd'hui ?",
# #     "bonjour": "👋 Bonjour ! Que puis-je faire pour vous ?",
# #     "merci": "Avec plaisir ! 😊",
# #     "au revoir": "Au revoir ! Bonne journée 👋",
# # }
# #
# # def detect_small_talk(prompt: str) -> Optional[str]:
# #     p = prompt.strip().lower()
# #     if p in SMALL_TALK:
# #         return SMALL_TALK[p]
# #     # short greetings
# #     if p in ["hey", "coucou", "yo"]:
# #         return "👋 Hello ! Comment puis-je vous aider aujourd'hui ?"
# #     return None
# #
# # # -------------------- Internal KB (upload documents + TF-IDF) --------------------
# # class InternalKB:
# #     def __init__(self):
# #         self.docs: List[str] = []
# #         self.titles: List[str] = []
# #         self.vectorizer = None
# #         self.tfidf_matrix = None
# #
# #     def add_text(self, text: str, title: str = "document"):
# #         self.titles.append(title)
# #         self.docs.append(text)
# #         self._rebuild()
# #
# #     def _rebuild(self):
# #         if TfidfVectorizer is None:
# #             return
# #         if not self.docs:
# #             self.vectorizer = None
# #             self.tfidf_matrix = None
# #             return
# #         self.vectorizer = TfidfVectorizer(stop_words="english")
# #         self.tfidf_matrix = self.vectorizer.fit_transform(self.docs)
# #
# #     def query(self, q: str, top_k: int = 2) -> List[Tuple[str, float]]:
# #         if self.vectorizer is None or self.tfidf_matrix is None:
# #             return []
# #         q_vec = self.vectorizer.transform([q])
# #         cos_sim = linear_kernel(q_vec, self.tfidf_matrix)[0]
# #         top_idx = cos_sim.argsort()[::-1][:top_k]
# #         return [(self.docs[i], float(cos_sim[i])) for i in top_idx if cos_sim[i] > 0]
# #
# # # -------------------- Simple cache --------------------
# # CACHE_DB = "chatbot_cache.sqlite"
# #
# # def init_cache_db():
# #     conn = sqlite3.connect(CACHE_DB)
# #     c = conn.cursor()
# #     c.execute("""
# #     CREATE TABLE IF NOT EXISTS cache(
# #         key TEXT PRIMARY KEY,
# #         response TEXT,
# #         timestamp REAL
# #     )
# #     """)
# #     conn.commit()
# #     conn.close()
# #
# # def cache_get(key: str) -> Optional[str]:
# #     conn = sqlite3.connect(CACHE_DB)
# #     c = conn.cursor()
# #     c.execute("SELECT response FROM cache WHERE key=?", (key,))
# #     row = c.fetchone()
# #     conn.close()
# #     if row:
# #         return row[0]
# #     return None
# #
# # def cache_set(key: str, response: str):
# #     conn = sqlite3.connect(CACHE_DB)
# #     c = conn.cursor()
# #     c.execute("REPLACE INTO cache(key, response, timestamp) VALUES(?,?,?)", (key, response, time.time()))
# #     conn.commit()
# #     conn.close()
# #
# # # -------------------- Tavily search wrapper with timeout/fallback --------------------
# #
# # def tavily_search_with_timeout(client, query: str, max_results: int = 3, timeout: int = 6):
# #     """Call Tavily but fallback if it takes longer than `timeout` seconds."""
# #     if client is None:
# #         return None
# #     cache_key = f"tavily::{query}::{max_results}"
# #     cached = cache_get(cache_key)
# #     if cached:
# #         try:
# #             return json.loads(cached)
# #         except Exception:
# #             return None
# #
# #     start = time.time()
# #     try:
# #         # Some Tavily clients might be synchronous. We'll just call and check time.
# #         results = client.search(query=query, max_results=max_results)
# #         elapsed = time.time() - start
# #         if elapsed > timeout:
# #             # mark as slow but still return
# #             return {"warning": "slow", "results": results.get("results", [])}
# #         # cache
# #         cache_set(cache_key, json.dumps(results))
# #         return results
# #     except Exception as e:
# #         return {"error": str(e)}
# #
# # # -------------------- OpenAI summarization helper --------------------
# #
# # def openai_summarize(openai_client, prompt_text: str, system_prompt: str = None) -> str:
# #     if openai_client is None:
# #         # fallback simple truncate
# #         return prompt_text[:1000] + ("..." if len(prompt_text) > 1000 else "")
# #     sys_p = system_prompt or (
# #         "Tu es un assistant qui résume les informations en une courte réponse conviviale. Mentionne une source si disponible."
# #     )
# #     try:
# #         resp = openai_client.chat.completions.create(
# #             model="gpt-4o-mini",
# #             messages=[
# #                 {"role": "system", "content": sys_p},
# #                 {"role": "user", "content": prompt_text}
# #             ],
# #             max_tokens=300,
# #             temperature=0.2,
# #         )
# #         return resp.choices[0].message.content
# #     except Exception as e:
# #         return f"[Synthèse automatique indisponible: {e}]\n" + (prompt_text[:800] + ("..." if len(prompt_text) > 800 else ""))
# #
# #
# # import requests
# #
# # def ollama_generate(prompt: str, model="mistral") -> str:
# #     url = "http://localhost:11434/api/generate"
# #     payload = {"model": model, "prompt": prompt, "stream": False}
# #     response = requests.post(url, json=payload)
# #     if response.status_code == 200:
# #         return response.json().get("response", "")
# #     else:
# #         return f"⚠️ Erreur Ollama: {response.text}"
# #
# #
# #
# # # -------------------- Streamlit UI --------------------
# #
# # st.set_page_config(page_title="Chatbot Hybride (Tavily+LLM)", layout="wide")
# #
# # # Initialize cache DB
# # init_cache_db()
# #
# # if "kb" not in st.session_state:
# #     st.session_state.kb = InternalKB()
# #
# # if "messages" not in st.session_state:
# #     st.session_state.messages = []  # list of tuples (role, text, meta)
# #
# # if "TAVILY_API_KEY" not in st.session_state:
# #     st.session_state["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY") or ""
# # if "OPENAI_API_KEY" not in st.session_state:
# #     st.session_state["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY") or ""
# #
# # # Sidebar
# # with st.sidebar:
# #     st.header("Paramètres")
# #     tavily_key_input = st.text_input("Clé Tavily (ou laisser vide si .env)", value=st.session_state["TAVILY_API_KEY"], type="password")
# #     openai_key_input = st.text_input("Clé OpenAI (ou laisser vide si .env)", value=st.session_state["OPENAI_API_KEY"], type="password")
# #     st.session_state["TAVILY_API_KEY"] = tavily_key_input
# #     st.session_state["OPENAI_API_KEY"] = openai_key_input
# #     st.markdown("---")
# #     st.write("**Options**")
# #     tavily_results_num = st.number_input("Nombre de résultats Tavily", min_value=1, max_value=10, value=3)
# #     use_openai = st.checkbox("Utiliser OpenAI pour reformuler/synthétiser (recommandé)", value=True)
# #     timeout_sec = st.number_input("Timeout Tavily (sec)", min_value=1, max_value=30, value=6)
# #     st.markdown("---")
# #     st.write("**Importer des documents (PDF / TXT)**")
# #     uploaded = st.file_uploader("Charger un document ", type=["pdf", "txt"], accept_multiple_files=True)
# #     if st.button("Indexer les documents"):  # process uploads
# #         if not uploaded:
# #             st.warning("Aucun fichier sélectionné.")
# #         else:
# #             for f in uploaded:
# #                 name = f.name
# #                 try:
# #                     if name.lower().endswith(".pdf") and PyPDF2 is not None:
# #                         reader = PyPDF2.PdfReader(f)
# #                         text = []
# #                         for p in reader.pages:
# #                             text.append(p.extract_text() or "")
# #                         txt = "\n".join(text)
# #                     else:
# #                         txt = f.read().decode("utf-8", errors="ignore")
# #                     st.session_state.kb.add_text(txt, title=name)
# #                     st.success(f"Indexe: {name}")
# #                 except Exception as e:
# #                     st.error(f"Erreur lors du traitement de {name}: {e}")
# #
# # # Main layout
# # col1, col2 = st.columns((3,1))
# #
# # with col1:
# #     st.title("🤖 Chatbot Hybride")
# #
# #     # Chat history
# #     for i, (role, text, meta) in enumerate(st.session_state.messages):
# #         if role == "user":
# #             st.markdown(f"**Vous:** {text}")
# #         else:
# #             st.markdown(f"**Bot:** {text}")
# #             if meta:
# #                 st.markdown(meta)
# #
# #     prompt = st.text_input("Tapez votre message...")
# #     if st.button("Envoyer") and prompt:
# #         # append user
# #         st.session_state.messages.append(("user", prompt, None))
# #
# #         # 1. small talk
# #         small = detect_small_talk(prompt)
# #         if small:
# #             st.session_state.messages.append(("assistant", small, None))
# #         else:
# #             # 2. internal KB
# #             internal_hits = st.session_state.kb.query(prompt, top_k=2) if TfidfVectorizer is not None else []
# #             if internal_hits:
# #                 # pick best
# #                 content, score = internal_hits[0]
# #                 summary = content[:800] + ("..." if len(content) > 800 else "")
# #                 meta = f"📚 Info interne (score {score:.3f})"
# #                 # if openai available and enabled, synthesize
# #                 openai_client = init_openai_client() if use_openai else None
# #                 if use_openai and openai_client:
# #                     synth = openai_summarize(openai_client, f"Document: {summary}\nQuestion: {prompt}")
# #                     st.session_state.messages.append(("assistant", synth, meta))
# #                 else:
# #                     st.session_state.messages.append(("assistant", summary, meta))
# #             else:
# #                 # 3. external Tavily search
# #                 tavily_client = init_tavily_client()
# #                 if tavily_client is None:
# #                     resp_text = "Tavily indisponible: fournissez une clé Tavily dans la sidebar."
# #                     st.session_state.messages.append(("assistant", resp_text, None))
# #                 else:
# #                     with st.spinner("Recherche externe en cours..."):
# #                         results = tavily_search_with_timeout(tavily_client, prompt, max_results=tavily_results_num, timeout=timeout_sec)
# #                         meta = ""
# #                         if results is None:
# #                             resp_text = "Erreur: impossible d'interroger Tavily."
# #                             st.session_state.messages.append(("assistant", resp_text, None))
# #                         elif results.get("error"):
# #                             st.session_state.messages.append(("assistant", f"Erreur Tavily: {results.get('error')}", None))
# #                         else:
# #                             if results.get("warning") == "slow":
# #                                 meta += "⏱️ Recherche lente (résultats partiels).\n"
# #                             hits = results.get("results", [])
# #                             if not hits:
# #                                 st.session_state.messages.append(("assistant", "Je n'ai rien trouvé.", None))
# #                             else:
# #                                 # build a short context for OpenAI
# #                                 brief = "\n".join([f"{h.get('title','')}: {h.get('content','')[:600]} (source: {h.get('url','')})" for h in hits[:3]])
# #                                 if use_openai and init_openai_client():
# #                                     openai_client = init_openai_client()
# #                                     answer = openai_summarize(openai_client, f"Données: {brief}\nQuestion: {prompt}\nRésume en une phrase et cite la source la plus pertinente.")
# #                                     meta += "Source principale affichée ci-dessous."
# #                                     # find top source
# #                                     top = hits[0]
# #                                     src = top.get('url','')
# #                                     st.session_state.messages.append(("assistant", answer, f"Source: {src}\n" + meta))
# #                                 else:
# #                                     # no openai -> present top result simply
# #                                     top = hits[0]
# #                                     txt = top.get('content','')
# #                                     src = top.get('url','')
# #                                     short = txt[:800] + ("..." if len(txt) > 800 else "")
# #                                     resp = f"{short}\n\nSource: {src}"
# #                                     st.session_state.messages.append(("assistant", resp, meta))
# #
# # with col2:
# #     st.markdown("### Contrôles rapides")
# #     if st.button("Effacer l'historique"):
# #         st.session_state.messages = []
# #         st.success("Historique supprimé.")
# #     st.markdown("---")
# #     st.markdown("**Statut des connectors**")
# #     st.write(f"Tavily client disponible: {TavilyClient is not None}")
# #     st.write(f"OpenAI client disponible: {OpenAI is not None}")
# #     st.write(f"PyPDF2 disponible: {PyPDF2 is not None}")
# #     st.write(f"TF-IDF disponible: {TfidfVectorizer is not None}")
# #
# #     st.markdown("---")
# #     st.markdown("### Conseils d'utilisation")
# #     st.markdown("- Pour salutations, tapez `hello` ou `bonjour` — le bot répondra naturellement.")
# #     st.markdown("- Pour infos récentes: activez Tavily dans la sidebar et fournissez une clé.")
# #     st.markdown("- Pour indexer des documents, chargez-les et cliquez sur `Indexer les documents`.")
# #
# # # End
# #
#
#
# # Chatbot Streamlit avancé corrigé (Tavily + Ollama)
# import os
# import time
# import json
# import sqlite3
# from typing import List, Optional, Tuple
#
# import streamlit as st
# from dotenv import load_dotenv
#
# # --- Optional libs ---
# try:
#     from tavily import TavilyClient
# except:
#     TavilyClient = None
#
# try:
#     import PyPDF2
# except:
#     PyPDF2 = None
#
# try:
#     from sklearn.feature_extraction.text import TfidfVectorizer
#     from sklearn.metrics.pairwise import linear_kernel
# except:
#     TfidfVectorizer = None
#     linear_kernel = None
#
# import requests
#
# # -------------------- Helpers --------------------
# load_dotenv()
#
# TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
# OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
#
# # Small talk
# SMALL_TALK = {
#     "hello": "👋 Hello ! Comment puis-je vous aider aujourd'hui ?",
#     "hi": "👋 Hi ! How can I help you today?",
#     "salut": "👋 Salut ! Comment puis-je vous aider aujourd'hui ?",
#     "bonjour": "👋 Bonjour ! Que puis-je faire pour vous ?",
#     "merci": "Avec plaisir ! 😊",
#     "au revoir": "Au revoir ! Bonne journée 👋",
# }
#
# def detect_small_talk(prompt: str) -> Optional[str]:
#     p = prompt.strip().lower()
#     if p in SMALL_TALK:
#         return SMALL_TALK[p]
#     if p in ["hey", "coucou", "yo"]:
#         return "👋 Hello ! Comment puis-je vous aider aujourd'hui ?"
#     return None
#
# # -------------------- Internal KB --------------------
# class InternalKB:
#     def __init__(self):
#         self.docs: List[str] = []
#         self.titles: List[str] = []
#         self.vectorizer = None
#         self.tfidf_matrix = None
#
#     def add_text(self, text: str, title: str = "document"):
#         self.titles.append(title)
#         self.docs.append(text)
#         self._rebuild()
#
#     def _rebuild(self):
#         if TfidfVectorizer is None or not self.docs:
#             self.vectorizer = None
#             self.tfidf_matrix = None
#             return
#         self.vectorizer = TfidfVectorizer(stop_words="english")
#         self.tfidf_matrix = self.vectorizer.fit_transform(self.docs)
#
#     def query(self, q: str, top_k: int = 2) -> List[Tuple[str, float]]:
#         if self.vectorizer is None or self.tfidf_matrix is None:
#             return []
#         q_vec = self.vectorizer.transform([q])
#         cos_sim = linear_kernel(q_vec, self.tfidf_matrix)[0]
#         top_idx = cos_sim.argsort()[::-1][:top_k]
#         return [(self.docs[i], float(cos_sim[i])) for i in top_idx if cos_sim[i] > 0]
#
# # -------------------- Cache --------------------
# CACHE_DB = "chatbot_cache.sqlite"
#
# def init_cache_db():
#     conn = sqlite3.connect(CACHE_DB)
#     c = conn.cursor()
#     c.execute("""
#     CREATE TABLE IF NOT EXISTS cache(
#         key TEXT PRIMARY KEY,
#         response TEXT,
#         timestamp REAL
#     )
#     """)
#     conn.commit()
#     conn.close()
#
# def cache_get(key: str) -> Optional[str]:
#     conn = sqlite3.connect(CACHE_DB)
#     c = conn.cursor()
#     c.execute("SELECT response FROM cache WHERE key=?", (key,))
#     row = c.fetchone()
#     conn.close()
#     return row[0] if row else None
#
# def cache_set(key: str, response: str):
#     conn = sqlite3.connect(CACHE_DB)
#     c = conn.cursor()
#     c.execute("REPLACE INTO cache(key, response, timestamp) VALUES(?,?,?)",
#               (key, response, time.time()))
#     conn.commit()
#     conn.close()
#
# # -------------------- Tavily search --------------------
# def init_tavily_client():
#     if TavilyClient is None:
#         return None
#     key = st.session_state.get("TAVILY_API_KEY") or TAVILY_API_KEY
#     if not key:
#         return None
#     return TavilyClient(api_key=key)
#
# def tavily_search_with_timeout(client, query: str, max_results: int = 3, timeout: int = 6):
#     if client is None:
#         return None
#     cache_key = f"tavily::{query}::{max_results}"
#     cached = cache_get(cache_key)
#     if cached:
#         try:
#             return json.loads(cached)
#         except:
#             pass
#     start = time.time()
#     try:
#         results = client.search(query=query, max_results=max_results)
#         if time.time() - start > timeout:
#             return {"warning": "slow", "results": results.get("results", [])}
#         cache_set(cache_key, json.dumps(results))
#         return results
#     except Exception as e:
#         return {"error": str(e)}
#
# # -------------------- Ollama --------------------
# def ollama_generate(prompt: str, model="mistral") -> str:
#     try:
#         resp = requests.post(f"{st.session_state.get('OLLAMA_URL', OLLAMA_URL)}/api/generate",
#                              json={"model": model, "prompt": prompt, "stream": False}, timeout=30)
#         if resp.status_code == 200:
#             data = resp.json()
#             if "response" in data:
#                 return data["response"]
#             if "results" in data and len(data["results"]) > 0 and "content" in data["results"][0]:
#                 return data["results"][0]["content"]
#             return str(data)
#         else:
#             return f"⚠️ Ollama error: {resp.status_code}"
#     except Exception as e:
#         return f"⚠️ Ollama error: {e}"
#
# def ollama_summarize(prompt: str, model="mistral") -> str:
#     sys_prompt = "Tu es un assistant qui résume les informations en une courte réponse conviviale. Mentionne une source si disponible.\n\n"
#     return ollama_generate(sys_prompt + prompt, model=model)
#
# # -------------------- Streamlit --------------------
# st.set_page_config(page_title="Chatbot Hybride (Tavily+Ollama)", layout="wide")
#
# # Init cache & KB
# init_cache_db()
# if "kb" not in st.session_state:
#     st.session_state.kb = InternalKB()
# if "messages" not in st.session_state:
#     st.session_state.messages = []
#
# # Sidebar
# with st.sidebar:
#     st.header("Paramètres")
#     st.session_state["TAVILY_API_KEY"] = st.text_input("Clé Tavily", value=st.session_state.get("TAVILY_API_KEY", ""), type="password")
#     st.session_state["OLLAMA_URL"] = st.text_input("URL Ollama", value=st.session_state.get("OLLAMA_URL", OLLAMA_URL))
#     tavily_results_num = st.number_input("Résultats Tavily", min_value=1, max_value=10, value=3)
#     timeout_sec = st.number_input("Timeout Tavily (s)", min_value=1, max_value=30, value=6)
#     use_ollama = st.checkbox("Utiliser Ollama pour synthèse", value=True)
#     st.markdown("---")
#     st.write("📄 Importer des documents (PDF/TXT)")
#     uploaded = st.file_uploader("Charger des fichiers", type=["pdf","txt"], accept_multiple_files=True)
#     if st.button("Indexer documents"):
#         if uploaded:
#             for f in uploaded:
#                 try:
#                     if f.name.lower().endswith(".pdf") and PyPDF2:
#                         reader = PyPDF2.PdfReader(f)
#                         text = "\n".join([p.extract_text() or "" for p in reader.pages])
#                     else:
#                         text = f.read().decode("utf-8", errors="ignore")
#                     st.session_state.kb.add_text(text, title=f.name)
#                     st.success(f"Indexé: {f.name}")
#                 except Exception as e:
#                     st.error(f"Erreur {f.name}: {e}")
#         else:
#             st.warning("Aucun fichier sélectionné.")
#
# # Main interface
# col1, col2 = st.columns((3,1))
# with col1:
#     st.title("🤖 Chatbot Hybride")
#     for role, text, meta in st.session_state.messages:
#         if role == "user":
#             st.markdown(f"**Vous:** {text}")
#         else:
#             st.markdown(f"**Bot:** {text}")
#             if meta:
#                 st.markdown(meta)
#     prompt = st.text_input("Votre message")
#     if st.button("Envoyer") and prompt:
#         st.session_state.messages.append(("user", prompt, None))
#         # Small talk
#         reply = detect_small_talk(prompt)
#         if reply:
#             st.session_state.messages.append(("assistant", reply, None))
#         else:
#             # Internal KB
#             hits = st.session_state.kb.query(prompt) if TfidfVectorizer else []
#             if hits:
#                 content, score = hits[0]
#                 summary = content[:800]+"..." if len(content)>800 else content
#                 meta = f"📚 Info interne (score {score:.3f})"
#                 if use_ollama:
#                     ans = ollama_summarize(f"Document: {summary}\nQuestion: {prompt}")
#                     st.session_state.messages.append(("assistant", ans, meta))
#                 else:
#                     st.session_state.messages.append(("assistant", summary, meta))
#             else:
#                 # Tavily search
#                 tavily_client = init_tavily_client()
#                 if tavily_client:
#                     with st.spinner("Recherche Tavily..."):
#                         res = tavily_search_with_timeout(tavily_client, prompt, tavily_results_num, timeout_sec)
#                         if res is None or res.get("error"):
#                             msg = "⚠️ Tavily indisponible ou erreur."
#                             if res and res.get("error"):
#                                 msg += f" Détails: {res.get('error')}"
#                             st.session_state.messages.append(("assistant", msg, None))
#                         else:
#                             hits = res.get("results", [])
#                             if not hits:
#                                 st.session_state.messages.append(("assistant", "Je n'ai rien trouvé.", None))
#                             else:
#                                 # On prend les 3 premiers résultats
#                                 brief = "\n".join(
#                                     [f"{h.get('title', '')}: {h.get('content', '')[:600]} (source: {h.get('url', '')})"
#                                      for h in hits[:3]])
#                                 if use_ollama:
#                                     ans = ollama_summarize(
#                                         f"Données: {brief}\nQuestion: {prompt}\nRésume en une phrase et cite la source principale.")
#                                     meta = f"Source principale: {hits[0].get('url', '')}"
#                                     st.session_state.messages.append(("assistant", ans, meta))
#                                 else:
#                                     # Sans Ollama -> texte simple
#                                     top = hits[0]
#                                     txt = top.get('content', '')
#                                     src = top.get('url', '')
#                                     short = txt[:800] + ("..." if len(txt) > 800 else "")
#                                     resp = f"{short}\n\nSource: {src}"
#                                     st.session_state.messages.append(("assistant", resp, None))
#                     else:
#
#
#                     st.session_state.messages.append(
#                         ("assistant", "Tavily non configuré. Fournissez une clé API dans la sidebar.", None))
#
#                 with col2:
#                     st.markdown("### Contrôles rapides")
#                     if st.button("Effacer l'historique"):
#                         st.session_state.messages = []
#                         st.success("Historique supprimé.")
#                     st.markdown("---")
#                     st.markdown("**Statut des connectors**")
#                     st.write(f"Tavily disponible : {TavilyClient is not None}")
#                     st.write(f"Ollama disponible : {OLLAMA_URL}")
#                     st.write(f"PyPDF2 disponible : {PyPDF2 is not None}")
#                     st.write(f"TF-IDF disponible : {TfidfVectorizer is not None}")
#                     st.markdown("---")
#                     st.markdown("### Conseils d'utilisation")
#                     st.markdown("- Tapez `hello`, `hi`, `bonjour`… pour des réponses naturelles.")
#                     st.markdown("- Fournissez une clé Tavily pour obtenir des infos récentes.")
#                     st.markdown("- Importez vos documents PDF/TXT et indexez-les pour la recherche interne.")
#
#                 # --- Fin du script ---
#


# Chatbot hybride Streamlit (Tavily + Ollama) - version single page
import os
import time
import json
import sqlite3
from typing import List, Optional, Tuple
import streamlit as st
from dotenv import load_dotenv
import requests

# --- Optional imports ---
try:
    from tavily import TavilyClient
except:
    TavilyClient = None

try:
    import PyPDF2
except:
    PyPDF2 = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
except:
    TfidfVectorizer = None
    linear_kernel = None

# -------------------- Helpers --------------------
load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

SMALL_TALK = {
    "hello": "👋 Hello ! Comment puis-je vous aider aujourd'hui ?",
    "hi": "👋 Hi ! How can I help you today?",
    "salut": "👋 Salut ! Comment puis-je vous aider aujourd'hui ?",
    "bonjour": "👋 Bonjour ! Que puis-je faire pour vous ?",
    "merci": "Avec plaisir ! 😊",
    "au revoir": "Au revoir ! Bonne journée 👋",
}

def detect_small_talk(prompt: str) -> Optional[str]:
    p = prompt.strip().lower()
    if p in SMALL_TALK:
        return SMALL_TALK[p]
    if p in ["hey", "coucou", "yo"]:
        return "👋 Hello ! Comment puis-je vous aider aujourd'hui ?"
    return None

# -------------------- Internal KB --------------------
class InternalKB:
    def __init__(self):
        self.docs: List[str] = []
        self.titles: List[str] = []
        self.vectorizer = None
        self.tfidf_matrix = None

    def add_text(self, text: str, title: str = "document"):
        self.titles.append(title)
        self.docs.append(text)
        self._rebuild()

    def _rebuild(self):
        if TfidfVectorizer is None or not self.docs:
            self.vectorizer = None
            self.tfidf_matrix = None
            return
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.vectorizer.fit_transform(self.docs)

    def query(self, q: str, top_k: int = 2) -> List[Tuple[str, float]]:
        if self.vectorizer is None or self.tfidf_matrix is None:
            return []
        q_vec = self.vectorizer.transform([q])
        cos_sim = linear_kernel(q_vec, self.tfidf_matrix)[0]
        top_idx = cos_sim.argsort()[::-1][:top_k]
        return [(self.docs[i], float(cos_sim[i])) for i in top_idx if cos_sim[i] > 0]

# -------------------- Cache --------------------
CACHE_DB = "chatbot_cache.sqlite"
def init_cache_db():
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS cache(
        key TEXT PRIMARY KEY,
        response TEXT,
        timestamp REAL
    )
    """)
    conn.commit()
    conn.close()

def cache_get(key: str) -> Optional[str]:
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute("SELECT response FROM cache WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def cache_set(key: str, response: str):
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute("REPLACE INTO cache(key, response, timestamp) VALUES(?,?,?)",
              (key, response, time.time()))
    conn.commit()
    conn.close()

# -------------------- Tavily --------------------
def init_tavily_client():
    if TavilyClient is None:
        return None
    key = st.session_state.get("TAVILY_API_KEY") or TAVILY_API_KEY
    if not key:
        return None
    return TavilyClient(api_key=key)

def tavily_search_with_timeout(client, query: str, max_results: int = 3, timeout: int = 6):
    if client is None:
        return None
    cache_key = f"tavily::{query}::{max_results}"
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass
    start = time.time()
    try:
        results = client.search(query=query, max_results=max_results)
        if time.time() - start > timeout:
            return {"warning": "slow", "results": results.get("results", [])}
        cache_set(cache_key, json.dumps(results))
        return results
    except Exception as e:
        return {"error": str(e)}

# -------------------- Ollama --------------------
def ollama_generate(prompt: str, model="mistral") -> str:
    try:
        resp = requests.post(f"{st.session_state.get('OLLAMA_URL', OLLAMA_URL)}/api/generate",
                             json={"model": model, "prompt": prompt, "stream": False}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if "response" in data:
                return data["response"]
            return str(data)
        else:
            return f"⚠️ Ollama error: {resp.status_code}"
    except Exception as e:
        return f"⚠️ Ollama error: {e}"

def ollama_summarize(prompt: str, model="mistral") -> str:
    sys_prompt = "Tu es un assistant qui résume les informations en une courte réponse conviviale. Mentionne une source si disponible.\n\n"
    return ollama_generate(sys_prompt + prompt, model=model)

# -------------------- Streamlit --------------------
st.set_page_config(page_title="Chatbot Hybride", layout="wide")
init_cache_db()
if "kb" not in st.session_state:
    st.session_state.kb = InternalKB()
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("Paramètres")
    st.session_state["TAVILY_API_KEY"] = st.text_input("Clé Tavily", value=st.session_state.get("TAVILY_API_KEY", ""), type="password")
    st.session_state["OLLAMA_URL"] = st.text_input("URL Ollama", value=st.session_state.get("OLLAMA_URL", OLLAMA_URL))
    tavily_results_num = st.number_input("Résultats Tavily", min_value=1, max_value=10, value=3)
    timeout_sec = st.number_input("Timeout Tavily (s)", min_value=1, max_value=30, value=6)
    use_ollama = st.checkbox("Utiliser Ollama pour synthèse", value=True)
    st.markdown("---")
    st.write("📄 Importer des documents (PDF/TXT)")
    uploaded = st.file_uploader("Charger des fichiers", type=["pdf","txt"], accept_multiple_files=True)
    if st.button("Indexer documents"):
        if uploaded:
            for f in uploaded:
                try:
                    if f.name.lower().endswith(".pdf") and PyPDF2:
                        reader = PyPDF2.PdfReader(f)
                        text = "\n".join([p.extract_text() or "" for p in reader.pages])
                    else:
                        text = f.read().decode("utf-8", errors="ignore")
                    st.session_state.kb.add_text(text, title=f.name)
                    st.success(f"Indexé: {f.name}")
                except Exception as e:
                    st.error(f"Erreur {f.name}: {e}")
        else:
            st.warning("Aucun fichier sélectionné.")

# Chat interface
st.title("🤖 Chatbot Hybride (Single Page)")

for role, text, meta in st.session_state.messages:
    if role == "user":
        st.markdown(f"<div style='text-align:right; background-color:#DCF8C6; padding:5px; border-radius:8px; margin:5px'>{text}</div>", unsafe_allow_html=True)
    else:
        content = f"{text}"
        if meta:
            content += f"<br><small>{meta}</small>"
        st.markdown(f"<div style='text-align:left; background-color:#F1F0F0; padding:5px; border-radius:8px; margin:5px'>{content}</div>", unsafe_allow_html=True)

prompt = st.text_input("Votre message")
if st.button("Envoyer") and prompt:
    st.session_state.messages.append(("user", prompt, None))
    reply = detect_small_talk(prompt)
    if reply:
        st.session_state.messages.append(("assistant", reply, None))
    else:
        hits = st.session_state.kb.query(prompt) if TfidfVectorizer else []
        if hits:
            content, score = hits[0]
            summary = content[:800]+"..." if len(content)>800 else content
            meta = f"📚 Info interne (score {score:.3f})"
            if use_ollama:
                ans = ollama_summarize(f"Document: {summary}\nQuestion: {prompt}")
                st.session_state.messages.append(("assistant", ans, meta))
            else:
                st.session_state.messages.append(("assistant", summary, meta))
        else:
            tavily_client = init_tavily_client()
            if tavily_client:
                with st.spinner("Recherche Tavily..."):
                    res = tavily_search_with_timeout(tavily_client, prompt, tavily_results_num, timeout_sec)
                    if res is None or res.get("error"):
                        msg = "⚠️ Tavily indisponible ou erreur."
                        if res and res.get("error"):
                            msg += f" Détails: {res.get('error')}"
                        st.session_state.messages.append(("assistant", msg, None))
                    else:
                        hits = res.get("results", [])
                        if not hits:
                            st.session_state.messages.append(("assistant", "Je n'ai rien trouvé.", None))
                        else:
                            brief = "\n".join([f"{h.get('title','')}: {h.get('content','')[:600]} (source: {h.get('url','')})" for h in hits[:3]])
                            if use_ollama:
                                ans = ollama_summarize(f"Données: {brief}\nQuestion: {prompt}")
                                meta = f"Source principale: {hits[0].get('url','')}"
                                st.session_state.messages.append(("assistant", ans, meta))
                            else:
                                top = hits[0]
                                txt = top.get('content','')
                                src = top.get('url','')
                                short = txt[:800] + ("..." if len(txt) > 800 else "")
                                resp = f"{short}\n\nSource: {src}"
                                st.session_state.messages.append(("assistant", resp, None))
            else:
                st.session_state.messages.append(("assistant", "Tavily non configuré. Fournissez une clé API.", None))

if st.button("Effacer l'historique"):
    st.session_state.messages = []
    st.success("Historique supprimé.")
