# Forma — Suivi fitness

Application Django en français : inscription, connexion, profil, poids, repas, activités, objectifs, dashboard, graphique et administration. Les données sont isolées par utilisateur. Les saisies peuvent être modifiées ou supprimées avec confirmation.

## Démarrer

Python 3.12 conseillé (3.10 minimum), Django 5.2 LTS.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000/ et créer un compte. L’environnement `.venv` est déjà préparé si vous utilisez ce dossier de développement.

## Utilisation

1. Compléter la taille du profil pour calculer l’IMC.
2. Définir les objectifs souhaités (facultatifs).
3. Ajouter des mesures, activités et repas.
4. Consulter le tableau de bord et les historiques.

Administration : `/admin/`, avec le superutilisateur créé ci-dessus. La gestion Django des utilisateurs permet de consulter, modifier, désactiver (`Actif`) ou supprimer les comptes. Un compte désactivé perd également l’accès via une session existante. Un utilisateur standard n’a pas accès à l’administration. La suppression d’un compte supprime ses données associées.

## Règles de calcul

- Une mesure de poids par jour ; modifier l’entrée existante si nécessaire. Dates futures refusées.
- Poids actuel : dernière mesure selon sa date, pas selon sa date d’insertion.
- IMC : dernier poids / taille en mètres au carré ; absent si la taille manque. Aucune interprétation médicale automatique.
- Progression : `(poids actuel - poids initial) / (cible - poids initial)`, bornée entre 0 et 100 %. Fonctionne pour une hausse ou une baisse. Si cible et poids initial sont identiques, 100 % uniquement lorsque le poids actuel égale la cible. Changer la cible recalcule depuis la première mesure.
- Variation : comparaison avec la mesure précédente. L’évolution de l’IMC utilise la taille actuelle.
- Calories : sommes des saisies du jour, fuseau Europe/Paris. Les calories brûlées sont saisies par l’utilisateur.
- Semaine : du lundi à aujourd’hui. Le compteur porte sur les séances, même si plusieurs ont lieu le même jour.
- Les observations comparent les données aux objectifs personnels, sans prescription médicale.
- Graphique SVG local, sans CDN ni transmission de données à un service externe. Historique détaillé accessible sous forme de tableau paginé.

## Vérifier

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

## PostgreSQL

Sans configuration, SQLite est utilisé. Pour PostgreSQL, exporter les variables avant `migrate` :

```bash
export POSTGRES_DB=fitness
export POSTGRES_USER=fitness
export POSTGRES_PASSWORD='votre-mot-de-passe'
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
python manage.py migrate
```

La base et le rôle doivent déjà exister. Aucune donnée SQLite n’est automatiquement transférée.
