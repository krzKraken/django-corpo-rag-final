#!/usr/bin/env python

# WARN: No se esta usando

import io

from PIL import Image
from PyPDF2 import PdfFileReader


def obtener_imagenes_pdf(ruta_archivo):
    imagenes = []
    with open(ruta_archivo, "rb") as archivo:
        pdf = PdfFileReader(archivo)
        for pagina in range(pdf.getNumPages()):
            pagina_objeto = pdf.getPage(pagina)
            imagen_bytes = pagina_objeto.extract_image(apply_rotation=False)
            if imagen_bytes is not None:
                imagen = Image.open(io.BytesIO(imagen_bytes))
                imagenes.append(imagen)
    return imagenes


ruta_archivo = "ruta/al/archivo.pdf"
imagenes = obtener_imagenes_pdf(ruta_archivo)

# Ahora puedes guardar o manipular las imágenes como desees
for imagen in imagenes:
    imagen.save("imagen_{}.png".format(imagenes.index(imagen)))
