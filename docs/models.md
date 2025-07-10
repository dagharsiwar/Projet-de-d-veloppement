# Schéma UML - Débats

## Classe : Debat
- **titre** : CharField(max_length=200)
- **description** : TextField (optionnel)
- **auteur_debat** : ForeignKey vers User
- **date_creation** : DateTimeField(auto_now_add=True)
- **statut** : CharField (choix : `en_cours`, `termine`)
- **type_debat** : CharField (choix : `standard`, `kialo`)
- **racine_id** : ForeignKey vers Argument (nullable, SET_NULL)

---

## Classe : Argument
- **debat_id** : ForeignKey vers Debat
- **auteur_argument** : ForeignKey vers User
- **titre_argument** : CharField (optionnel)
- **contenu_argument** : TextField
- **score_argument** : IntegerField (par défaut : 0)
- **position_argument** : BooleanField (optionnel, standard uniquement)
- **relation** : FloatField (Kialo uniquement : 1.0 = pour, -1.0 = contre)
- **parent_id** : ForeignKey vers Argument (nullable, Kialo)
- **est_racine** : BooleanField (par défaut : False)
- **quad_score** : FloatField (par défaut : 0.5)
- **upvotes** : IntegerField
- **downvotes** : IntegerField
- **date_argument** : DateTimeField(auto_now_add=True)
- **users_voted** : ManyToManyField vers User (votes)

---

## Classe : Reponse
- **argument_id** : ForeignKey vers Argument
- **auteur_reponse** : ForeignKey vers User
- **contenu_reponse** : TextField
- **score_reponse** : IntegerField
- **position_reponse** : BooleanField (True = pour, False = contre)
- **date_reponse** : DateTimeField(auto_now_add=True)
- **users_voted** : ManyToManyField vers User (votes)

---

## Relations :
- **Debat 1---n Argument**
- **Argument 1---n Reponse**
- **Argument 0---n Argument** (relation parent-enfant pour Kialo)
