from .models import Debat, Argument, Reponse

# Algorithme du score du débat

def algo_score(liste_arg_pour, liste_arg_contre):
    """
    Calcul le score d'un débat en fonction du score des arguments de chaque parti et de leurs réponses.
    Valeur de retour : float entre 0 et 1 (0.5 par défaut)

    liste_arg_pour : liste des arguments Pour
    liste_arg_contre : liste des arguments Contre
    """

    score_side_pour = 0
    score_side_contre = 0

    # Score camp Pour
    for arg in liste_arg_pour:
        score_arg = arg.score_argument # Score d'un argument relatif à ses réponses
        for rep in Reponse.objects.filter(argument_id=arg.pk):
            # Si la réponse est un support -> son score s'ajoute au score de l'argument
            if rep.position_reponse:
                score_arg+=rep.score_reponse
            # Si la réponse est une attaque -> son score diminue le score de l'argument
            else:
                score_arg-=rep.score_reponse
        # Ajout du score de l'argument au score de son camp
        score_side_pour+=score_arg
    # Minorer le score à 0
    if score_side_pour<0:
        score_side_pour=0


    # Score camp Contre
    for arg in liste_arg_contre:
        score_arg = arg.score_argument
        for rep in Reponse.objects.filter(argument_id=arg.pk):
            # Si la réponse est un support -> son score s'ajoute au score de l'argument
            if not rep.position_reponse:
                score_arg+=rep.score_reponse
            # Si la réponse est une attaque -> son score diminue le score de l'argument
            else:
                score_arg-=rep.score_reponse
        # Ajout du score de l'argument au score de son camp
        score_side_contre+=score_arg
    # Minorer le score à 0
    if score_side_contre<0:
        score_side_contre=0


    # Score total du débat
    if(score_side_pour+score_side_contre)!=0:
        score_debat = score_side_pour/(score_side_pour+score_side_contre)
    else:
        score_debat = 0.5

    return score_debat