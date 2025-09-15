# from PyPDF2 import PdfReader
#
# pdf_path = "guide bpf 473 pages.pdf"
# reader = PdfReader(pdf_path)
# text = ""
# for page in reader.pages:
#     page_text = page.extract_text()
#     if page_text:
#         text += page_text + "\n"
#
# # Sauvegarde pour vérifier
# with open("document.txt", "w", encoding="utf-8") as f:
#     f.write(text)
#     # print(text)
#
#
# import re
#
# def split_text(text, max_words=500):
#     words = text.split()
#     chunks = []
#     for i in range(0, len(words), max_words):
#         chunk = " ".join(words[i:i+max_words])
#         chunks.append(chunk)
#     return chunks
#
# chunks = split_text(text)
# print(f"Nombre de chunks : {len(chunks)}")
#
#
#


# -*- coding: utf-8 -*-
"""
Script Python pour résumer et rechercher dans un PDF volumineux
100% local, compatible PyCharm
"""

import os
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Optionnel : pour résumé avec transformers
from transformers import pipeline

# ======== CONFIG ========
PDF_PATH = "guide bpf 473 pages.pdf"   # Remplace par le chemin de ton PDF
CHUNK_SIZE = 500            # Nombre de mots par chunk
USE_SUMMARIZER = True       # True pour résumer chaque chunk

# ======== 1️⃣ EXTRACTION TEXTE ========
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

text = extract_text_from_pdf(PDF_PATH)
print(f"Texte extrait : {len(text)} caractères")

# ======== 2️⃣ DIVISER EN CHUNKS ========
def split_text(text, max_words=CHUNK_SIZE):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i+max_words])
        chunks.append(chunk)
    return chunks

chunks = split_text(text)
print(f"Nombre de chunks : {len(chunks)}")

# ======== 3️⃣ RECHERCHE PAR QUESTION ========
vectorizer = TfidfVectorizer(stop_words='english')
X = vectorizer.fit_transform(chunks)

def search(query):
    query_vec = vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, X)
    best_idx = similarities.argmax()
    return chunks[best_idx]

# ======== 4️⃣ RÉSUMÉ DES CHUNKS (OPTIONNEL) ========
if USE_SUMMARIZER:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    summaries = []
    print("Résumé des chunks en cours...")
    for i, chunk in enumerate(chunks):
        summary = summarizer(chunk, max_length=200, min_length=50, do_sample=False)
        summaries.append(summary[0]['summary_text'])
        print(f"Chunk {i+1}/{len(chunks)} résumé")
    # Résumé global
    print("\n=== Résumé global ===")
    global_text = " ".join(summaries)
    global_summary = summarizer(global_text, max_length=300, min_length=100, do_sample=False)
    print(global_summary[0]['summary_text'])

# ======== 5️⃣ EXEMPLE DE RECHERCHE ========
while True:
    query = input("\nPose ta question (ou 'exit' pour quitter) : ")
    if query.lower() == 'exit':
        break
    result = search(query)
    print("\n=== Résultat trouvé ===")
    print(result)
