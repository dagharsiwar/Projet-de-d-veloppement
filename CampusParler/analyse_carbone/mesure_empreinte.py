import os
import sys
import time
import pandas as pd
import requests
import random
import string
from codecarbon import EmissionsTracker

# Configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8000
BASE_URL = f'http://{SERVER_HOST}:{SERVER_PORT}'
NB_ITERATIONS = 10  # Nombre d'itérations pour obtenir une moyenne fiable
RESULTATS = []

# Chemins de fichiers
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAPPORT_CSV = os.path.join(SCRIPT_DIR, "empreinte_carbone.csv")

def creer_tracker(nom_fonction):
    """Créer un tracker d'émissions pour une fonction spécifique"""
    return EmissionsTracker(
        project_name=f"CampusParler-{nom_fonction}",
        output_file=os.path.join(SCRIPT_DIR, "emissions.csv"),
        tracking_mode="process",
        log_level="info",
        measure_power_secs=1,
        save_to_file=True
    )

def mesurer_fonction(session, nom, url, methode="GET", donnees=None):
    """Mesurer l'empreinte carbone d'une fonction via une requête HTTP"""
    print(f"Mesure de {nom}...")
    
    tracker = creer_tracker(nom)
    tracker.start()
    
    for _ in range(NB_ITERATIONS):
        if methode == "GET":
            response = session.get(f'{BASE_URL}{url}')
        else:  # POST
            response = session.post(f'{BASE_URL}{url}', data=donnees)
        
        if response.status_code != 200 and response.status_code != 302:
            print(f" Avertissement: {url} a retourné un code {response.status_code}")
        
        time.sleep(0.5)  # Pause pour éviter de surcharger le serveur mm si la c'est inutile vu que c'est une action par action d'1 seul user
    
    emissions = tracker.stop()
    RESULTATS.append({
        "fonctionnalite": nom,
        "url": url,
        "emissions_CO2_g": emissions,
        "iterations": NB_ITERATIONS
    })
    
    return emissions

def generer_chaine_aleatoire(longueur=8):
    """Générer une chaîne aléatoire pour éviter les doublons dans les tests"""
    caracteres = string.ascii_lowercase + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longueur))

def generer_rapport():
    """Générer un rapport CSV des mesures"""
    # Générer CSV
    df = pd.DataFrame(RESULTATS)
    df.to_csv(RAPPORT_CSV, index=False)
    print(f"Rapport CSV généré: {RAPPORT_CSV}")

def creer_compte_utilisateur(session):
    """Créer un compte utilisateur et mesurer l'empreinte carbone"""
    # Générer un nom d'utilisateur unique
    username = f"test_user_{generer_chaine_aleatoire()}"
    password = "testpassword123"
    
    # Mesurer l'empreinte carbone de la page d'inscription
    mesurer_fonction(session, "[PAGE] Formulaire d'inscription", "/register")
    
    # Mesurer l'empreinte carbone de la création de compte
    donnees = {
        'username': username,
        'password': password
    }
    mesurer_fonction(
        session, 
        "[ACTION] Création de compte utilisateur", 
        "/register", 
        methode="POST", 
        donnees=donnees
    )
    
    return username, password

def creer_debat_standard(session):
    """Créer un débat Flash et mesurer l'empreinte carbone"""
    print("Création d'un débat Flash pour les mesures...")
    
    # Mesurer l'affichage de la page de création
    mesurer_fonction(session, "[PAGE] Formulaire de débat Flash", "/create_debat_standard")
    
    # Créer un débat Flash
    debat_data = {
        'titre': f'Débat Flash Test {generer_chaine_aleatoire()}',
        'description': 'Ce débat est créé automatiquement pour les mesures d\'empreinte carbone'
    }
    
    # Mesurer la création du débat
    response = None
    try:
        # Mesurer la soumission du formulaire
        mesurer_fonction(
            session, 
            "[ACTION] Création d'un débat Flash", 
            "/save_debat_standard", 
            methode="POST", 
            donnees=debat_data
        )
        
        # Faire une requête directe pour obtenir l'ID du débat créé
        response = session.post(f'{BASE_URL}/save_debat_standard', data=debat_data, allow_redirects=True)
    except Exception as e:
        print(f" Erreur lors de la création du débat Flash: {e}")
        return None
    
    # Extraire l'ID du débat de la redirection
    debat_id = None
    if response and response.history:
        redirect_url = response.url
        if '/debats_en_cours/' in redirect_url:
            try:
                debat_id = redirect_url.split('/debats_en_cours/')[1].strip('/')
                print(f"Débat Flash créé avec ID: {debat_id}")
            except:
                print("Impossible d'extraire l'ID du débat de l'URL de redirection")
    
    return debat_id

def creer_debat_kialo(session):
    """Créer un débat Thinktree et mesurer l'empreinte carbone"""
    print("Création d'un débat Thinktree pour les mesures...")
    
    # Mesurer l'affichage de la page de création
    mesurer_fonction(session, "[PAGE] Formulaire de débat Thinktree", "/create_debat_kialo")
    
    # Créer un débat Thinktree
    debat_data = {
        'titre': f'Débat Thinktree Test {generer_chaine_aleatoire()}',
        'contenu_argument': 'Argument central pour le test de mesure carbone'
    }
    
    # Mesurer la création du débat
    response = None
    try:
        # Mesurer la soumission du formulaire
        mesurer_fonction(
            session, 
            "[ACTION] Création d'un débat Thinktree", 
            "/save_debat_kialo", 
            methode="POST", 
            donnees=debat_data
        )
        
        # Faire une requête directe pour obtenir l'ID du débat créé
        response = session.post(f'{BASE_URL}/save_debat_kialo', data=debat_data, allow_redirects=True)
    except Exception as e:
        print(f" Erreur lors de la création du débat Thinktree: {e}")
        return None
    
    # Extraire l'ID du débat de la redirection
    debat_id = None
    if response and response.history:
        redirect_url = response.url
        if '/debats_en_cours/' in redirect_url:
            try:
                debat_id = redirect_url.split('/debats_en_cours/')[1].strip('/')
                print(f" Débat Thinktree créé avec ID: {debat_id}")
            except:
                print(" Impossible d'extraire l'ID du débat de l'URL de redirection")
    
    return debat_id

def ajouter_argument_standard(session, debat_id):
    """Ajouter un argument à un débat Flash et mesurer l'empreinte carbone"""
    if not debat_id:
        print("Impossible d'ajouter un argument: aucun ID de débat fourni")
        return False
    
    # Mesurer l'affichage du débat avant d'ajouter un argument
    mesurer_fonction(session, "[PAGE] Affichage débat Flash", f"/debats_en_cours/{debat_id}/")
    
    # Préparer les données de l'argument
    argument_data = {
        'contenu': f'Argument de test pour mesure carbone {generer_chaine_aleatoire()}',
        'debat_id': debat_id
    }
    
    # Mesurer l'ajout de l'argument
    try:
        reponse_url = f"/ajouter_argument/{debat_id}/"
        mesurer_fonction(
            session, 
            "[ACTION] Ajout argument à débat Flash", 
            reponse_url, 
            methode="POST", 
            donnees=argument_data
        )
        print(f"Argument ajouté au débat Flash {debat_id}")
        return True
    except Exception as e:
        print(f"Erreur lors de l'ajout d'un argument Flash: {e}")
        return False

def ajouter_argument_kialo(session, debat_id):
    """Ajouter un argument à un débat Thinktree et mesurer l'empreinte carbone"""
    if not debat_id:
        print("Impossible d'ajouter un argument: aucun ID de débat fourni")
        return False
    
    # Mesurer l'affichage du débat Thinktree avant d'ajouter un argument
    mesurer_fonction(session, "[PAGE] Affichage débat Thinktree", f"/debats_en_cours/{debat_id}/")
    
    # Pour ajouter un argument Thinktree, nous devons d'abord obtenir l'ID de l'argument parent
    try:
        response = session.get(f'{BASE_URL}/debats_en_cours/{debat_id}/')
        content = response.text
        
        # Tenter de trouver un ID d'argument dans la page
        parent_id = None
        if 'data-argument-id' in content:
            import re
            match = re.search(r'data-argument-id="(\d+)"', content)
            if match:
                parent_id = match.group(1)
        
        if not parent_id:
            print("Impossible de trouver un argument parent dans le débat Thinktree")
            return False
        
        # Préparer les données de l'argument
        argument_data = {
            'contenu': f'Argument Thinktree de test {generer_chaine_aleatoire()}',
            'parent_id': parent_id,
            'relation': '1',  # 1 = pour, -1 = contre
            'debat_id': debat_id
        }
        
        # Mesurer l'ajout de l'argument Thinktree
        mesurer_fonction(
            session, 
            "[ACTION] Ajout argument à débat Thinktree", 
            f"/ajouter_argument_kialo/{debat_id}/", 
            methode="POST", 
            donnees=argument_data
        )
        print(f"Argument ajouté au débat Thinktree {debat_id}")
        return True
    except Exception as e:
        print(f"Erreur lors de l'ajout d'un argument Thinktree: {e}")
        return False

def mesurer_navigation_pages(session):
    """Mesurer l'empreinte carbone de la navigation basique entre les pages"""
    mesurer_fonction(session, "[PAGE] Accueil", "/")
    mesurer_fonction(session, "[PAGE] Liste des débats en cours", "/debats_en_cours")
    mesurer_fonction(session, "[PAGE] Liste des débats finis", "/debats_finis")
    mesurer_fonction(session, "[PAGE] Formulaire de création de débat", "/create_debat")

def main():
    """Fonction principale"""
    print("=" * 70)
    print(f"MESURE D'EMPREINTE CARBONE COMPLÈTE - CampusParler")
    print("=" * 70)
    print(f"Serveur: {BASE_URL}")
    print(f"Itérations par test: {NB_ITERATIONS}")
    print()
    print("CONSEIL: Ce script utilise une base de données de test avec:")
    print("  - Un utilisateur de test (test_carbon/testcarbon)")
    print("  - Settings Django configurés pour les tests (--settings=config.settings_test)")
    print()
    
    # Vérifier que le serveur est en cours d'exécution
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f" Serveur trouvé et accessible (code: {response.status_code})")
    except Exception as e:
        print(f" ERREUR: Impossible de se connecter au serveur ({e}).")
        print("   Assurez-vous que votre serveur Django est en cours d'exécution avec:")
        print("   python manage.py runserver --settings=config.settings_test")
        return
    
    # Créer une session pour conserver les cookies
    with requests.Session() as session:
        print("\n1. PHASE DE NAVIGATION BASIQUE")
        print("-" * 40)
        mesurer_navigation_pages(session)
        
        print("\n2. PHASE D'INSCRIPTION ET CONNEXION")
        print("-" * 40)
        # Création d'un compte utilisateur
        username, password = creer_compte_utilisateur(session)
        
        # Connexion avec ce compte
        mesurer_fonction(
            session, 
            "[AUTH] Connexion utilisateur", 
            "/login", 
            methode="POST", 
            donnees={'username': username, 'password': password}
        )
        
        print("\n3. PHASE DE CRÉATION ET INTERACTION AVEC DÉBATS")
        print("-" * 40)
        # Créer un débat Flash et ajouter un argument
        debat_standard_id = creer_debat_standard(session)
        if debat_standard_id:
            ajouter_argument_standard(session, debat_standard_id)
        
        # Créer un débat Thinktree et ajouter un argument
        debat_kialo_id = creer_debat_kialo(session)
        if debat_kialo_id:
            ajouter_argument_kialo(session, debat_kialo_id)
        
        print("\n4. PHASE DE MESURES AVANCÉES")
        print("-" * 40)
        # Mesurer la recherche (si disponible)
        if debat_standard_id:
            mesurer_fonction(
                session,
                "[ACTION] Recherche de débats",
                f"/search?q={generer_chaine_aleatoire()}"
            )
        
        # Mesurer la déconnexion
        mesurer_fonction(session, "[AUTH] Déconnexion utilisateur", "/logout")
    
    # Générer le rapport
    generer_rapport()
    
    # Afficher les résultats
    print("\nRÉSULTATS DES MESURES:")
    for r in sorted(RESULTATS, key=lambda x: x["emissions_CO2_g"], reverse=True):
        print(f"- {r['fonctionnalite']} ({r['url']}): {r['emissions_CO2_g']:.8f} g CO2e")
    
    print(f"\nTotal: {sum(r['emissions_CO2_g'] for r in RESULTATS):.8f} g CO2e")
    print("\nRapport détaillé:")
    print(f"- CSV: {RAPPORT_CSV}")
    print("\nPour une analyse plus approfondie, consultez le rapport CSV.")

if __name__ == "__main__":
    main() 