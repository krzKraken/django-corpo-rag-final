#!/usr/bin/env python3
import os

import openai
from dotenv import load_dotenv
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from termcolor import colored

from corpo_chatbot.settings import BASE_DIR

# from src.response_to_html import format_to_html
# from src.token_calculator import main

# loading dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, max_tokens=800)
chromadb_path = os.path.join(BASE_DIR, "vectordb")
chroma_local = Chroma(
    persist_directory=chromadb_path,
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
)


def prompt(text):
    system_prompt = text + "{context}"
    print(colored(f"########...ESTO ES UNA PRUEBA.############\n"))
    print(colored(system_prompt, "red"))

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    print(colored(f"########...ESTO ES UNA PRUEBA.############\n"))
    return prompt


def complete_query(query, llm, chroma_db, prompt):
    retriever = chroma_db.as_retriever()
    chain = create_stuff_documents_chain(llm, prompt)
    rag = create_retrieval_chain(retriever, chain)
    results = rag.invoke({"input": query})
    # Printing retriever_response from embeddings docs
    retriever_response = results["context"]
    print(colored(f"########...RETRIEVER.############\n", "green"))
    print(colored(retriever_response, "blue"))

    print(colored(f"########...RETRIEVER.############\n", "green"))
    return results


text = """Eres un asistente experto que responde preguntas basadas en los documentos relevantes.Por favor, responde a mi pregunta basándote en estos documentos. Al final de cada respuesta menciona el origen del documento (nombre de documento) y pagina donde se encuentra. Si no sabes la respuesta solo di que no tienes informacion de este documento"""


def get_embedding_response(question):
    try:

        response = complete_query(question, llm, chroma_local, prompt(text))["answer"]
        print(colored(f"\n[+] Response: {response}", "blue"))
        return response
    except:
        return "No fue posible conectar con la base de datos de embeddings"
