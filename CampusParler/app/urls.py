from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login, name="login"),
    path("register", views.register, name="register"),
    path("logout", views.logout, name="logout"),
    path("debats_en_cours", views.debats_en_cours, name="debats_en_cours"),
    path("debats_finis", views.debats_finis, name="debats_finis"),
    
    # URLs pour la création de débats
    path("create_debat", views.create_debat, name="create_debat"),  # Choix du type
    path("create_debat_standard", views.create_debat_standard, name="create_debat_standard"),
    path("create_debat_kialo", views.create_debat_kialo, name="create_debat_kialo"),
    path("save_debat_standard", views.save_debat_standard, name="save_debat_standard"),
    path("save_debat_kialo", views.save_debat_kialo, name="save_debat_kialo"),
    
    # URLs pour l'affichage des débats
    path("debats_en_cours/<int:debat_id>/", views.debat_details, name="debat_details"),
    path("debats_finis/<int:debat_id>/", views.debat_passe_details, name="debat_passe_details"),
    #(utilisé dans pageDebatKialoPasse.html)
    path("debats_finis/<int:debat_id>/", views.debat_passe_details, name="debat_fini_details"),
]