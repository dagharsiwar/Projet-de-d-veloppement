import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User  # Import du User de Django


class Debat(models.Model):
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    ]
    TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('kialo', 'Kialo'),
    ]

    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)  # Optionnel pour type Kialo
    auteur_debat = models.ForeignKey(User, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='en_cours')
    type_debat = models.CharField(max_length=10, choices=TYPE_CHOICES, default='standard')
    racine_id = models.ForeignKey('Argument', on_delete=models.SET_NULL, null=True, blank=True, related_name='debat_racine')

    def __str__(self):
        return self.titre

    def get_description(self):
        """Retourne la description du débat (contenu de l'argument racine pour Kialo)"""
        if self.type_debat == 'kialo' and self.racine_id:
            return self.racine_id.contenu_argument
        return self.description or ""

class Argument(models.Model): # Argument pour un debat
    debat_id = models.ForeignKey(Debat, on_delete=models.CASCADE)
    auteur_argument = models.ForeignKey(User, on_delete=models.CASCADE)
    titre_argument = models.CharField(max_length=200, blank=True, null=True)  # Obligatoire pour standard, optionnel pour kialo
    contenu_argument = models.TextField()
    score_argument = models.IntegerField(default=0)
    
    # Champs pour débat standard
    position_argument = models.BooleanField(null=True, blank=True)  # True argument pour, False argument contre
    
    # Champs pour débat kialo
    relation = models.FloatField(null=True, blank=True)  # 1.0: pour, -1.0: contre, null pour les racines
    parent_id = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='reponses')
    est_racine = models.BooleanField(default=False)
    quad_score = models.FloatField(default=0.5)  # Score calculé par l'algorithme Kialo
    upvotes = models.IntegerField(default=0)  # Nombre de votes positifs pour les débats Kialo
    downvotes = models.IntegerField(default=0)  # Nombre de votes négatifs pour les débats Kialo
    
    date_argument = models.DateTimeField(auto_now_add=True)
    users_voted = models.ManyToManyField(User, related_name='votes_arguments', blank=True)

    def __str__(self):
        if self.titre_argument:
            return self.titre_argument
        return self.contenu_argument[:50]  # Retourne les 50 premiers caractères du contenu
    
    def update_score_argument(self):
        """Met à jour le score_argument basé sur les upvotes et downvotes"""
        self.score_argument = self.upvotes - self.downvotes
        return self.score_argument

class Reponse(models.Model): # Reponse à un argument (débat standard uniquement)
    argument_id = models.ForeignKey(Argument, on_delete=models.CASCADE)
    auteur_reponse = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu_reponse = models.TextField()
    score_reponse = models.IntegerField()
    position_reponse = models.BooleanField() # True camp pour, false camp contre
    date_reponse = models.DateTimeField(auto_now_add=True)
    users_voted = models.ManyToManyField(User, related_name='votes_reponses', blank=True)

    def __str__(self):
        return self.contenu_reponse



    