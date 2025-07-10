from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from app.models import Debat, Argument, Reponse
from django.test import Client



class DebatFlashE2ETest(StaticLiveServerTestCase):
    """Test E2E complet pour un parcours utilisateur avec débat Flash"""
    
    def setUp(self):
        """Configuration initiale"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='userflash', 
            password='passwordflash'
        )
    
    def test_parcours_complet_debat_flash(self):
        """Test E2E d'un parcours utilisateur complet avec débat Flash"""
        # 1. Connexion de l'utilisateur
        response = self.client.post(reverse('login'), {
            'username': 'userflash',
            'password': 'passwordflash'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('Bienvenue' in str(m) for m in response.context['messages']))
        
        # 2. Accès à la page de création de débat
        response = self.client.get(reverse('create_debat'))
        self.assertEqual(response.status_code, 200)
        
        # 3. Accès à la page de création de débat Flash
        response = self.client.get(reverse('create_debat_standard'))
        self.assertEqual(response.status_code, 200)
        
        # 4. Création d'un débat Flash
        response = self.client.post(reverse('save_debat_standard'), {
            'titre': 'Débat Flash E2E Simplifié',
            'description': 'Description du débat Flash pour test E2E simplifié'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Récupérer le débat créé
        debat = Debat.objects.get(titre='Débat Flash E2E Simplifié')
        self.assertIsNotNone(debat)
        
        # 5. Accès au débat créé
        response = self.client.get(reverse('debat_details', args=[debat.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Débat Flash E2E Simplifié')
        
        # 6. Ajout d'un argument "pour"
        response = self.client.post(reverse('debat_details', args=[debat.id]), {
            'titre_argument': 'Argument pour - Flash',
            'contenu_argument': 'Contenu de l\'argument pour le débat Flash',
            'position_argument': 'True'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'argument a été créé
        arg_pour = Argument.objects.get(titre_argument='Argument pour - Flash')
        self.assertIsNotNone(arg_pour)
        
        # 7. Ajout d'un argument "contre"
        response = self.client.post(reverse('debat_details', args=[debat.id]), {
            'titre_argument': 'Argument contre - Flash',
            'contenu_argument': 'Contenu de l\'argument contre le débat Flash',
            'position_argument': 'False'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'argument a été créé
        arg_contre = Argument.objects.get(titre_argument='Argument contre - Flash')
        self.assertIsNotNone(arg_contre)
        
        # 8. Ajout d'une réponse à l'argument "pour"
        response = self.client.post(reverse('debat_details', args=[debat.id]), {
            'argument_id': arg_pour.id,
            'contenu_reponse': 'Réponse à l\'argument pour',
            'position_reponse': 'False'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la réponse a été créée
        reponse = Reponse.objects.get(contenu_reponse='Réponse à l\'argument pour')
        self.assertIsNotNone(reponse)
        
        # 9. Vote sur un argument
        response = self.client.post(reverse('debat_details', args=[debat.id]), {
            'vote_type': 'like',
            'element_type': 'argument',
            'element_id': arg_pour.id
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le vote a été enregistré
        arg_pour.refresh_from_db()
        self.assertEqual(arg_pour.score_argument, 1)
        self.assertIn(self.user, arg_pour.users_voted.all())

        # 10. Retour à la liste des débats en cours
        response = self.client.get(reverse('debats_en_cours'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Débat Flash E2E Simplifié')
        
        # 11. Déconnexion
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)


class DebatThinktreeE2ETest(StaticLiveServerTestCase):
    """Test E2E complet pour un parcours utilisateur avec débat Thinktree"""
    
    def setUp(self):
        """Configuration initiale"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='usertree', 
            password='passwordtree'
        )
        
    def test_parcours_complet_debat_thinktree(self):
        """Test E2E d'un parcours utilisateur complet avec débat Thinktree"""
        # 1. Connexion de l'utilisateur
        response = self.client.post(reverse('login'), {
            'username': 'usertree',
            'password': 'passwordtree'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('Bienvenue' in str(m) for m in response.context['messages']))
        
        # 2. Accès à la page de création de débat
        response = self.client.get(reverse('create_debat'))
        self.assertEqual(response.status_code, 200)
        
        # 3. Accès à la page de création de débat Thinktree
        response = self.client.get(reverse('create_debat_kialo'))
        self.assertEqual(response.status_code, 200)
        
        # 4. Création d'un débat Thinktree
        response = self.client.post(reverse('save_debat_kialo'), {
            'titre': 'Débat Thinktree E2E Simplifié',
            'contenu_argument': 'Question initiale du débat Thinktree simplifié'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Récupérer le débat créé
        debat = Debat.objects.get(titre='Débat Thinktree E2E Simplifié')
        self.assertIsNotNone(debat)
        self.assertIsNotNone(debat.racine_id)
        
        # 5. Accès au débat créé
        response = self.client.get(reverse('debat_details', args=[debat.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Débat Thinktree E2E Simplifié')
        self.assertContains(response, 'Question initiale du débat Thinktree simplifié')
        
        # 6. Ajout d'un argument "pour"
        response = self.client.post(reverse('debat_details', args=[debat.id]), {
            'contenu_argument': 'Argument pour - Thinktree',
            'parent_id': debat.racine_id.id,
            'relation': '1.0'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'argument a été créé
        arg_pour = Argument.objects.get(contenu_argument='Argument pour - Thinktree')
        self.assertIsNotNone(arg_pour)
        self.assertEqual(arg_pour.relation, 1.0)
        
        # 7. Ajout d'un argument "contre" lié au parent
        response = self.client.post(reverse('debat_details', args=[debat.id]), {
            'contenu_argument': 'Argument contre - Thinktree',
            'parent_id': debat.racine_id.id,
            'relation': '-1.0'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'argument a été créé
        arg_contre = Argument.objects.get(contenu_argument='Argument contre - Thinktree')
        self.assertIsNotNone(arg_contre)
        self.assertEqual(arg_contre.relation, -1.0)
        
        # 8. Navigation vers un argument spécifique (changer le focus)
        response = self.client.get(f"{reverse('debat_details', args=[debat.id])}?focus={arg_pour.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Argument pour - Thinktree')
        
        # 9. Ajout d'un argument de troisième niveau
        response = self.client.post(reverse('debat_details', args=[debat.id]), {
            'contenu_argument': 'Argument de niveau 3',
            'parent_id': arg_pour.id,
            'relation': '-1.0'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'argument a été créé
        arg_niveau3 = Argument.objects.get(contenu_argument='Argument de niveau 3')
        self.assertIsNotNone(arg_niveau3)
        self.assertEqual(arg_niveau3.parent_id, arg_pour)
        
        # 10. Vote sur un argument
        response = self.client.post(reverse('debat_details', args=[debat.id]), {
            'vote_type': 'like',
            'element_id': arg_pour.id
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le vote a été enregistré
        arg_pour.refresh_from_db()
        self.assertEqual(arg_pour.upvotes, 1)
        self.assertIn(self.user, arg_pour.users_voted.all())
        
        # 11. Retour à la racine du débat
        response = self.client.get(reverse('debat_details', args=[debat.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Question initiale du débat Thinktree simplifié')
        
        # 12. Retour à la liste des débats en cours
        response = self.client.get(reverse('debats_en_cours'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Débat Thinktree E2E Simplifié')
        
        # 13. Déconnexion
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)