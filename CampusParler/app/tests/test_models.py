from django.test import TestCase
from django.contrib.auth.models import User
from app.models import Debat, Argument, Reponse
from django.utils import timezone
import datetime

"""
TESTS UNITAIRES SIMPLIFIÉS - MODÈLES
------------------------------------
Ce fichier contient les tests unitaires essentiels pour les modèles de données,
concentré sur les fonctionnalités critiques de chaque modèle:

1. Débat (Flash/Standard et Thinktree/Kialo)
2. Argument
3. Réponse

Chaque test est ciblé et vérifie une seule responsabilité du modèle.
"""

class DebatTest(TestCase):
    """Tests des modèles de débat (Flash et Thinktree)"""
    
    def setUp(self):
        """Configuration commune pour les tests de débats"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_debat_flash(self):
        """Test des propriétés et méthodes du débat Flash"""
        # Créer un débat Flash
        debat_flash = Debat.objects.create(
            titre="Débat Flash test",
            description="Description du débat Flash",
            auteur_debat=self.user,
            type_debat='standard'
        )
        
        # Vérifier les propriétés de base
        self.assertEqual(debat_flash.titre, "Débat Flash test")
        self.assertEqual(debat_flash.description, "Description du débat Flash")
        self.assertEqual(debat_flash.auteur_debat, self.user)
        self.assertEqual(debat_flash.type_debat, 'standard')
        self.assertEqual(debat_flash.statut, 'en_cours')  # valeur par défaut
        
        # Vérifier la méthode get_description
        self.assertEqual(debat_flash.get_description(), "Description du débat Flash")
    
    def test_debat_thinktree(self):
        """Test des propriétés et méthodes du débat Thinktree"""
        # Créer un débat Thinktree
        debat_thinktree = Debat.objects.create(
            titre="Débat Thinktree test",
            auteur_debat=self.user,
            type_debat='kialo'
        )
        
        # Vérifier les propriétés de base
        self.assertEqual(debat_thinktree.titre, "Débat Thinktree test")
        self.assertEqual(debat_thinktree.auteur_debat, self.user)
        self.assertEqual(debat_thinktree.type_debat, 'kialo')
        
        # Créer un argument racine
        arg_racine = Argument.objects.create(
            debat_id=debat_thinktree,
            auteur_argument=self.user,
            contenu_argument="Argument racine du débat Thinktree",
            est_racine=True
        )
        
        # Associer l'argument racine au débat
        debat_thinktree.racine_id = arg_racine
        debat_thinktree.save()
        
        # Vérifier que l'association est correcte
        self.assertEqual(debat_thinktree.racine_id, arg_racine)
        self.assertTrue(arg_racine.est_racine)
        
        # Vérifier la méthode get_description
        self.assertEqual(debat_thinktree.get_description(), "Argument racine du débat Thinktree")


class ArgumentTest(TestCase):
    """Tests du modèle Argument"""
    
    def setUp(self):
        """Configuration commune pour les tests d'arguments"""
        self.user = User.objects.create_user(username='testuser', password='12345')
        
        # Créer un débat
        self.debat = Debat.objects.create(
            titre="Débat pour tester les arguments",
            description="Description du débat",
            auteur_debat=self.user
        )
    
    def test_argument_standard(self):
        """Test des propriétés et méthodes d'un argument standard"""
        # Créer un argument
        argument = Argument.objects.create(
            debat_id=self.debat,
            auteur_argument=self.user,
            titre_argument="Titre de l'argument",
            contenu_argument="Contenu de l'argument de test",
            position_argument=True  # Argument pour
        )
        
        # Vérifier les propriétés de base
        self.assertEqual(argument.titre_argument, "Titre de l'argument")
        self.assertEqual(argument.contenu_argument, "Contenu de l'argument de test")
        self.assertEqual(argument.auteur_argument, self.user)
        self.assertEqual(argument.debat_id, self.debat)
        self.assertTrue(argument.position_argument)
        self.assertEqual(argument.score_argument, 0)  # Valeur par défaut
    
    def test_argument_thinktree(self):
        """Test des propriétés et méthodes d'un argument Thinktree"""
        # Créer un débat Thinktree
        debat_thinktree = Debat.objects.create(
            titre="Débat Thinktree pour tests",
            auteur_debat=self.user,
            type_debat='kialo'
        )
        
        # Créer un argument racine
        argument_racine = Argument.objects.create(
            debat_id=debat_thinktree,
            auteur_argument=self.user,
            contenu_argument="Argument racine du débat Thinktree",
            est_racine=True
        )
        
        # Créer un argument enfant (niveau 2)
        argument_enfant = Argument.objects.create(
            debat_id=debat_thinktree,
            auteur_argument=self.user,
            contenu_argument="Argument enfant",
            parent_id=argument_racine,
            relation=1.0  # Argument pour (soutient l'argument parent)
        )
        
        # Vérifier les propriétés de base
        self.assertEqual(argument_enfant.contenu_argument, "Argument enfant")
        self.assertEqual(argument_enfant.parent_id, argument_racine)
        self.assertEqual(argument_enfant.relation, 1.0)
        
        # Vérifier que l'argument sans titre fonctionne (cas Thinktree)
        self.assertIsNone(argument_enfant.titre_argument)
    
    def test_calcul_score(self):
        """Test du calcul de score d'un argument"""
        # Créer un argument
        argument = Argument.objects.create(
            debat_id=self.debat,
            auteur_argument=self.user,
            titre_argument="Test score",
            contenu_argument="Argument pour tester le score",
            position_argument=True
        )
        
        # Définir les votes
        argument.upvotes = 10
        argument.downvotes = 3
        
        # Calculer le score
        score = argument.update_score_argument()
        
        # Vérifier le calcul
        self.assertEqual(score, 7)  # 10 - 3 = 7
        self.assertEqual(argument.score_argument, 7)
    
    def test_gestion_votes_utilisateurs(self):
        """Test de la gestion des utilisateurs qui ont voté"""
        # Créer un argument
        argument = Argument.objects.create(
            debat_id=self.debat,
            auteur_argument=self.user,
            titre_argument="Test votes",
            contenu_argument="Argument pour tester les votes",
            position_argument=True
        )
        
        # Créer des utilisateurs supplémentaires
        user2 = User.objects.create_user(username='testuser2', password='12345')
        user3 = User.objects.create_user(username='testuser3', password='12345')
        
        # Ajouter des utilisateurs qui ont voté
        argument.users_voted.add(self.user, user2)
        
        # Vérifier la relation many-to-many
        self.assertEqual(argument.users_voted.count(), 2)
        self.assertIn(self.user, argument.users_voted.all())
        self.assertIn(user2, argument.users_voted.all())
        self.assertNotIn(user3, argument.users_voted.all())


class ReponseTest(TestCase):
    """Tests du modèle Réponse"""
    
    def setUp(self):
        """Configuration commune pour les tests de réponses"""
        self.user1 = User.objects.create_user(username='testuser1', password='12345')
        self.user2 = User.objects.create_user(username='testuser2', password='12345')
        
        # Créer un débat
        self.debat = Debat.objects.create(
            titre="Débat pour tester les réponses",
            description="Description du débat",
            auteur_debat=self.user1
        )
        
        # Créer un argument
        self.argument = Argument.objects.create(
            debat_id=self.debat,
            auteur_argument=self.user1,
            titre_argument="Titre de l'argument",
            contenu_argument="Contenu de l'argument de test",
            position_argument=True
        )
    
    def test_proprietes_reponse(self):
        """Test des propriétés de base d'une réponse"""
        # Créer une réponse
        reponse = Reponse.objects.create(
            argument_id=self.argument,
            auteur_reponse=self.user2,
            contenu_reponse="Contenu de la réponse de test",
            position_reponse=False,  # Réponse contre l'argument
            score_reponse=0  # Ajout du score par défaut
        )
        
        # Vérifier les propriétés de base
        self.assertEqual(reponse.contenu_reponse, "Contenu de la réponse de test")
        self.assertEqual(reponse.auteur_reponse, self.user2)
        self.assertEqual(reponse.argument_id, self.argument)
        self.assertFalse(reponse.position_reponse)
        self.assertEqual(reponse.score_reponse, 0)  # Valeur par défaut
    
    def test_gestion_votes_reponse(self):
        """Test de la gestion des utilisateurs qui ont voté pour une réponse"""
        # Créer une réponse
        reponse = Reponse.objects.create(
            argument_id=self.argument,
            auteur_reponse=self.user2,
            contenu_reponse="Réponse pour tester les votes",
            position_reponse=True,
            score_reponse=0  # Ajout du score par défaut
        )
        
        # Ajouter un utilisateur qui a voté
        reponse.users_voted.add(self.user1)
        
        # Vérifier la relation many-to-many
        self.assertEqual(reponse.users_voted.count(), 1)
        self.assertIn(self.user1, reponse.users_voted.all()) 

        