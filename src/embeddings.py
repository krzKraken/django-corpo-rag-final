#!/usr/bin/env python3

import os

import chromadb
import pdfplumber
import PyPDF2
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PIL import Image
from termcolor import colored

from corpo_chatbot import settings
from src.extraer_imagenes_pdf import extraer_imagenes_pdf, extraer_texto_de_imagenes

load_dotenv()
# openai api key

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MEDIA_ROOT = settings.MEDIA_ROOT
BASE_DIR = settings.BASE_DIR


def read_pdf(pdf_name):
    # Read pdf from docs
    full_path = os.path.join(BASE_DIR, f"/docs/{pdf_name}")
    with open(full_path, "rb") as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
    return text


def create_embedding_from_text(text):
    vectordb_path = os.path.join(BASE_DIR, "vectordb")

    try:
        chromadb.PersistentClient(path=vectordb_path)
    except:
        print(colored(f"\n[!] Chromadb clients has already exist...\n", "yellow"))
    print(colored(f"\n[+] Creando embedding from text...\n"))
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=20000, chunk_overlap=5000)
    splits = text_splitter.split_text(text)

    vectorstore = Chroma.from_texts(
        texts=splits,
        embedding=OpenAIEmbeddings(model="text-embedding-3-large"),
        persist_directory=vectordb_path,
    )
    vectorstore.as_retriever()


def create_embedding_from_pdf(name):

    full_path = os.path.join(MEDIA_ROOT, name)

    # Extract images from pdf and save in img/'pdf_name'
    extraer_imagenes_pdf(full_path)
    contenido_imagenes = (
        extraer_texto_de_imagenes(name) or {}
    )  # if content is None return empty dict

    # Reading pdf file
    loader = PyPDFLoader(full_path)
    documents = loader.load()
    for page_number in range(len(documents)):
        text_from_images = contenido_imagenes.get(page_number + 1, "")
        documents[page_number].page_content = (
            f"\n Documento: {name}, pagina: {page_number+1}: \n"
            + documents[page_number].page_content
            + "\n"
            + text_from_images
            + "\n"
        )

    # Adding tables to documents
    with pdfplumber.open(full_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            tables_to_text = str(page.extract_tables())
            documents[page_index].page_content += tables_to_text
    # Create the img folder
    if not os.path.exists("img"):
        os.makedirs("img")

    # WARN: DELETE
    # # Adding text from images to documents - OLD Version
    # pages = convert_from_path(full_path)
    # # iterate peer page
    # for index, page in enumerate(pages):
    #     # save the imgages in img/
    #     image_path = f"img/page_{index+1}.jpg"
    #     page.save(image_path, format="JPEG")
    #     text_imagen = pytesseract.image_to_string(
    #         Image.open(image_path), lang="spa"
    #     )  # eng / spa ingles o spanol
    #     if text_imagen.strip():
    #         documents[
    #             index
    #         ].page_content += f"Texto extraido de imagen en {text_imagen}"
    #     else:
    #         print(f"No se detecto texto en las imagenes {index}")

    # NOTE: Eliminar despues de validar
    with open("extracted_text.txt", "w") as f:
        for page_number in range(len(documents)):
            f.write(f"\n--------------pagina {page_number+1}------------\n")
            f.write(documents[page_number].page_content)
            f.write(f"\n--------------------------\n")

    print(colored(f"\n[+] File: {full_path} has been loaded successfully\n", "green"))
    print(colored(f"\n[+] pages: {len(documents)}, 'green'"))

    # Creating vectordb folder
    vectordb_path = os.path.join(BASE_DIR, "vectordb")
    try:
        chromadb.PersistentClient(path=vectordb_path)
    except:
        print(colored(f"[!] Chromadb client has already exist", "yellow"))

    # Creating embeddings and adding to vectordb
    print(colored(f"[+] Creando embedding from {full_path}", "blue"))
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=20000, chunk_overlap=3000)
    splits = text_splitter.split_documents(documents)
    print(splits)

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_directory=vectordb_path,
    )

    vectorstore.as_retriever()


def get_unique_sources_list():
    vectordb_path = os.path.join(BASE_DIR, "vectordb")
    persistent_client = chromadb.PersistentClient(path=vectordb_path)
    collection_data = persistent_client.get_collection("langchain").get(
        include=["embeddings", "documents", "metadatas"]
    )

    # Extrae los metadatos
    metadatas = collection_data["metadatas"]

    # Obtén los valores únicos de 'source'
    sources = set()
    if metadatas:
        for metadata in metadatas:
            source = metadata.get("source", None)
            if source:
                sources.add(source)
    else:
        print(colored(f"[!] No metadatas loaded", "red"))

    # Obtener solo el nombre de archivo de cada ruta
    file_names = list(set(source.split("/")[-1] for source in sources))

    return file_names
