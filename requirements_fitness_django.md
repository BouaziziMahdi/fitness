# Requirements — Application de suivi de santé / fitness

## 1. Présentation du projet

L’application permet à un utilisateur de suivre son évolution de santé et de fitness à partir des données qu’il saisit régulièrement : poids, activités physiques, repas et objectifs personnels.

Le système analyse ensuite ces données afin d’afficher l’évolution des principaux indicateurs, notamment l’IMC, les calories consommées et brûlées, ainsi que la progression par rapport aux objectifs définis.

L’application comporte deux rôles principaux :

- **Admin**
- **User**

---

## 2. Objectifs

L’application doit permettre de :

- gérer les comptes utilisateurs ;
- enregistrer les informations personnelles liées au suivi ;
- enregistrer le poids au fil du temps ;
- enregistrer les repas et leurs calories ;
- enregistrer les activités sportives ;
- définir des objectifs personnels ;
- calculer automatiquement certains indicateurs ;
- suivre la progression dans un dashboard ;
- afficher des recommandations basées sur les tendances observées.

---

## 3. Rôles

### 3.1 Admin

L’administrateur doit pouvoir :

- se connecter à l’application ;
- consulter la liste des utilisateurs ;
- consulter les informations principales d’un utilisateur ;
- activer un compte utilisateur ;
- désactiver un compte utilisateur ;
- supprimer un utilisateur ;
- donner ou retirer l’accès à l’application.

Un utilisateur désactivé ne doit plus pouvoir se connecter.

---

### 3.2 User

L’utilisateur doit pouvoir :

- créer un compte ;
- se connecter ;
- se déconnecter ;
- consulter son profil ;
- modifier certaines informations personnelles ;
- saisir son poids ;
- enregistrer une activité physique ;
- enregistrer un repas ;
- définir ses objectifs ;
- consulter son historique ;
- consulter sa progression ;
- visualiser ses statistiques ;
- recevoir des recommandations simples basées sur ses données.

Chaque utilisateur doit uniquement avoir accès à ses propres données.

---

## 4. Authentification et sécurité

Le système doit fournir :

- une page d’inscription ;
- une page de connexion ;
- une fonction de déconnexion ;
- une gestion sécurisée des mots de passe avec Django ;
- une protection des pages privées ;
- une séparation des droits entre Admin et User.

Un utilisateur non authentifié ne doit pas accéder au dashboard.

Un utilisateur standard ne doit pas accéder aux fonctions réservées à l’administrateur.

---

## 5. Profil utilisateur

Chaque utilisateur possède un profil contenant notamment :

- nom ;
- prénom ;
- email ;
- âge ;
- sexe, si nécessaire pour les fonctionnalités choisies ;
- taille en centimètres ;
- poids actuel ;
- objectif de poids.

Les informations du profil peuvent être utilisées pour calculer les indicateurs de suivi.

---

## 6. Suivi du poids

L’utilisateur doit pouvoir ajouter régulièrement son poids.

Pour chaque mesure, le système doit enregistrer :

- utilisateur ;
- poids en kilogrammes ;
- date de mesure.

Exemple :

| Date | Poids |
|---|---:|
| 25/09/2026 | 78 kg |
| 02/10/2026 | 77.2 kg |
| 10/10/2026 | 76.5 kg |

Le système doit permettre d’afficher l’évolution du poids dans le temps.

---

## 7. Calcul de l’IMC

L’IMC doit être calculé automatiquement à partir du poids et de la taille.

Formule :

```text
IMC = poids (kg) / taille² (m)
```

Exemple :

```text
Poids = 78 kg
Taille = 1.80 m

IMC = 78 / (1.80 × 1.80)
IMC = 24.07
```

Le calcul doit utiliser le poids le plus récent de l’utilisateur.

---

## 8. Gestion des activités physiques

L’utilisateur doit pouvoir enregistrer une activité.

Une activité contient :

- type ou nom de l’activité ;
- durée en minutes ;
- calories brûlées ;
- date.

Exemples :

```text
Course
45 minutes
400 kcal
```

```text
Marche
30 minutes
150 kcal
```

Le système doit pouvoir calculer :

- le nombre d’activités par semaine ;
- la durée totale ;
- le total des calories brûlées.

---

## 9. Gestion des repas

L’utilisateur doit pouvoir enregistrer ses repas.

Un repas contient :

- nom du repas ;
- description ;
- nombre de calories ;
- date.

Exemple :

```text
Petit déjeuner
Oeufs + pain
450 kcal
```

Le système doit calculer le total des calories consommées par jour.

Exemple :

```text
Petit déjeuner : 450 kcal
Déjeuner         : 750 kcal
Dîner            : 550 kcal
Snack            : 150 kcal

Total            : 1900 kcal
```

---

## 10. Gestion des objectifs

L’utilisateur doit pouvoir définir ses objectifs.

Exemples :

- poids cible ;
- nombre maximum de calories par jour ;
- nombre d’activités par semaine ;
- éventuellement un objectif de calories brûlées.

Exemple :

```text
Poids actuel : 78 kg
Poids cible  : 72 kg

Calories/jour : 2000 kcal
Sport         : 4 séances/semaine
```

---

## 11. Dashboard utilisateur

Le dashboard doit présenter au minimum :

- poids actuel ;
- poids cible ;
- évolution du poids ;
- IMC actuel ;
- calories consommées aujourd’hui ;
- calories brûlées aujourd’hui ;
- nombre d’activités de la semaine ;
- progression par rapport aux objectifs ;
- recommandations.

Exemple :

```text
Poids actuel
76.5 kg

Objectif
72 kg

Progression
65 %

IMC
23.6

Calories consommées
1850 kcal

Calories brûlées
500 kcal

Activités cette semaine
3 / 4
```

---

## 12. Analyse de la progression

Le système doit comparer les données actuelles aux données précédentes.

Exemples d’analyses :

- variation du poids entre deux périodes ;
- progression vers le poids cible ;
- comparaison des calories consommées avec l’objectif quotidien ;
- comparaison du nombre d’activités avec l’objectif hebdomadaire ;
- évolution de l’IMC.

Exemple :

```text
Poids précédent : 78 kg
Poids actuel    : 76.5 kg

Evolution : -1.5 kg
```

---

## 13. Recommandations

Dans une première version, les recommandations peuvent être basées sur des règles simples.

### Exemple 1 — progression du poids

Si le poids diminue et que l’objectif est de perdre du poids :

```text
Bonne progression. Votre poids évolue dans la direction de votre objectif.
```

### Exemple 2 — calories

Si les calories consommées dépassent l’objectif quotidien :

```text
Votre consommation calorique dépasse votre objectif du jour.
```

### Exemple 3 — activité physique

Si le nombre d’activités de la semaine est inférieur à l’objectif :

```text
Vous êtes actuellement en dessous de votre objectif d’activité physique hebdomadaire.
```

Les recommandations doivent rester informatives et ne doivent pas remplacer un avis médical professionnel.

---

## 14. Modèle de données

### User

Utiliser le système utilisateur fourni par Django.

Champs principaux :

- id ;
- username ;
- email ;
- password ;
- is_active ;
- is_staff ;
- is_superuser.

---

### Profile

Relation :

```text
User 1 ---- 1 Profile
```

Champs possibles :

- user ;
- first_name ;
- last_name ;
- age ;
- height ;
- target_weight.

---

### WeightRecord

Relation :

```text
User 1 ---- N WeightRecord
```

Champs :

- id ;
- user ;
- weight ;
- date.

---

### Activity

Relation :

```text
User 1 ---- N Activity
```

Champs :

- id ;
- user ;
- name ;
- duration ;
- calories_burned ;
- date.

---

### Meal

Relation :

```text
User 1 ---- N Meal
```

Champs :

- id ;
- user ;
- name ;
- description ;
- calories ;
- date.

---

### Goal

Relation :

```text
User 1 ---- 1 Goal
```

Champs :

- id ;
- user ;
- target_weight ;
- daily_calorie_target ;
- weekly_activity_target.

---

## 15. Relations principales

```text
User
 |
 +---- Profile
 |
 +---- WeightRecord
 |
 +---- Activity
 |
 +---- Meal
 |
 +---- Goal
```

---

## 16. Architecture Django proposée

```text
fitness_project/
|
├── manage.py
|
├── fitness_project/
|   ├── settings.py
|   ├── urls.py
|   └── ...
|
├── accounts/
|   ├── models.py
|   ├── views.py
|   ├── urls.py
|   └── forms.py
|
├── health/
|   ├── models.py
|   ├── views.py
|   ├── urls.py
|   ├── forms.py
|   └── services.py
|
├── dashboard/
|   ├── views.py
|   ├── urls.py
|   └── services.py
|
└── templates/
```

---

## 17. Responsabilités des applications Django

### accounts

Responsable de :

- inscription ;
- connexion ;
- déconnexion ;
- profil utilisateur ;
- gestion des comptes.

### health

Responsable de :

- poids ;
- repas ;
- activités ;
- objectifs.

### dashboard

Responsable de :

- calcul des indicateurs ;
- statistiques ;
- progression ;
- graphiques ;
- recommandations.

---

## 18. Règles métier principales

1. Chaque donnée de santé appartient à un seul utilisateur.
2. Un User ne peut pas consulter les données d’un autre User.
3. Un utilisateur désactivé ne peut pas se connecter.
4. Seul un Admin peut administrer les comptes.
5. L’IMC doit utiliser la taille du profil et le poids le plus récent.
6. Les calories quotidiennes correspondent à la somme des repas d’une journée.
7. Les calories brûlées correspondent à la somme des activités enregistrées.
8. La progression doit être calculée à partir de l’historique.
9. Les recommandations doivent être générées à partir des tendances et des objectifs.
10. La suppression d’un utilisateur doit également gérer correctement les données qui lui appartiennent.

---

## 19. Pages principales

### Pages publiques

- `/register`
- `/login`

### Pages utilisateur

- `/dashboard`
- `/profile`
- `/weights`
- `/weights/add`
- `/activities`
- `/activities/add`
- `/meals`
- `/meals/add`
- `/goals`

### Administration

- `/admin`

---

## 20. Technologies proposées

Backend :

```text
Python
Django
```

Base de données :

```text
PostgreSQL
```

Interface :

```text
HTML
CSS
Bootstrap
JavaScript
```

Graphiques :

```text
Chart.js
```

Pour une version API :

```text
Django REST Framework
```

Déploiement possible :

```text
Docker
PostgreSQL
Django
```

---

## 21. MVP — Première version

La première version doit contenir :

- authentification ;
- gestion Admin/User ;
- profil ;
- ajout du poids ;
- ajout de repas ;
- ajout d’activités ;
- définition des objectifs ;
- calcul de l’IMC ;
- calcul des calories ;
- dashboard ;
- évolution du poids ;
- recommandations simples.

Les fonctionnalités avancées pourront être ajoutées après validation du MVP.

---

## 22. Évolutions possibles

Après le MVP, le projet pourra être enrichi avec :

- API REST ;
- application mobile ;
- notifications ;
- rappels pour saisir le poids ;
- calcul automatique des calories à partir des aliments ;
- objectifs personnalisés ;
- export PDF ;
- rapports hebdomadaires ;
- synchronisation avec une montre connectée ;
- authentification JWT ;
- système de rôles plus avancé ;
- recommandations basées sur une analyse statistique ou un modèle d’IA.
