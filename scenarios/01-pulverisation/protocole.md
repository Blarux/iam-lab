# Scénario 01 — Pulvérisation de mots de passe (password spraying)

## Objectif
Montrer qu'une attaque qui essaie **un seul** mot de passe sur **beaucoup** de comptes passe sous le verrouillage par compte, et vérifier qu'elle est quand même détectée.

## Technique MITRE ATT&CK
T1110.003 — Brute Force: Password Spraying (tactique Credential Access, TA0006).

## Hypothèse de l'attaquant
Il connaît le format des identifiants (prenom.nom, deviné depuis LinkedIn ou le site de l'entreprise). Il essaie un mot de passe courant (« Automne2026! ») une seule fois par compte, pour ne verrouiller personne et rester discret.

## Prérequis
- Keycloak, le collecteur et Wazuh (manager et dashboard) démarrés.
- Verrouillage par compte actif : verrouillage temporaire après 5 échecs (étape 3).
- Règle R1 (100110) chargée : 5 échecs (100102) sur des comptes différents, depuis la même IP, en 120 s.
- 5 comptes fictifs du royaume acmefin.

## Étapes
1. Ouvrir https://sso.acmefin.test/realms/acmefin/account dans une fenêtre InPrivate.
2. Saisir l'identifiant du compte 1, puis un mauvais mot de passe : « Invalid password. »
3. Cliquer sur ↻ (changer d'identifiant) et recommencer avec 4 autres comptes, en moins de 2 minutes.
4. Relever les LOGIN_ERROR dans Keycloak (Events > User events), puis l'alerte 100110 dans Wazuh.
5. Extraire les preuves : `python3 scenarios/extraire.py 25 > scenarios/01-pulverisation/evenements.jsonl`.

## Résultat attendu
- Prévention : **aucune**. Avec un seul échec par compte, on reste sous le seuil de 5 : aucun compte n'est verrouillé. C'est la limite du verrouillage par compte que ce scénario démontre.
- Détection : R1 (100110, niveau 12), dans le délai de collecte (relevé toutes les 30 s, plus le traitement).
- Défense en profondeur : même si le mot de passe essayé était le bon, le second facteur bloquerait la connexion (scénario 02).
