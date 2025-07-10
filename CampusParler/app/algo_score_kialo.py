"""
Module d'analyse des forces d'arguments selon la sémantique Quad
"""

from .models import Argument
import logging

# Configurer le logger
logger = logging.getLogger(__name__)

# Score initial pour tout argument sans supporteurs ni attaquants
INITIAL_SCORE = 0.5

def normaliser_score_votes(argument):
    """
    Normalise le score des votes sur une échelle de 0 à 1
    Utilise la formule: score = upvotes / (upvotes + downvotes) ou 0.5 si pas de votes
    """
    upvotes = argument.upvotes
    downvotes = argument.downvotes
    total_votes = upvotes + downvotes
    
    if total_votes > 0:
        normalized_score = upvotes / total_votes
    else:
        normalized_score = 0.5
    
    logger.info(f"Argument {argument.id}: up({upvotes}), down({downvotes}) normalisé en {normalized_score}")
    return normalized_score

def get_score_initial(argument):
    """
    Retourne le score initial d'un argument basé sur ses votes
    """
    # Utiliser la formule de normalisation 
    return normaliser_score_votes(argument)

def get_supporteurs(argument):
    """Retourne les arguments qui supportent l'argument donné"""
    return Argument.objects.filter(parent_id=argument, relation=1.0)

def get_attaquants(argument):
    """Retourne les arguments qui attaquent l'argument donné"""
    return Argument.objects.filter(parent_id=argument, relation=-1.0)

def calcul_force_attaque(argument, cache=None):
    """
    Calcule la force d'attaque f-(alpha)
    
    Le paramètre cache est un dictionnaire qui stocke les scores déjà calculés
    pour éviter les calculs redondants et la récursion infinie
    """
    if cache is None:
        cache = {}
    
    attaquants = get_attaquants(argument)
    if not attaquants.exists():
        return None
    
    logger.info(f"Calcul force attaque pour argument {argument.id}, {len(attaquants)} attaquants trouvés")
    
    # Obtenir le score initial basé sur les votes
    score_initial = get_score_initial(argument)
    
    product = 1
    for attaquant in attaquants:
        score_attaquant = calcul_score_final(attaquant, cache)
        logger.info(f"  - Attaquant {attaquant.id} a un score de {score_attaquant}")
        product *= (1 - score_attaquant)
    
    force_attaque = score_initial * product
    logger.info(f"  => Force d'attaque calculée: {force_attaque}")
    return force_attaque

def calcul_force_support(argument, cache=None):
    """
    Calcule la force de support f+(alpha)
    
    Le paramètre cache est un dictionnaire qui stocke les scores déjà calculés
    pour éviter les calculs redondants et la récursion infinie
    """
    if cache is None:
        cache = {}
    
    supporteurs = get_supporteurs(argument)
    if not supporteurs.exists():
        return None
    
    logger.info(f"Calcul force support pour argument {argument.id}, {len(supporteurs)} supporteurs trouvés")
    
    # Obtenir le score initial basé sur les votes
    score_initial = get_score_initial(argument)
    
    product = 1
    for supporteur in supporteurs:
        score_supporteur = calcul_score_final(supporteur, cache)
        logger.info(f"  - Supporteur {supporteur.id} a un score de {score_supporteur}")
        product *= (1 - score_supporteur)
    
    force_support = 1 - (1 - score_initial) * product
    logger.info(f"  => Force de support calculée: {force_support}")
    return force_support

def calcul_score_final(argument, cache=None):
    """
    Calcule le score final s^f(alpha)
    
    Le paramètre cache est un dictionnaire qui stocke les scores déjà calculés
    pour éviter les calculs redondants et la récursion infinie
    """
    if cache is None:
        cache = {}
    
    # Vérifier si le score est déjà dans le cache
    arg_id = argument.id
    if arg_id in cache:
        return cache[arg_id]
    
    # Calculer le score pour tous les arguments, y compris les racines
    # Les racines auront leur score calculé en fonction de leurs arguments fils
    f_moins_val = calcul_force_attaque(argument, cache)
    f_plus_val = calcul_force_support(argument, cache)
    
    # Obtenir le score initial basé sur les votes
    score_initial = get_score_initial(argument)
    
    if f_moins_val is None and f_plus_val is None:
        score = score_initial
        logger.info(f"Argument {arg_id} n'a ni supporteurs ni attaquants, score = {score_initial}")
    elif f_moins_val is not None and f_plus_val is None:
        score = f_moins_val
        logger.info(f"Argument {arg_id} n'a que des attaquants, score = {score}")
    elif f_moins_val is None and f_plus_val is not None:
        score = f_plus_val
        logger.info(f"Argument {arg_id} n'a que des supporteurs, score = {score}")
    else:
        score = (f_plus_val + f_moins_val) / 2
        logger.info(f"Argument {arg_id} a des supporteurs et attaquants, score = {score} (support: {f_plus_val}, attaque: {f_moins_val})")
    
    # Stocker le résultat dans le cache
    cache[arg_id] = score
    return score

def calcul_scores_debat(debat_id):
    """
    Calcule les scores pour tous les arguments d'un débat
    et retourne un dictionnaire {argument_id: score}
    """
    arguments = Argument.objects.filter(debat_id=debat_id)
    logger.info(f"Calcul des scores pour le débat {debat_id}, {len(arguments)} arguments trouvés")
    
    cache = {}
    
    for arg in arguments:
        score = calcul_score_final(arg, cache)
        logger.info(f"Score final calculé pour argument {arg.id}: {score} (up: {arg.upvotes}, down: {arg.downvotes})")
    
    return cache

def mettre_a_jour_scores_arguments(debat_id):
    """
    Met à jour les scores dans la base de données pour tous les arguments d'un débat
    """
    logger.info(f"Mise à jour des scores pour le débat {debat_id}")
    scores = calcul_scores_debat(debat_id)
    
    # Log tous les scores calculés
    logger.info("Résumé des scores calculés:")
    for arg_id, score in scores.items():
        logger.info(f"  - Argument {arg_id}: {score}")
    
    count = 0
    for arg_id, score in scores.items():
        try:
            argument = Argument.objects.get(pk=arg_id)
            old_score = argument.quad_score
            argument.quad_score = score
            argument.save(update_fields=['quad_score'])
            count += 1
            logger.info(f"Score mis à jour pour argument {arg_id}: {old_score} -> {score}")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du score pour l'argument {arg_id}: {str(e)}")
    
    logger.info(f"Mise à jour terminée, {count} arguments mis à jour")
    return count 