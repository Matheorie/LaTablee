# Usage de l'IA

Ce fichier répond à l'exigence de transparence du sujet. Il décrit ce que l'assistant a réellement fait pendant le projet, la vérification effectuée et les erreurs corrigées.

## Outil utilisé

Deux usages de l'IA, tous deux avec Claude d'Anthropic :

- **Assistant de conversation** : rédaction du cahier des charges. L'équipe a exprimé ses besoins et ses choix, l'IA les a mis en forme.
- **Claude Code**, l'assistant de code, dans son application de bureau avec le modèle Claude Sonnet 5.5 : réalisation du projet, le 2 novembre 2026, à partir de l'énoncé du TP, du cahier des charges et des maquettes. Les maquettes ont été fournies par l'équipe.

## Parties du projet concernées

| Partie | Rôle de l'IA |
| --- | --- |
| Cahier des charges | Rédigé par l'assistant de conversation d'après les consignes de l'équipe : fonctionnalités, architecture, règles de calcul, plan du projet |
| Services Python users, meals, bookings, accounts | Code écrit par Claude Code d'après le cahier des charges : routes, modèles, jetons JWT, règles de calcul des parts et des remboursements |
| Tests pytest et configuration ruff | Écrits par l'IA, dont les deux exemples chiffrés du cahier des charges |
| Frontend Vue.js | Écrit par l'IA, puis refait d'après les maquettes HTML et PNG fournies, avec les skills de design apple-design et emil-design-eng |
| Dockerfiles, `.dockerignore`, `docker-compose.yml`, `db/init.sh` | Écrits par l'IA |
| Manifestes Kubernetes, `kustomization.yaml`, `create_secrets.ps1` | Écrits par l'IA |
| Workflows GitHub Actions `ci.yml` et `cd.yml` | Écrits par l'IA |
| README, `docs/architecture.md`, ce fichier | Rédigés par l'IA |
| Git et GitHub | L'IA a fourni les commandes. L'équipe les a exécutées : commits, branches, pull requests, secrets, tag `v1.0.0`. L'IA n'a rien commité ni poussé |

## Vérification effectuée

- **Tests et lint** : 54 tests pytest (users 11, meals 12, bookings 11, accounts 20), dont les deux exemples du cahier des charges, et `ruff check` sans erreur.
- **Images Docker** : les 5 images construites, puis mesure de leur taille avec et sans multi stage.
- **Docker Compose** : lancement et parcours complet de l'application par l'équipe, qui a validé l'étape.
- **Frontend** : rendu comparé aux maquettes dans un navigateur, avec une API simulée aux données des maquettes. Le build `npm` n'a pas pu tourner sur le poste (politique Application Control de Windows) : il est fait dans Docker.
- **Kubernetes sur minikube** : 11 pods `Running`, test de bout en bout par requêtes (inscription, repas, réservation, clôture, dépense, soldes), puis les démonstrations de mise à l'échelle, de mise à jour sans interruption, de retour arrière, d'auto réparation et de persistance. Les résultats chiffrés sont dans le README.
- **Pipeline** : CI verte sur la pull request de `develop` vers `main` (20 vérifications), puis CD vert sur le tag `v1.0.0` : vérification du tag, publication des 5 images sur GHCR, déploiement sur un cluster kind éphémère et contrôle de `/health` des 4 services.

## Erreurs de l'IA détectées et corrigées

| Erreur | Comment elle a été trouvée | Correction |
| --- | --- | --- |
| Le frontend envoyait connexion et inscription en GET avec un corps | Signalée par l'équipe dans le navigateur | `POST` par défaut quand un corps est fourni |
| Design du frontend non conforme aux maquettes | Remarque de l'équipe | Réécriture d'après le code des maquettes (polices, couleurs, verre, animations) |
| 3 échecs sur 500 requêtes pendant une mise à jour | Boucle de test dans le cluster | `preStop` de 5 secondes sur les 5 Deployments, puis 0 échec |
| `cd.yml` invalide (`: ` dans une commande non protégée) | Run en échec à 0 s sur GitHub | Commande placée dans un bloc `run: \|`, validé avec un analyseur YAML |
| Le multi stage supposé réduire la taille des services Python | Mesure avec `docker images` | Aucun gain mesuré pour Python (271 Mo contre 254 Mo), gain net pour le frontend (74,1 Mo contre 269 Mo). Le README donne les deux |
| Commande de suivi de pull request inadaptée dans la procédure Git | Message d'erreur de `gh` | Procédure corrigée : suivre le run de la branche `develop` |

## Sécurité

Aucun secret n'a été partagé avec l'IA. Le fichier `.env` n'a pas été lu ni affiché : le script `create_secrets.ps1` le lit localement et les secrets GitHub ont été posés par l'équipe avec `gh secret set`. Les comptes créés pendant les tests dans le cluster utilisaient des mots de passe générés à la volée et des adresses `@k8s.test`.
