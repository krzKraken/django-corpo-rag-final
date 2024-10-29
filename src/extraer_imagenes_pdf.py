#!/usr/bin/env python


import os

import fitz  # PyMuPDF
import pytesseract
from fpdf import FPDF
from PIL import Image
from termcolor import colored

from corpo_chatbot import settings

MEDIA_ROOT = settings.MEDIA_ROOT
BASE_DIR = settings.BASE_DIR


def extraer_imagenes_pdf(ruta_pdf):
    # Abrir el documento PDF
    documento = fitz.open(ruta_pdf)

    # Extraer el nombre del archivo PDF sin la extensión
    nombre_pdf = os.path.splitext(os.path.basename(ruta_pdf))[0]

    # Crear carpeta de destino
    carpeta_destino = f"img/{nombre_pdf}"
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    # Iterar sobre cada página del PDF
    for num_pagina in range(len(documento)):
        pagina = documento[num_pagina]
        imagenes = pagina.get_images(full=True)

        # Si no hay imágenes en la página, saltar a la siguiente
        if not imagenes:
            continue

        # Iterar sobre cada imagen de la página
        for i, img in enumerate(imagenes, start=1):
            xref = img[0]
            base_imagen = documento.extract_image(xref)
            imagen_bytes = base_imagen["image"]
            extension_imagen = base_imagen["ext"]

            # Crear la ruta para guardar la imagen
            ruta_imagen = os.path.join(
                carpeta_destino,
                f"pagina_{num_pagina + 1}_imagen_{i}.{extension_imagen}",
            )

            # Guardar la imagen
            with open(ruta_imagen, "wb") as f:
                f.write(imagen_bytes)

            print(f"Imagen guardada en: {ruta_imagen}")

    # Cerrar el documento PDF
    documento.close()


def extraer_texto_de_imagenes(nombre_pdf, idioma="spa"):
    # Eliminate the ext from the pdf_file_name
    base_name, _ = os.path.splitext(nombre_pdf)

    carpeta_imagenes = f"img/{base_name}"

    # Verifica si la carpeta del PDF existe
    if not os.path.exists(carpeta_imagenes):
        print(colored(f"\n[!] La carpeta {carpeta_imagenes} no existe.\n", "red"))
        return {}  # Devolver un diccionario vacío si la carpeta no existe

    contenido_paginas = {}

    # Iterar sobre todas las imágenes en la carpeta
    for imagen in sorted(os.listdir(carpeta_imagenes)):
        ruta_imagen = os.path.join(carpeta_imagenes, imagen)

        if os.path.isfile(ruta_imagen) and ruta_imagen.lower().endswith(
            (".png", ".jpg", ".jpeg")
        ):
            try:
                # Extraer número de página de la imagen a partir del nombre (pagina_#_imagen_#)
                partes_nombre = imagen.split("_")
                if len(partes_nombre) >= 3 and partes_nombre[0] == "pagina":
                    num_pagina = int(partes_nombre[1])
                else:
                    print(f"Nombre de imagen no sigue el formato esperado: {imagen}")
                    continue

                # Abrir la imagen y realizar OCR
                img = Image.open(ruta_imagen)
                print(f"Procesando imagen: {ruta_imagen}")

                # Realizar OCR con el idioma especificado
                texto_imagen = pytesseract.image_to_string(img, lang=idioma)

                # Si hay texto en la imagen, agregarlo al contenido de la página
                if texto_imagen.strip():
                    if num_pagina not in contenido_paginas:
                        contenido_paginas[num_pagina] = ""
                    contenido_paginas[
                        num_pagina
                    ] += f"\nImagen: {imagen}\n{texto_imagen.strip()}\n"

            except Exception as e:
                print(f"Error al procesar la imagen {ruta_imagen}: {e}")

    return (
        contenido_paginas  # Asegurarse de devolver un diccionario (aunque esté vacío)
    )


def convert_text_to_pdf(title, text):

    saved_pdf_path = os.path.join(BASE_DIR, "docs")
    # Crear la carpeta de salida si no existe
    if not os.path.exists(saved_pdf_path):
        os.makedirs(saved_pdf_path)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Separar el texto por líneas usando saltos de línea
    lines = text.split("\n")
    for line in lines:
        # Usa multi_cell para que el texto se ajuste al ancho de la página
        pdf.multi_cell(0, 10, txt=line, align="L")

    # Guardar el PDF
    pdf_name = title + ".pdf"
    saved_pdf_path = os.path.join(saved_pdf_path, pdf_name)
    pdf.output(saved_pdf_path)
