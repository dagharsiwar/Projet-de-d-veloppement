from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Debat, Argument, Reponse

# Créer un nouvel UserAdmin personnalisé
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'id', 'email', 'first_name', 'last_name', 'is_staff')
    ordering = ('username',)  # Trier par username par défaut

# Réenregistrer le User avec notre admin personnalisé
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Debat)
admin.site.register(Argument)
admin.site.register(Reponse)
