import os

import openai
from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from dotenv import load_dotenv
from termcolor import colored

from src.embeddingchat import get_embedding_response
from src.embeddings import create_embedding_from_pdf, get_unique_sources_list
from src.extraer_imagenes_pdf import convert_text_to_pdf
from src.response_to_html import format_to_html

from .models import Blog, Chat

# Ruta almacenamiento de documentos
DOCS_DIR = os.path.join(settings.MEDIA_ROOT)

# Views
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)


# NOTE: Admin verify
def is_admin(user):
    return user.is_superuser


def welcome(request):
    return render(request, "welcome.html")


def ask_openai(message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente virtual de una empresa de equipos medicos, vas a responder como su asistente personal."
                "",
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        max_tokens=500,
        temperature=1,
    )
    if response.choices[0].message.content:
        answer = response.choices[0].message.content.strip()
        return answer
    else:
        return "No answer received from chatgpt"


@login_required
def chatbot(request):
    chats = Chat.objects.filter(user=request.user)

    if request.method == "POST":
        message = request.POST.get("message")
        response = ask_openai(message)
        response = format_to_html(response)
        # NOTE: Create a chat for db
        chat = Chat(
            user=request.user,
            message=message,
            response=response,
            created_at=timezone.now,
        )
        chat.save()

        return JsonResponse(
            {
                "message": message,
                "response": response,
            },
        )
    return render(request, "chatbot.html", {"chats": chats})


def ask_embedding(message):
    response = get_embedding_response(message)

    return response


@login_required
def chatdocs(request):
    if request.method == "POST":
        message = request.POST.get("message")
        response = ask_embedding(message)
        response = format_to_html(response)
        chat = Chat(
            user=request.user,
            message=message,
            response=response,
            created_at=timezone.now,
        )
        chat.save()
        return JsonResponse(
            {
                "message": message,
                "response": response,
            }
        )

    return render(request, "chatdocs.html")


@login_required
def loadedfiles(request):
    try:
        documents = get_unique_sources_list()
    except:
        return render(request, "loadedfiles.html")
    # Asegurarnos que docs existe
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)

    # Manejo de carga de archivos
    if request.method == "POST" and request.FILES.get("documento_pdf"):
        archivo_pdf = request.FILES["documento_pdf"]
        # Validar que el archivo sea un pdf
        if archivo_pdf.content_type != "application/pdf":

            return render(
                request,
                "loadedfiles.html",
                {
                    "documents": documents,
                    "error_message": "Solo se permiten archivos pdf por el momento",
                },
            )
        if archivo_pdf.name in documents:
            error_message = "El archivo o nombre del pdf ya existe en la base de datos"
            return render(
                request,
                "loadedfiles.html",
                {"documents": documents, "error_message": error_message},
            )
        else:
            fs = FileSystemStorage(location=DOCS_DIR)
            archivo_nombre = fs.save(archivo_pdf.name, archivo_pdf)

            create_embedding_from_pdf(archivo_pdf.name)

            messages.success(
                request, f"El archivo '{archivo_pdf}' se ha cargado correctamente"
            )
            return redirect("loadedfiles")

    return render(
        request,
        "loadedfiles.html",
        {
            "documents": documents,
            "DOCS_URL": "media/",
        },
    )


def login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("welcome")
        else:
            error_message = "Invalid username or password"
            return render(request, "login.html", {"error_message": error_message})
    else:
        return render(request, "login.html")


@login_required
def blog(request):
    blogs = Blog.objects.all()

    if request.method == "POST":
        title = request.POST.get("title")
        message = request.POST.get("message")

        if title and message:  # Verificar que los valores existan
            blog = Blog(
                user=request.user,
                title=title,
                post=message,
                created_at=timezone.now(),  # Asegúrate de llamar la función
            )
            blog.save()
            title = f"{request.user} - {title}"
            convert_text_to_pdf(title, message)
            new_pdf_name = title + ".pdf"
            create_embedding_from_pdf(new_pdf_name)

            return JsonResponse(
                {
                    "message": message,
                    "title": title,
                    "response": f"Tu Post se ha almacenado correctamente. Titulo:\n{title}\nContenido:\n<br>{message}",
                }
            )

        # En caso de que falten datos, envía una respuesta de error
        return JsonResponse({"error": "Faltan datos en el formulario."}, status=400)

    return render(request, "blog.html", {"blogs": blogs})


@user_passes_test(is_admin)
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]
        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect("chatbot")
            except:
                error_message = "Error creating account"
                return render(
                    request, "register.html", {"error_message": error_message}
                )
        else:
            error_message = "Password dont match"
            return render(request, "register.html", {"error_message": error_message})
    return render(request, "register.html")


def logout(request):
    auth.logout(request)
    return redirect("login")


# Listar pdfs
def list_pdfs(request):
    # Obtener la lista de archivos PDF en la carpeta docs/
    pdf_dir = settings.MEDIA_ROOT
    try:
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    except FileNotFoundError:
        pdf_files = []

    return render(request, "list_pdfs.html", {"pdf_files": pdf_files})


def view_pdf(request, filename):
    # Verifica que el archivo PDF existe
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if not os.path.exists(file_path):
        raise Http404("El archivo no existe")

    # Renderiza una plantilla que cargue el PDF
    return render(request, "view_pdf.html", {"pdf_url": settings.MEDIA_URL + filename})
