from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Debat, Argument, Reponse
from .algo_score import algo_score
from .algo_score_kialo import calcul_score_final, mettre_a_jour_scores_arguments

# Page de présentation
def index(request):
    return render(request, 'app/index.html')

# Page de connexion
def login(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Bienvenue, {username} !')
            return redirect('index')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    
    return render(request, 'app/login.html')

# Page d'inscription
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # on vérifie si l'utilisateur existe déjà 
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
            return render(request, 'app/login.html')
        
        # création du nouvel utilisateur
        user = User.objects.create_user(username=username, password=password)
        auth_login(request, user)
        messages.success(request, f'Compte créé avec succès ! Bienvenue, {username} !')
        return redirect('index')
    
    # Si la méthode n'est pas post on redirige vers la page de login
    return redirect('login')

def logout(request):
    auth_logout(request) 
    messages.info(request, 'Vous avez été déconnecté.') 
    return redirect('index')

# Page des débats en cours
def debats_en_cours(request):
    # Trie des débats en cours en fonction de la date actuelle
    expiration = timezone.now() - timedelta(days=5) # Durée de vie d'un débat de 5 jours
    Debat.objects.filter(statut='en_cours', date_creation__lte=expiration).update(statut='termine') # Met à jour le statut des débats de date antérieure à il y a 5 jours
    # Recupère les débats en cours
    debats = Debat.objects.filter(statut='en_cours').order_by('-date_creation')
    return render(request, 'app/debats_en_cours.html', {'debats': debats})

# Page des débats passés
def debats_finis(request):
    debats = Debat.objects.filter(statut='termine').order_by('-date_creation')
    return render(request, 'app/debats_finis.html', {'debats': debats})

# Page de choix du type de débat
@login_required(login_url='login')
def create_debat(request):
    return render(request, 'app/choix_type_debat.html')

# Formulaire de création de débat standard
@login_required(login_url='login')
def create_debat_standard(request):
    return render(request, 'app/create_debat_standard.html')

# Formulaire de création de débat kialo
@login_required(login_url='login')
def create_debat_kialo(request):
    return render(request, 'app/create_debat_kialo.html')

# Sauvegarde d'un nouveau débat standard
@login_required(login_url='login')
def save_debat_standard(request):
    if request.method == 'POST':
        titre = request.POST.get('titre')
        description = request.POST.get('description')
        
        if not titre or not description:
            messages.error(request, "Le titre et la description sont obligatoires.")
            return redirect('create_debat_standard')
        
        try:
            # Création d'un débat standard
            debat = Debat.objects.create(
                titre=titre,
                description=description,
                auteur_debat=request.user,
                statut='en_cours',
                type_debat='standard'
            )
            messages.success(request, "Votre débat standard a été créé avec succès !")
            return redirect('debats_en_cours')
        except Exception as e:
            messages.error(request, f"Une erreur est survenue: {str(e)}")
            return redirect('create_debat_standard')
    
    return redirect('create_debat_standard')

# Sauvegarde d'un nouveau débat kialo
@login_required(login_url='login')
def save_debat_kialo(request):
    if request.method == 'POST':
        titre = request.POST.get('titre')
        contenu_argument = request.POST.get('contenu_argument')
        
        if not titre or not contenu_argument:
            messages.error(request, "Le titre et l'argument initial sont obligatoires.")
            return redirect('create_debat_kialo')
        
        try:
            # Création d'un débat kialo
            debat = Debat.objects.create(
                titre=titre,
                auteur_debat=request.user,
                statut='en_cours',
                type_debat='kialo'
            )
            
            # Création de l'argument racine
            racine = Argument.objects.create(
                debat_id=debat,
                auteur_argument=request.user,
                contenu_argument=contenu_argument,
                est_racine=True,
                quad_score=0.5  # Score initial
            )
            
            # Association de la racine au débat
            debat.racine_id = racine
            debat.save()
            
            messages.success(request, "Votre débat Kialo a été créé avec succès !")
            return redirect('debats_en_cours')
        except Exception as e:
            messages.error(request, f"Une erreur est survenue: {str(e)}")
            return redirect('create_debat_kialo')
    
    return redirect('create_debat_kialo')

# Point d'entrée pour l'affichage d'un débat (standard ou kialo)
@login_required(login_url='login')
def debat_details(request, debat_id):
    """Point d'entrée commun pour visualiser un débat standard ou kialo"""
    debat = get_object_or_404(Debat, pk=debat_id)
    
    # Rediriger vers la vue appropriée selon le type de débat
    if debat.type_debat == 'standard':
        return debat_standard_details(request, debat)
    else:  # 'kialo'
        return debat_kialo_details(request, debat)

# Affichage et traitement des actions pour un débat standard
def debat_standard_details(request, debat):
    # Gestion Votes
    if request.method == 'POST' and 'vote_type' in request.POST:
        vote_type = request.POST.get('vote_type')
        element_type = request.POST.get('element_type')
        element_id = request.POST.get('element_id')
        user = request.user

        try:
            if element_type == 'argument':
                element = get_object_or_404(Argument, pk=element_id)
            elif element_type == 'reponse':
                element = get_object_or_404(Reponse, pk=element_id)
            else:
                raise ValueError("Type d'élément invalide")

            # Vérifier si l'utilisateur a déjà voté
            if user in element.users_voted.all():
                messages.warning(request, "Vous avez déjà voté pour cet élément!")
            else:
                if vote_type == 'like':
                    if element_type == 'argument':
                        element.score_argument += 1
                    else:  # réponse
                        element.score_reponse += 1
                elif vote_type == 'dislike':
                    if element_type == 'argument':
                        element.score_argument -= 1
                    else:  # réponse
                        element.score_reponse -= 1
                else:
                    raise ValueError("Type de vote invalide")
                
                element.users_voted.add(user)
                element.save()
                messages.success(request, "Votre vote a été enregistré!")

        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")

        return redirect('debat_details', debat_id=debat.id)
    
    # Gestion de l'ajout d'argument
    if request.method == 'POST'and 'titre_argument' in request.POST:
        titre = request.POST.get('titre_argument', '').strip()
        contenu = request.POST.get('contenu_argument', '').strip()
        position = request.POST.get('position_argument') == 'True'
        
        if titre and contenu:
            Argument.objects.create(
                debat_id=debat,
                auteur_argument=request.user,
                titre_argument=titre,
                contenu_argument=contenu,
                position_argument=position,
                score_argument=0
            )
            messages.success(request, "Argument ajouté avec succès!")
            return redirect('debat_details', debat_id=debat.id)
        else:
            messages.error(request, "Veuillez remplir tous les champs")
            return redirect('debat_details', debat_id=debat.id)
            
    # Gestion de l'ajout des réponses  
    if request.method == 'POST' and 'contenu_reponse' in request.POST:
        argument_id = request.POST.get('argument_id')
        contenu = request.POST.get('contenu_reponse', '').strip()
        position = request.POST.get('position_reponse')
        
        if contenu and position is not None:
            argument = get_object_or_404(Argument, pk=argument_id)
            Reponse.objects.create(
                argument_id=argument,
                auteur_reponse=request.user,
                contenu_reponse=contenu,
                position_reponse=position,
                score_reponse=0
            )
            messages.success(request, "Réponse ajoutée avec succès!")
            return redirect('debat_details', debat_id=debat.id)
        else:
            messages.error(request, "Veuillez remplir tous les champs")
            return redirect('debat_details', debat_id=debat.id)
  
    # Liste arguments pour
    arg_pour = Argument.objects.filter(debat_id=debat.pk, position_argument=True).order_by('-score_argument')
    # Liste arguments contre
    arg_contre = Argument.objects.filter(debat_id=debat.pk, position_argument=False).order_by('-score_argument')
    # Liste de tous les arguments
    ens_arg = Argument.objects.filter(debat_id=debat.pk).order_by('-score_argument')
    liste_rep = [] # Liste des réponses liées au débat
    # Ajouter l'ensemble des réponses aux arguments
    for arg in ens_arg:
        for rep in Reponse.objects.filter(argument_id=arg.pk).order_by('-date_reponse'):
            liste_rep.append(rep)
    
    # Score du débat en % (utilisation de l'algorithme de calcul)
    score_debat = round(algo_score(arg_pour, arg_contre), 3)*100
    # Score du débat côté Contre
    score_inverse = 100-score_debat

    return render(request, 'app/pageDebat.html', {
        'debat': debat,
        'liste_arg_pour': arg_pour,
        'liste_arg_contre': arg_contre,
        'liste_rep': liste_rep,
        'score_debat': score_debat,
        'score_inverse': score_inverse
    })

# Affichage et traitement des actions pour un débat kialo
def debat_kialo_details(request, debat):
    # Gestion des Votes
    if request.method == 'POST' and 'vote_type' in request.POST:
        vote_type = request.POST.get('vote_type')
        element_id = request.POST.get('element_id')
        user = request.user

        try:
            element = get_object_or_404(Argument, pk=element_id)

            # Vérifier si l'utilisateur a déjà voté
            if user in element.users_voted.all():
                messages.warning(request, "Vous avez déjà voté pour cet argument!")
            else:
                if vote_type == 'like':
                    element.upvotes += 1
                    element.score_argument += 1  # Mettre à jour aussi score_argument pour compatibilité
                elif vote_type == 'dislike':
                    element.downvotes += 1
                    element.score_argument -= 1  # Mettre à jour aussi score_argument pour compatibilité
                else:
                    raise ValueError("Type de vote invalide")
                
                element.users_voted.add(user)
                element.save()
                
                # Mettre à jour les scores de tous les arguments après un vote
                mettre_a_jour_scores_arguments(debat.pk)
                messages.success(request, "Votre vote a été enregistré!")

        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")

        # Rediriger vers la même page avec le même focus si défini
        focus_id = request.GET.get('focus')
        if focus_id:
            return redirect(f'/debats_en_cours/{debat.pk}/?focus={focus_id}')
        return redirect('debat_details', debat_id=debat.pk)
    
    # Gestion de l'ajout d'argument
    if request.method == 'POST' and 'contenu_argument' in request.POST:
        contenu = request.POST.get('contenu_argument', '').strip()
        relation = float(request.POST.get('relation', '1.0'))  # Utiliser directement relation
        parent_id = request.POST.get('parent_id', None)
        
        if contenu:
            parent = None
            # Vérifier si parent_id est valide
            if parent_id:
                try:
                    parent_id = int(parent_id)
                    parent = get_object_or_404(Argument, pk=parent_id)
                except (ValueError, TypeError):
                    # Si la conversion échoue, utiliser l'argument racine comme parent
                    parent = debat.racine_id
            else:
                # Si aucun parent_id n'est fourni, utiliser l'argument racine
                parent = debat.racine_id
            
            # Créer le nouvel argument
            Argument.objects.create(
                debat_id=debat,
                auteur_argument=request.user,
                contenu_argument=contenu,
                relation=relation,
                parent_id=parent,
                est_racine=False,
                quad_score=0.5  # Score initial, sera recalculé
            )
            
            # Mettre à jour les scores de tous les arguments
            num_updated = mettre_a_jour_scores_arguments(debat.pk)
            messages.success(request, "Argument ajouté avec succès!")
            
            # Si un focus était défini, rediriger vers lui
            if parent_id:
                return redirect(f'/debats_en_cours/{debat.pk}/?focus={parent_id}')
            return redirect('debat_details', debat_id=debat.pk)
        else:
            messages.error(request, "Veuillez remplir tous les champs")
            return redirect('debat_details', debat_id=debat.pk)
    
    # Récupérer le focus_argument (argument central actuel)
    focus_id = request.GET.get('focus')
    focus_argument = None
    ancestors = []  # Liste pour stocker tous les ancêtres
    
    # Récupérer l'argument racine du débat
    racine = debat.racine_id
    
    if focus_id:
        try:
            focus_argument = Argument.objects.get(pk=focus_id, debat_id=debat.pk)
            
            # Récupérer tous les ancêtres (chaîne complète jusqu'à la racine)
            current = focus_argument
            while current.parent_id and not current.parent_id.est_racine:
                ancestors.append(current.parent_id)
                current = current.parent_id
                
            # Si le dernier parent n'est pas la racine, ajouter la racine
            if current.parent_id and current.parent_id.est_racine:
                ancestors.append(current.parent_id)
            elif not current.est_racine:
                ancestors.append(racine)
                
            # Inverser pour avoir l'ordre: racine -> parent direct
            ancestors.reverse()
            
        except (Argument.DoesNotExist, ValueError):
            focus_argument = None
    
    # Si aucun focus n'est défini ou est invalide, utiliser la racine
    if not focus_argument:
        focus_argument = racine
        ancestors = []
    
    # Mettre à jour les scores dans la base de données
    # (on le fait ici pour s'assurer que tous les scores sont à jour)
    num_updated = mettre_a_jour_scores_arguments(debat.pk)
    
    # Arguments de premier niveau pour et contre l'argument en focus
    arg_pour = Argument.objects.filter(
        debat_id=debat.pk, 
        relation=1.0,  # Support
        parent_id=focus_argument,
        est_racine=False
    ).order_by('-quad_score')
    
    arg_contre = Argument.objects.filter(
        debat_id=debat.pk, 
        relation=-1.0,  # Attaque
        parent_id=focus_argument,
        est_racine=False
    ).order_by('-quad_score')
    
    # Forcer le rafraîchissement du focus_argument pour avoir le score le plus récent
    if focus_argument:
        focus_argument.refresh_from_db()
    
    return render(request, 'app/pageDebatKialo.html', {
        'debat': debat,
        'racine': racine,
        'focus_argument': focus_argument,
        'ancestors': ancestors,
        'liste_arg_pour': arg_pour,
        'liste_arg_contre': arg_contre,
        'num_updated': num_updated  # Pour debugging
    })

# Page du débat passé
def debat_passe_details(request, debat_id):
    debat = get_object_or_404(Debat, pk=debat_id)
    
    # Rediriger vers la vue appropriée selon le type de débat
    if debat.type_debat == 'kialo':
        return debat_kialo_passe_details(request, debat)
    
    # Si c'est un débat standard, continuer avec le code existant
    # Liste arguments pour
    arg_pour = Argument.objects.filter(debat_id=debat_id, position_argument=True).order_by('-score_argument')
    # Liste arguments contre
    arg_contre = Argument.objects.filter(debat_id=debat_id, position_argument=False).order_by('-score_argument')
    # Liste de tous les arguments
    ens_arg = Argument.objects.filter(debat_id=debat_id).order_by('-score_argument')
    liste_rep = [] # Liste des réponses liées au débat
    # Ajouter l'ensemble des réponses aux arguments
    for arg in ens_arg:
        for rep in Reponse.objects.filter(argument_id=arg.pk).order_by('-date_reponse'):
            liste_rep.append(rep)
    
    # Score du débat en % (utilisation de l'algorithme de calcul)
    score_debat = round(algo_score(arg_pour, arg_contre), 3)*100
    # Score du débat côté Contre
    score_inverse = 100-score_debat

    return render(request, 'app/pageDebatPasse.html', {
        'debat': debat,
        'liste_arg_pour': arg_pour,
        'liste_arg_contre': arg_contre,
        'liste_rep': liste_rep,
        'score_debat': score_debat,
        'score_inverse': score_inverse
    })
    
# Affichage d'un débat kialo terminé
def debat_kialo_passe_details(request, debat):
    # Récupérer le focus_argument (argument central actuel)
    focus_id = request.GET.get('focus')
    focus_argument = None
    ancestors = []  # Liste pour stocker tous les ancêtres
    
    # Récupérer l'argument racine du débat
    racine = debat.racine_id
    
    if focus_id:
        try:
            focus_argument = Argument.objects.get(pk=focus_id, debat_id=debat.pk)
            
            # Récupérer tous les ancêtres (chaîne complète jusqu'à la racine)
            current = focus_argument
            while current.parent_id and not current.parent_id.est_racine:
                ancestors.append(current.parent_id)
                current = current.parent_id
                
            # Si le dernier parent n'est pas la racine, ajouter la racine
            if current.parent_id and current.parent_id.est_racine:
                ancestors.append(current.parent_id)
            elif not current.est_racine:
                ancestors.append(racine)
                
            # Inverser pour avoir l'ordre: racine -> parent direct
            ancestors.reverse()
            
        except (Argument.DoesNotExist, ValueError):
            focus_argument = None
    
    # Si aucun focus n'est défini ou est invalide, utiliser la racine
    if not focus_argument:
        focus_argument = racine
        ancestors = []
    
    # Arguments de premier niveau pour et contre l'argument en focus
    arg_pour = Argument.objects.filter(
        debat_id=debat.pk, 
        relation=1.0,  # Support
        parent_id=focus_argument,
        est_racine=False
    ).order_by('-quad_score')
    
    arg_contre = Argument.objects.filter(
        debat_id=debat.pk, 
        relation=-1.0,  # Attaque
        parent_id=focus_argument,
        est_racine=False
    ).order_by('-quad_score')
    
    # Forcer le rafraîchissement du focus_argument pour avoir le score le plus récent
    if focus_argument:
        focus_argument.refresh_from_db()
    
    return render(request, 'app/pageDebatKialoPasse.html', {
        'debat': debat,
        'racine': racine,
        'focus_argument': focus_argument,
        'ancestors': ancestors,
        'liste_arg_pour': arg_pour,
        'liste_arg_contre': arg_contre
    })