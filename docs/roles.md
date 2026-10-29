# Modèle de rôles AcmeFin

Règle de conception : les groupes LDAP décrivent l'organisation, les rôles Keycloak portent les droits.
Chaque groupe donne un rôle. On n'attribue jamais un rôle directement à une personne.

| Service | Groupe LDAP | Rôle Keycloak | Accès |
| --- | --- | --- | --- |
| RH | grp-rh | rh-gestionnaire | Nextcloud (dossiers RH) |
| Finance | grp-finance-saisie | finance-saisie | Nextcloud (finance), API : saisir un paiement |
| Finance | grp-finance-validation | finance-validation | Nextcloud (finance), API : valider un paiement |
| Développement | grp-dev | dev | Gitea, Grafana en lecture |
| Développement | grp-dev-lead | dev-lead | Gitea (fusion sur la branche principale), Grafana en lecture |
| IT | grp-it-support | it-support | Grafana en édition |
| IT | grp-it-admin | it-admin | Administration de Gitea et Grafana, srv-01 via OpenBao |

## Règles particulières

- Séparation des tâches : `finance-saisie` et `finance-validation` sont incompatibles sur un même compte.
- `it-admin` : passkey obligatoire, accès SSH uniquement par certificat OpenBao de 30 minutes.

## Personnages de test

| Compte | Groupe | Rôle dans la démo |
| --- | --- | --- |
| alice.martin | grp-finance-saisie | Saisit les paiements |
| bruno.leroy | grp-finance-validation | Valide les paiements |
| chloe.dubois | grp-dev | Utilisatrice standard, future mutation |
| david.moreau | grp-it-admin | Administrateur, accès à srv-01 |
| emma.petit | grp-rh | Future salariée sur le départ |

## Écarts connus

- Gitea : tout salarié authentifié peut se connecter, alors que la matrice le réserve à dev, dev-lead et it-admin. Correction prévue à l'étape 7 (flux Keycloak dédié au client gitea).
