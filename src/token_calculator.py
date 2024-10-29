import os

import PyPDF2
import tiktoken

from corpo_chatbot.settings import BASE_DIR


def read_pdf(pdf_path):
    pdf_path = os.path.join(BASE_DIR, pdf_path)
    """Lee el contenido del PDF y lo retorna como una cadena de texto"""
    with open(pdf_path, "rb") as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
    return text


def count_tokens(text, model="gpt-3.5-turbo"):
    """Calcula la cantidad de tokens que se generarían para un modelo específico"""
    encoder = tiktoken.encoding_for_model(model)
    tokens = encoder.encode(text)
    return len(tokens)


def main(pdf_path):
    # Leer el contenido del PDF
    pdf_text = read_pdf(pdf_path)

    # Calcular el número aproximado de tokens
    num_tokens = count_tokens(pdf_text)

    # Mostrar resultados
    print(
        f"El archivo PDF '{pdf_path}' contiene aproximadamente {num_tokens} tokens para el modelo."
    )


# Ejemplo de uso
if __name__ == "__main__":
    pdf_path = "ruta_al_archivo.pdf"  # Cambia esta ruta por la ruta de tu archivo PDF
    main(pdf_path)
