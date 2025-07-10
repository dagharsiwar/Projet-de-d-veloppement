from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from app.models import Debat, Argument, Reponse
from django.utils import timezone
import datetime
from django.db import transaction

"""
TESTS UNITAIRES SIMPLIFIÉS - VUES
---------------------------------
Ce fichier contient les tests unitaires essentiels pour les vues de l'application.
Les tests sont concentrés sur les fonctionnalités critiques de chaque type de vue:

1. Vues d'authentification (inscription, connexion)
2. Vues de débats Flash (création, affichage, interaction)
3. Vues de débats Thinktree (création, affichage, interaction)
4. Vues de gestion des arguments et votes
"""

class AuthViewsTest(TestCase):
    """Tests des vues d'authentification"""
    
    def setUp(self):
        """Configuration pour les tests d'authentification"""
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.home_url = reverse('index')
        
        # Créer un utilisateur pour les tests de connexion
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_inscription_utilisateur(self):
        """Test d'inscription d'un nouvel utilisateur"""
        # Données d'inscription
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complex_password123',
            'password2': 'complex_password123'
        }
        
        # Soumettre le formulaire d'inscription
        response = self.client.post(self.register_url, data, follow=True)
        
        # Vérifier que l'utilisateur a été créé et redirigé correctement
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertRedirects(response, self.home_url)
    
    def test_connexion_utilisateur(self):
        """Test de connexion d'un utilisateur existant"""
        # Données de connexion
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        # Soumettre le formulaire de connexion
        response = self.client.post(self.login_url, data, follow=True)
        
        # Vérifier que l'utilisateur est connecté et redirigé correctement
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertRedirects(response, self.home_url)


class DebatFlashViewsTest(TestCase):
    """Tests des vues pour les débats Flash/Standard"""
    
    def setUp(self):
        """Configuration pour les tests de débats Flash"""
        self.client = Client()
        
        # Créer un utilisateur et le connecter
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # URLs utiles
        self.create_debat_url = reverse('save_debat_standard')
        self.debats_en_cours_url = reverse('debats_en_cours')
        
        # Créer un débat pour les tests
        self.debat = Debat.objects.create(
            titre="Débat Flash test",
            description="Description du débat Flash",
            auteur_debat=self.user,
            type_debat='standard'
        )
        self.debat_detail_url = reverse('debat_details', args=[self.debat.id])
    
    def test_creation_debat_flash(self):
        """Test de création d'un débat Flash"""
        # Données du formulaire
        data = {
            'titre': 'Nouveau débat Flash',
            'description': 'Description du nouveau débat Flash'
        }
        
        # Soumettre le formulaire de création
        response = self.client.post(self.create_debat_url, data, follow=True)
        
        # Vérifier que le débat a été créé et redirigé correctement
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Debat.objects.filter(titre='Nouveau débat Flash').exists())
        
        # Vérifier les propriétés du débat créé
        debat = Debat.objects.get(titre='Nouveau débat Flash')
        self.assertEqual(debat.description, 'Description du nouveau débat Flash')
        self.assertEqual(debat.auteur_debat, self.user)
        self.assertEqual(debat.type_debat, 'standard')
    
    def test_affichage_details_debat_flash(self):
        """Test d'affichage des détails d'un débat Flash"""
        # Accéder à la page de détails du débat
        response = self.client.get(self.debat_detail_url)
        
        # Vérifier que la page s'affiche correctement
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Débat Flash test")
        self.assertContains(response, "Description du débat Flash")
        
        # Vérifier que le contexte contient les données nécessaires
        self.assertEqual(response.context['debat'], self.debat)
    
    def test_ajout_argument_debat_flash(self):
        """Test d'ajout d'un argument à un débat Flash"""
        # Données du formulaire d'argument
        data = {
            'titre_argument': 'Titre argument test',
            'contenu_argument': 'Contenu de l\'argument test',
            'position_argument': 'true'  # Position "pour"
        }
        
        # Soumettre le formulaire d'ajout d'argument
        response = self.client.post(self.debat_detail_url, data, follow=True)
        
        # Vérifier que l'argument a été créé
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Argument.objects.filter(titre_argument='Titre argument test').exists())
        
        # Vérifier les propriétés de l'argument créé
        argument = Argument.objects.get(titre_argument='Titre argument test')
        self.assertEqual(argument.contenu_argument, 'Contenu de l\'argument test')
        self.assertEqual(argument.debat_id, self.debat)
        self.assertEqual(argument.auteur_argument, self.user)
        self.assertFalse(argument.position_argument)
    
    def test_vote_sur_argument(self):
        """Test de vote sur un argument"""
        # Créer un argument pour tester le vote
        argument = Argument.objects.create(
            debat_id=self.debat,
            auteur_argument=self.user,
            titre_argument='Argument pour tester le vote',
            contenu_argument='Contenu de l\'argument',
            position_argument=True
        )
        
        # Données du formulaire de vote
        data = {
            'vote_type': 'like',
            'element_id': argument.id
        }
        
        # Soumettre le vote
        response = self.client.post(self.debat_detail_url, data, follow=True)
        
        # Vérifier que la requête a réussi
        self.assertEqual(response.status_code, 200)


class DebatThinktreeViewsTest(TestCase):
    """Tests des vues pour les débats Thinktree/Kialo"""
    
    def setUp(self):
        """Configuration pour les tests de débats Thinktree"""
        self.client = Client()
        
        # Créer un utilisateur et le connecter
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # URLs utiles
        self.create_debat_url = reverse('save_debat_kialo')
        self.debats_en_cours_url = reverse('debats_en_cours')
        
        # Créer un débat Thinktree avec son argument racine
        self.debat = Debat.objects.create(
            titre="Débat Thinktree test",
            auteur_debat=self.user,
            type_debat='kialo'
        )
        
        # Créer l'argument racine
        self.racine = Argument.objects.create(
            debat_id=self.debat,
            auteur_argument=self.user,
            contenu_argument="Question centrale du débat Thinktree",
            est_racine=True
        )
        
        # Associer l'argument racine au débat
        self.debat.racine_id = self.racine
        self.debat.save()
        
        self.debat_detail_url = reverse('debat_details', args=[self.debat.id])
    
    def test_creation_debat_thinktree(self):
        """Test de création d'un débat Thinktree"""
        # Données du formulaire
        data = {
            'titre': 'Nouveau débat Thinktree',
            'contenu_argument': 'Question centrale du nouveau débat'
        }
        
        # Soumettre le formulaire de création
        response = self.client.post(self.create_debat_url, data, follow=True)
        
        # Vérifier que le débat a été créé et redirigé correctement
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Debat.objects.filter(titre='Nouveau débat Thinktree').exists())
        
        # Vérifier les propriétés du débat et de son argument racine
        debat = Debat.objects.get(titre='Nouveau débat Thinktree')
        self.assertEqual(debat.type_debat, 'kialo')
        self.assertEqual(debat.auteur_debat, self.user)
        self.assertIsNotNone(debat.racine_id)
        self.assertEqual(debat.racine_id.contenu_argument, 'Question centrale du nouveau débat')
    
    def test_affichage_details_debat_thinktree(self):
        """Test d'affichage des détails d'un débat Thinktree"""
        # Accéder à la page de détails du débat
        response = self.client.get(self.debat_detail_url)
        
        # Vérifier que la page s'affiche correctement
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Débat Thinktree test")
        self.assertContains(response, "Question centrale du débat Thinktree")
        
        # Vérifier que le contexte contient les données nécessaires
        self.assertEqual(response.context['debat'], self.debat)
        self.assertEqual(response.context['racine'], self.racine)
    
    def test_ajout_argument_thinktree(self):
        """Test d'ajout d'un argument à un débat Thinktree"""
        # Données du formulaire d'argument
        data = {
            'contenu_argument': 'Argument en réponse à la question centrale',
            'parent_id': self.racine.id,
            'relation': '1.0'  # Relation "pour"
        }
        
        # Soumettre le formulaire d'ajout d'argument
        response = self.client.post(self.debat_detail_url, data, follow=True)
        
        # Vérifier que l'argument a été créé
        self.assertEqual(response.status_code, 200)
        
        # Vérifier l'argument créé
        argument = Argument.objects.get(
            contenu_argument='Argument en réponse à la question centrale',
            parent_id=self.racine
        )
        self.assertEqual(argument.debat_id, self.debat)
        self.assertEqual(argument.auteur_argument, self.user)
        self.assertEqual(argument.relation, 1.0)
    
        # Vérifier que l'argument n'est pas une racine
        self.assertFalse(argument.est_racine)


class ListesDebatsViewsTest(TestCase):
    """Tests des vues de listes de débats"""
    
    def setUp(self):
        """Configuration pour les tests de listes de débats"""
        self.client = Client()
        
        # Créer un utilisateur et le connecter
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # URLs utiles
        self.debats_en_cours_url = reverse('debats_en_cours')
        self.debats_finis_url = reverse('debats_finis')
        self.mes_debats_url = reverse('debats_en_cours')
        
        # Créer des débats avec différents statuts
        self.debat_en_cours = Debat.objects.create(
            titre="Débat en cours",
            description="Description du débat en cours",
            auteur_debat=self.user,
            statut='en_cours'
        )
        
        self.debat_termine = Debat.objects.create(
            titre="Débat terminé",
            description="Description du débat terminé",
            auteur_debat=self.user,
            statut='termine'
        )
        
        # Créer un autre utilisateur et un débat associé
        self.autre_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        self.debat_autre_user = Debat.objects.create(
            titre="Débat d'un autre utilisateur",
            description="Description du débat d'un autre utilisateur",
            auteur_debat=self.autre_user,
            statut='en_cours'
        )
    
    def test_liste_debats_en_cours(self):
        """Test de la vue de liste des débats en cours"""
        # Accéder à la liste des débats en cours
        response = self.client.get(self.debats_en_cours_url)
        
        # Vérifier que la page s'affiche correctement
        self.assertEqual(response.status_code, 200)
        
        # Vérifier les débats via le contexte uniquement
        self.assertIn(self.debat_en_cours, response.context['debats'])
        self.assertIn(self.debat_autre_user, response.context['debats'])
        self.assertNotIn(self.debat_termine, response.context['debats'])
    
    def test_liste_debats_finis(self):
        """Test de la vue de liste des débats terminés"""
        # Accéder à la liste des débats terminés
        response = self.client.get(self.debats_finis_url)
        
        # Vérifier que la page s'affiche correctement
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que les débats terminés sont inclus
        self.assertContains(response, "Débat terminé")
        
        # Vérifier que les débats en cours ne sont pas inclus
        self.assertNotContains(response, "Débat en cours")
        self.assertNotContains(response, "Débat d'un autre utilisateur")
        
        # Vérifier que le contexte contient les bons débats
        self.assertIn(self.debat_termine, response.context['debats'])
        self.assertNotIn(self.debat_en_cours, response.context['debats'])
        self.assertNotIn(self.debat_autre_user, response.context['debats'])
    
    def test_liste_mes_debats(self):
        """Test de la vue de liste des débats de l'utilisateur connecté"""
        # Accéder à la liste de mes débats
        response = self.client.get(self.mes_debats_url)
        
        # Vérifier que la page s'affiche correctement
        self.assertEqual(response.status_code, 200)
        
        
        self.assertIn(self.debat_en_cours, response.context['debats'])
        self.assertIn(self.debat_autre_user, response.context['debats'])
        self.assertNotIn(self.debat_termine, response.context['debats'])
        