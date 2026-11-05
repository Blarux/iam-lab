# Scénario 04 — Départ d'un salarié

## Objectif
Mesurer le temps entre la déclaration du départ par les RH et la perte effective de **tous** les accès, y compris les sessions déjà ouvertes dans les applications.

## Technique MITRE ATT&CK
T1078 — Valid Accounts (usage d'un compte après départ).

## Hypothèse de l'attaquant
Bruno quitte l'entreprise en mauvais termes. Il garde ses onglets ouverts sur son PC personnel et tente de récupérer des données après son départ.

## Prérequis
- bruno.leroy actif, avec accès à Nextcloud (et à Gitea s'il est développeur).
- JML : LEAVER = retrait des groupes, suppression du mot de passe, déplacement dans ou=departs, désactivation dans Keycloak avec fermeture des sessions, désactivation dans Nextcloud (occ user:disable).
- Règle R3 (100104) : connexion d'un compte désactivé ou inconnu.

## Étapes
1. Fenêtre InPrivate : connecter Bruno à https://cloud.acmefin.test, puis à https://git.acmefin.test. Laisser les deux onglets ouverts.
2. Passer Bruno à « parti » dans governance/hr/rh.csv.
3. Lancer jml.py en simulation, puis avec --apply, en notant l'heure de départ.
4. Recharger l'onglet Nextcloud, puis l'onglet Gitea, et noter l'heure de perte d'accès.
5. Nouvelle fenêtre InPrivate : tenter une connexion de Bruno sur https://sso.acmefin.test/realms/acmefin/account.
6. Extraire les preuves : jml-log.jsonl, événements Keycloak, état du compte Nextcloud.

## Résultat attendu
- Keycloak : compte désactivé, sessions fermées ; nouvelle connexion refusée.
- Nextcloud : session ouverte perdue au rechargement (compte désactivé).
- Gitea : **à observer** (aucune action prévue dans le JML).
- Détection : R3 (100104) lors de la tentative de l'étape 5.
- Mesures : délai départ → plus de connexion possible ; délai départ → perte de chaque session ouverte.
