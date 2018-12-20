from django.contrib import admin
from .models import Clipping, User_Clipping, Book

admin.site.register(Clipping)
admin.site.register(Book)
admin.site.register(User_Clipping)