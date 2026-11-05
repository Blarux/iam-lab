# Scénario 06 — Élévation de privilèges et séparation des tâches

## Objectif
Montrer qu'un administrateur qui ajoute un rôle sensible à un compte, hors processus, est détecté. Montrer aussi que l'API applique la séparation des tâches, même si ce rôle est attribué.

## Technique MITRE ATT&CK
T1098 — Account Manipulation (ajout de rôle) ; T1078 — Valid Accounts.

## Hypothèse de l'attaquant
Un administrateur malveillant, ou un compte administrateur compromis, donne à Alice (saisie des paiements) le rôle finance-validation, pour qu'elle puisse saisir **et** valider un paiement frauduleux. Par le processus normal (fichier RH, puis JML), cette demande serait refusée (SOD_REFUSE).

## Prérequis
- alice.martin : rôle finance-saisie (groupe grp-finance-saisie), déverrouillée, compteur remis à zéro.
- Admin events enregistrés avec leur contenu ; règles R5 (100131) et 100132 (niveau 12 pour it-admin et finance-validation).
- API : règle « on ne valide pas son propre paiement ».

## Étapes
1. Console d'administration : Users > alice.martin > Role mapping > Assign role > **finance-validation** (attribution directe, hors groupe). Noter l'heure.
2. PowerShell : Connexion-Api avec alice.martin, puis Recuperer-Jeton. Vérifier que le jeton contient les deux rôles.
3. `Appeler-Api POST /paiements/10` : saisie du paiement 10.
4. `Appeler-Api POST /paiements/10/validation` : tentative de validation.
5. Revue des accès : `INACTIF_JOURS=1 .venv/bin/python governance/access_review.py`.
6. **Remédiation** : retirer le rôle finance-validation d'Alice. Noter l'heure.
7. Extraire les événements, les admin events et le journal de l'API.

## Résultat attendu
- Détection : R5 (100131) et 100132 (niveau 12, T1098) quelques secondes après l'étape 1.
- Prévention : étape 3 acceptée, étape 4 **refusée** (403 « on ne valide pas son propre paiement »).
- Revue : Alice signalée « CONFLIT SoD » et « Rôle direct ».
- Comparaison : la même demande faite par le fichier RH avait été refusée par le JML (SOD_REFUSE, étape 10).
