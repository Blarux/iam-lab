# Matrice des droits AcmeFin

| Rôle | Gitea | Grafana | Nextcloud | API paiements | srv-01 (SSH) |
| --- | --- | --- | --- | --- | --- |
| rh-gestionnaire | — | — | Dossiers RH | — | — |
| finance-saisie | — | — | Dossiers finance | Saisir | — |
| finance-validation | — | — | Dossiers finance | Valider (pas ses propres saisies) | — |
| dev | Lecture et écriture | Lecture | Partage équipe | — | — |
| dev-lead | Fusion sur la branche principale | Lecture | Partage équipe | — | — |
| it-support | — | Édition | — | — | — |
| it-admin | Administrateur | Administrateur | — | — | Temporaire via OpenBao (étape 8) |

## Où chaque règle est appliquée

| Règle | Appliquée par |
| --- | --- |
| Accès à Gitea | Keycloak (flux acmefin-gitea et droit acces-gitea) |
| Rôle dans Grafana | Grafana (ROLE_ATTRIBUTE_PATH, mode strict) |
| Saisie et validation des paiements | API (rôles du jeton) |
| Pas de validation de ses propres paiements | API (règle métier) |
| Rôles incompatibles sur un même compte | Script JML (étape 10) et revue des accès |
