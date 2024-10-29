from django.contrib import admin

from .models import Blog, Chat

# Register your models here.
admin.site.register(Chat)
admin.site.register(Blog)
