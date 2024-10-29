#!/usr/bin/env python


import hashlib
import os
from io import BytesIO

import cv2
import fitz  # PyMuPDF
import numpy as np
import pytesseract
from PIL import Image

from corpo_chatbot import settings

# Configurar el path de Tesseract si es necesario (ejemplo para Windows)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

MEDIA_ROOT = settings.MEDIA_ROOT


# Función para calcular el hash de una imagen
def calcular_hash(imagen_bytes):
    hash_md5 = hashlib.md5()
    hash_md5.update(imagen_bytes)
    return hash_md5.hexdigest()


# Función para extraer imágenes y obtener texto mediante OCR
def extraer_imagenes_y_ocr(pdf_name, output_folder):

    full_path = os.path.join(MEDIA_ROOT, pdf_name)
    # Abrir el PDF
    doc = fitz.open(full_path)

    # Crear la carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Lista para almacenar los hashes de las imágenes ya extraídas
    imagenes_hashes = set()

    # Diccionario para almacenar el texto obtenido por página
    texto_por_pagina = {}

    # Iterar sobre las páginas del documento
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # Cargar la página
        images = page.get_images(full=True)  # Obtener todas las imágenes de la página

        texto_de_imagenes = ""  # Almacenar el texto de las imágenes en esta página

        for image_index, img in enumerate(images):
            xref = img[0]  # El índice de la imagen
            base_image = doc.extract_image(xref)  # Extraer la imagen
            image_bytes = base_image["image"]  # Obtener los bytes de la imagen
            image_ext = base_image[
                "ext"
            ]  # Obtener la extensión de la imagen (ej: 'png')

            # Calcular el hash de la imagen
            imagen_hash = calcular_hash(image_bytes)

            # Si el hash ya existe, es una imagen duplicada
            if imagen_hash in imagenes_hashes:
                print(
                    f"Imagen duplicada en página {page_num + 1}, imagen {image_index + 1}. No se procesará."
                )
                continue  # Saltar si es duplicada

            # Guardar el hash en el set para evitar duplicados
            imagenes_hashes.add(imagen_hash)

            # Convertir los bytes de la imagen en una imagen PIL para el OCR
            image = Image.open(BytesIO(image_bytes))
            # Aplicar filtros
            img_cv = np.array(image)
            if img_cv.shape[2] == 4:  # Verificar si tiene un canal alpha
                img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGBA2BGR)
            else:
                img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
            img_cv = cv2.resize(img_cv, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            img_cv = cv2.medianBlur(img_cv, 9)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGRA2GRAY)
            thresh1 = cv2.threshold(
                gray, 0, 225, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV
            )[1]

            # Mostrar la imagen usando OpenCV (esto abre una ventana con la imagen)
            cv2.imshow("Imagen", img_cv)
            cv2.waitKey(0)  # Espera a que se presione una tecla
            cv2.destroyAllWindows()

            # Usar OCR para extraer texto de la imagen
            texto_imagen = pytesseract.image_to_string(image)
            texto_de_imagenes += texto_imagen + "\n"  # Agregar el texto extraído

            # Guardar la imagen en la carpeta de salida (opcional)
            image_filename = f"page_{page_num + 1}_image_{image_index + 1}.{image_ext}"
            image_path = os.path.join(output_folder, image_filename)

            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)

            print(f"Imagen extraída: {image_path}")

        # Guardar el texto extraído de las imágenes en esta página
        if texto_de_imagenes.strip():  # Solo si hay texto extraído
            texto_por_pagina[page_num + 1] = texto_de_imagenes
            print(
                f"Texto extraído de imágenes en página {page_num + 1}: \n{texto_de_imagenes}"
            )

    # Retornar el texto extraído por página
    return texto_por_pagina


# Extraer texto pasando imagen
def extract_text_from_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text


# Ejemplo de uso
# pdf_path = "/ruta/al/archivo.pdf"
# output_folder = "imagenes_extraidas"
# texto_por_pagina = extraer_imagenes_y_ocr(pdf_path, output_folder)

# Mostrar el texto extraído por página
# for page_num, texto in texto_por_pagina.items():
# print(f"\nTexto de la página {page_num}:\n{texto}")
