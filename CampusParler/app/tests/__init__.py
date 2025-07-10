# Module de tests pour l'application Campus Parler

"""
COMMANDE DE TEST DJANGO:
------------------------
python3 manage.py test app.tests

- 'python3 manage.py': Lance l'utilitaire de gestion Django

- 'test': Sous-commande qui active le framework de test Django et:
    * Crée une base de données temporaire isolée pour les tests
    * Configure l'environnement spécifique aux tests
    * Découvre automatiquement les tests à exécuter
    * Exécute les tests et rapporte les résultats
    * Détruit la base de données temporaire après les tests

- 'app.tests': Indique le package où chercher les tests
    * Recherche tous les fichiers commençant par test_*.py
    * Exécute toutes les classes qui héritent de TestCase
    * Suit la convention standard de Django (dossier 'tests' dans l'app)

""" 