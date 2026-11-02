# Usage de l'IA

Ce fichier répond à l'exigence de transparence du sujet. Il est à relire et à corriger par l'équipe pour refléter l'usage réel.

## Outils utilisés

| Outil | Parties du projet concernées |
| --- | --- |
| Assistant de code (Claude Code) | Code des quatre services FastAPI et de leurs tests, frontend Vue.js, Dockerfiles, `docker-compose.yml`, manifestes Kubernetes, workflows GitHub Actions, README |
| Assistant de conversation (Claude) | Rédaction du cahier des charges, choix d'architecture et de découpage en services |

## Vérification effectuée

À compléter par l'équipe pour chaque partie : ce qui a été relu, exécuté et testé.

- Tests unitaires et d'API : `pytest` dans chaque service, dont les deux exemples chiffrés de répartition des prix du cahier des charges.
- Lint : `ruff check .`
- Démarrage : `docker compose up --build`, puis parcours complet dans le navigateur.
- Kubernetes : `kubectl apply -k deploy/`, puis les démonstrations de mise à l'échelle, de mise à jour sans interruption, d'auto réparation et de persistance.

## Adaptations faites

À compléter par l'équipe : modifications apportées au code généré, choix personnels, erreurs de l'IA corrigées.

## Les cinq règles du sujet

1. Transparence : les outils et les parties concernées sont listés ci dessus.
2. Compréhension : chaque membre sait expliquer chaque ligne de code, y compris celles générées.
3. Validation : tout code généré est vérifié et testé.
4. Personnalisation : le code est adapté à l'architecture du projet.
5. Sécurité : aucune clé, aucun mot de passe ni aucun secret n'est partagé avec un outil d'IA.
