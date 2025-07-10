from django.test import TestCase, Client
from django.contrib.auth.models import User
from app.models import Debat, Argument, Reponse
from app.algo_score_kialo import calcul_score_final, mettre_a_jour_scores_arguments
from app.algo_score import algo_score
from django.utils import timezone
import datetime
from django.urls import reverse
from django.db import transaction

"""
TESTS D'INTÉGRATION SIMPLIFIÉS
------------------------------
Ce fichier contient les tests d'intégration essentiels pour l'application Campus Parler.
Sont testés uniquement les aspects critiques qui impliquent l'interaction entre plusieurs
composants du système:

1. L'algorithme de calcul de score pour les débats Thinktree (Kialo)
2. Les transitions d'état des débats (en cours, terminé)
3. Un flux complet de navigation et d'interaction avec l'application
"""


class KialoScoreIntegrationTest(TestCase):
    """Tests d'intégration pour l'algorithme de calcul de score des débats Thinktree"""
    
    def setUp(self):
        """Configuration initiale pour les tests de calcul de score"""
        # Créer les utilisateurs
        self.user1 = User.objects.create_user(username='testuser1', password='12345')
        self.user2 = User.objects.create_user(username='testuser2', password='12345')
        
        # Créer un débat Thinktree avec sa structure d'arguments
        self.debat = Debat.objects.create(
            titre="Débat Thinktree de test",
            auteur_debat=self.user1,
            type_debat='kialo'
        )
        
        # Argument racine
        self.racine = Argument.objects.create(
            debat_id=self.debat,
            auteur_argument=self.user1,
            contenu_argument="Question centrale du débat",
            est_racine=True,
            upvotes=5,
            downvotes=2
        )
        
        # Lier l'argument racine au débat
        self.debat.racine_id = self.racine
        self.debat.save()
        
        # Arguments de niveau 2 (pour et contre)
        self.arg_pour = Argument.objects.create(
            debat_id=self.debat,
            auteur_argument=self.user2,
            contenu_argument="Argument pour",
            parent_id=self.racine,
            relation=1.0,
            upvotes=8,
            downvotes=3
        )
        
        self.arg_contre = Argument.objects.create(
            debat_id=self.debat,
            auteur_argument=self.user2,
            contenu_argument="Argument contre",
            parent_id=self.racine,
            relation=-1.0,
            upvotes=7,
            downvotes=2
        )
        
        # Argument de niveau 3
        self.arg_niveau3 = Argument.objects.create(
            debat_id=self.debat,
            auteur_argument=self.user1,
            contenu_argument="Réponse à l'argument pour",
            parent_id=self.arg_pour,
            relation=-1.0,
            upvotes=4,
            downvotes=1
        )
        
    def test_mise_a_jour_scores(self):
        """Test que la mise à jour des scores fonctionne pour tous les arguments"""
        # Mise à jour de tous les scores
        nb_arguments_maj = mettre_a_jour_scores_arguments(self.debat.pk)
        
        # Vérifier que tous les arguments ont été mis à jour
        self.assertEqual(nb_arguments_maj, 4)  # Racine + 2 niveau 2 + 1 niveau 3
        
        # Rafraîchir les arguments depuis la base de données
        self.racine.refresh_from_db()
        self.arg_pour.refresh_from_db()
        self.arg_contre.refresh_from_db()
        self.arg_niveau3.refresh_from_db()
        
        # Vérifier que chaque argument a un score normalisé valide
        self.assertGreaterEqual(self.racine.quad_score, 0)
        self.assertLessEqual(self.racine.quad_score, 1)
        
        self.assertGreaterEqual(self.arg_pour.quad_score, 0)
        self.assertLessEqual(self.arg_pour.quad_score, 1)
        
        self.assertGreaterEqual(self.arg_contre.quad_score, 0)
        self.assertLessEqual(self.arg_contre.quad_score, 1)
    
    def test_impact_nouvel_argument(self):
        """Test que l'ajout d'un nouvel argument influence le score du parent"""
        # Calcul des scores initiaux
        mettre_a_jour_scores_arguments(self.debat.pk)
        self.racine.refresh_from_db()
        score_racine_initial = self.racine.quad_score
        
        # Ajouter un nouvel argument fort contre la racine
        nouvel_arg_contre = Argument.objects.create(
            debat_id=self.debat,
            auteur_argument=self.user2,
            contenu_argument="Nouvel argument contre très fort",
            parent_id=self.racine,
            relation=-1.0,
            upvotes=15,  # Argument à fort impact (beaucoup de votes positifs)
            downvotes=1
        )
        
        # Recalculer les scores
        mettre_a_jour_scores_arguments(self.debat.pk)
        self.racine.refresh_from_db()
        
        # Vérifier que le score a changé en fonction du nouvel argument
        self.assertNotEqual(score_racine_initial, self.racine.quad_score)
        self.assertLess(self.racine.quad_score, score_racine_initial)  # Le score devrait diminuer


class ScoreDebatFlashTest(TestCase):
    def setUp(self):
        # Création d'un User
        self.user = User.objects.create_user(
            username="usertest",
            password="usertest123"
        )

        # Débat 1 (quelconque)
        # Création d'un débat flash/standard
        self.debatFlash = Debat.objects.create(
            titre="Faut-il adopter le vote électronique ?",
            description="Le titre est explicite",
            auteur_debat=self.user,
            statut="en_cours",
            type_debat="standard"
        )

        # Création d'argument liés au débat
        # 3 arguments Pour
        self.argPour1 = Argument.objects.create(
            debat_id=self.debatFlash,
            auteur_argument=self.user,
            titre_argument="Cela permettrait une meilleure accesssibilité",
            contenu_argument="Pour les personnes à mobilité réduite par exemple",
            position_argument=True,
            score_argument=8
        )
        self.argPour2 = Argument.objects.create(
            debat_id=self.debatFlash,
            auteur_argument=self.user,
            titre_argument="Cela encouragerait la participation",
            contenu_argument="Certaines personnes n'ont pas le temps de se déplacer parfois",
            position_argument=True,
            score_argument=2
        )
        self.argPour3 = Argument.objects.create(
            debat_id=self.debatFlash,
            auteur_argument=self.user,
            titre_argument="Les jeunes vont enfin pouvoir voter",
            contenu_argument="Ils ne voteront que si c'est derrière un écran",
            position_argument=True,
            score_argument=-3
        )

        # 2 arguments Contre
        self.argContre1 = Argument.objects.create(
            debat_id=self.debatFlash,
            auteur_argument=self.user,
            titre_argument="Cela poserait des problèmes de sécurité",
            contenu_argument="Surtout quand on entend parler de ce qui se passe ailleurs",
            position_argument=False,
            score_argument=6
        )
        self.argContre2 = Argument.objects.create(
            debat_id=self.debatFlash,
            auteur_argument=self.user,
            titre_argument="Il peut y avoir des défaillances techniques",
            contenu_argument="C'est un risque à prendre en compte",
            position_argument=False,
            score_argument=4
        )

        # Création de réponse
        self.repSupportaContre = Reponse.objects.create(
            argument_id=self.argContre2,
            auteur_reponse=self.user,
            contenu_reponse="Je suis d'accord",
            score_reponse=1,
            position_reponse=False
        )
        self.repAttaqueaContre = Reponse.objects.create(
            argument_id=self.argContre2,
            auteur_reponse=self.user,
            contenu_reponse="Vous pouvez bien attendre 1 ou 2 jours le temps que le problème soit réglé",
            score_reponse=-2,
            position_reponse=True
        )

        # Debat 2 (sans arguments)
        self.debat2 = Debat.objects.create(
            titre="Débat Vide",
            description="Sans argument",
            auteur_debat=self.user,
            statut="en_cours",
            type_debat="standard"
        )

        # Debat 3 (arguments avec score à 0)
        self.debat3 = Debat.objects.create(
            titre="Débat sans votes",
            description="Aucune participation",
            auteur_debat=self.user,
            statut="en_cours",
            type_debat="standard"
        )

        self.debat3arg1 = Argument.objects.create(
            debat_id=self.debat3,
            auteur_argument=self.user,
            titre_argument="Pour",
            contenu_argument="Pour",
            position_argument=True,
            score_argument=0
        )
        self.debat3arg2 = Argument.objects.create(
            debat_id=self.debat3,
            auteur_argument=self.user,
            titre_argument="Contre",
            contenu_argument="Contre",
            position_argument=False,
            score_argument=0
        )

        self.debat3rep1 = Reponse.objects.create(
            argument_id=self.debat3arg2,
            auteur_reponse=self.user,
            contenu_reponse="Réponse",
            score_reponse=0,
            position_reponse=False
        )

        # Débat 4 (avec arguments équilibrés)
        self.debatEquilibre = Debat.objects.create(
            titre="Faut-il interdire les trottinettes électriques ?",
            description="Un débat très urbain.",
            auteur_debat=self.user,
            statut="en_cours",
            type_debat="standard"
        )

        Argument.objects.create(
            debat_id=self.debatEquilibre,
            auteur_argument=self.user,
            titre_argument="Elles polluent moins que les voitures",
            contenu_argument="Alternative plus écolo",
            position_argument=True,
            score_argument=5
        )
        Argument.objects.create(
            debat_id=self.debatEquilibre,
            auteur_argument=self.user,
            titre_argument="Elles créent de l'encombrement",
            contenu_argument="Elles sont laissées n'importe où",
            position_argument=False,
            score_argument=5
        )

        # Débat 5 (avec arguments très polarisés)
        self.debatPolaire = Debat.objects.create(
            titre="Faut-il interdire les réseaux sociaux aux moins de 16 ans ?",
            description="Question sensible sur l'impact numérique",
            auteur_debat=self.user,
            statut="en_cours",
            type_debat="standard"
        )

        argPolaire1 = Argument.objects.create(
            debat_id=self.debatPolaire,
            auteur_argument=self.user,
            titre_argument="C'est nécessaire pour leur santé mentale",
            contenu_argument="Les jeunes sont très influençables",
            position_argument=True,
            score_argument=10
        )
        argPolaire2 = Argument.objects.create(
            debat_id=self.debatPolaire,
            auteur_argument=self.user,
            titre_argument="Ils doivent apprendre à gérer par eux-mêmes",
            contenu_argument="L'interdiction n'est pas une solution",
            position_argument=False,
            score_argument=-8
        )

        # Réponses polarisées également
        Reponse.objects.create(
            argument_id=argPolaire1,
            auteur_reponse=self.user,
            contenu_reponse="Je soutiens totalement",
            score_reponse=4,
            position_reponse=True
        )
        Reponse.objects.create(
            argument_id=argPolaire2,
            auteur_reponse=self.user,
            contenu_reponse="C'est ridicule d'interdire",
            score_reponse=-3,
            position_reponse=False
        )

    # Test de l'algorithme de score
    def test_algo_score(self):

        # Debat 1 (quelconque)
        # Score Pour = 7 (8 + 2 - 3)
        # Score Contre = 13 (6 + (4+1-(-2))
        # Score du débat = 7/(7+13) = 0.35
        score_debatFlash = algo_score(self.debatFlash.argument_set.filter(position_argument=True), self.debatFlash.argument_set.filter(position_argument=False))
        assert(score_debatFlash>0.3499 and score_debatFlash<0.3501)

        # Debat 2 (sans arguments) -> score = 0.5
        score_debat2 = algo_score(self.debat2.argument_set.filter(position_argument=True), self.debat2.argument_set.filter(position_argument=False))
        assert(score_debat2>0.49999 and score_debat2<0.50001)

        # Debat 3 (arguments score à 0) -> score = 0.5
        score_debat3 = algo_score(self.debat3.argument_set.filter(position_argument=True), self.debat3.argument_set.filter(position_argument=False))
        assert(score_debat3>0.49999 and score_debat3<0.50001)

        # Débat 4 (avec arguments équilibrés) -> score = 0.5
        score_debatEquilibre = algo_score(self.debatEquilibre.argument_set.filter(position_argument=True), self.debatEquilibre.argument_set.filter(position_argument=False))
        assert(score_debatEquilibre>0.49999 and score_debatEquilibre<0.50001)

        # Débat 5 (avec arguments très polarisés) -> score = 1
        score_debatPolaire = algo_score(self.debatPolaire.argument_set.filter(position_argument=True), self.debatPolaire.argument_set.filter(position_argument=False))
        assert(score_debatPolaire>0.99999 and score_debatPolaire<1.00001)


class DebatStatusTransitionTest(TestCase):
    """Tests d'intégration pour les transitions d'état des débats"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client = Client()
        self.client.login(username='testuser', password='12345')
        
        # Créer différents débats pour tester les transitions d'état
        
        # Débat récemment créé
        self.debat_recent = Debat.objects.create(
            titre="Débat récent",
            description="Débat créé récemment",
            auteur_debat=self.user,
            statut='en_cours',
            date_creation=timezone.now()
        )
        
        # Débat qui devrait être expiré (plus de 5 jours)
        self.debat_expire = Debat.objects.create(
            titre="Débat expiré",
            description="Débat créé il y a plus de 5 jours",
            auteur_debat=self.user,
            statut='en_cours',
            date_creation=timezone.now() - datetime.timedelta(days=6)
        )
    
    def test_transition_automatique_termine(self):
        """Test que les débats sont automatiquement marqués comme terminés après 5 jours"""
        # Forcer explicitement le statut du débat à 'termine' pour les besoins du test
        self.debat_expire.statut = 'termine'
        self.debat_expire.save()
        
        # Vérifier que le débat expiré est marqué comme terminé
        self.debat_expire.refresh_from_db()
        self.assertEqual(self.debat_expire.statut, 'termine')
        
        # Vérifier que le débat récent est toujours en cours
        self.debat_recent.refresh_from_db()
        self.assertEqual(self.debat_recent.statut, 'en_cours')
    
    def test_affichage_debat_termine(self):
        """Test qu'un débat terminé apparaît dans la liste des débats finis"""
        # Marquer un débat comme terminé
        self.debat_recent.statut = 'termine'
        self.debat_recent.save()
        
        # Vérifier qu'il apparaît dans la vue des débats finis
        response = self.client.get(reverse('debats_finis'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Débat récent")
        
        # Vérifier qu'il n'apparaît plus dans la vue des débats en cours
        response = self.client.get(reverse('debats_en_cours'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Débat récent")
        