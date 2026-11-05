# Scénario 02 — Mot de passe volé

## Objectif
Montrer qu'un mot de passe volé ne suffit pas pour entrer : le second facteur bloque l'attaquant, et ses essais répétés au second facteur sont détectés.

## Technique MITRE ATT&CK
T1078 — Valid Accounts (le mot de passe est valide) ; T1621 — Multi-Factor Authentication Request Generation (insistance sur le second facteur).

## Hypothèse de l'attaquant
Il a obtenu le mot de passe d'Alice (hameçonnage, fuite d'une autre base, post-it). Il n'a ni son téléphone (TOTP) ni son PC (passkey). Il tente de deviner des codes TOTP.

## Prérequis
- Flux acmefin-browser actif : identifiant, puis passkey **ou** mot de passe + OTP.
- alice.martin a un TOTP enregistré.
- Règle 100103 : échec au second facteur (LOGIN_ERROR avec details.selected_credential_id).
- Règle R2 (100111) : 3 échecs au second facteur pour le même compte en 300 s.
- Verrouillage du compte à 5 échecs (non atteint ici : 3 essais).

## Étapes
1. Ouvrir https://sso.acmefin.test/realms/acmefin/account dans une fenêtre InPrivate.
2. Saisir alice.martin. Choisir « Try another way », puis la méthode mot de passe + OTP.
3. Saisir le **bon** mot de passe.
4. Saisir 3 codes faux (000000, 123456, 111111) : « Invalid authenticator code. »
5. Fermer la fenêtre sans se connecter.
6. Relever les LOGIN_ERROR dans Keycloak et déplier l'un d'eux (selected_credential_id), puis relever l'alerte 100111 dans Wazuh.
7. Extraire les preuves : `python3 scenarios/extraire.py 10 > scenarios/02-mot-de-passe-vole/evenements.jsonl`.
8. Remise à zéro : connecter Alice normalement (passkey), pour remettre à zéro son compteur d'échecs avant le scénario 06.

## Résultat attendu
- Prévention : connexion **refusée** au second facteur malgré le bon mot de passe.
- Détection : 3 × 100103 (niveau 6), puis R2 (100111, niveau 10) dans le délai de collecte.
- Pas de verrouillage : 3 échecs sur un seuil de 5. C'est la détection qui prend le relais.
