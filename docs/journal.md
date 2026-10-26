# Journal de bord

Une entrée par séance de travail, la plus récente en haut.

---

## 2026-10-26 — Étapes 0 et 1 — Erwan

**Fait**
- Étape 0 : notions IAM, manipulations dans un Keycloak jetable (jetons, flux Authorization Code + PKCE), quiz.
- Étape 1 : lecture du schéma d'architecture à deux, installation d'Ubuntu dans WSL2, création du dépôt.

**Problèmes et solutions**
- Docker en erreur 500 : virtualisation désactivée dans le BIOS. Activée (VT-x / SVM).
- `http://0.0.0.0:8080` inaccessible : 0.0.0.0 signifie « toutes les interfaces » ; il faut utiliser `http://localhost:8080`.
- « Realm does not exist » : en mode dev, les données sont dans le conteneur et disparaissent avec `docker rm`.
- `Invalid parameter: code_challenge` : empreinte mal générée. Remplacement de `Get-Random` (non cryptographique) par `RandomNumberGenerator`.
- `invalid_grant` : code expiré (durée d'environ 1 min) ou adresse écrasée dans le presse-papiers.

**Observations utiles pour le rapport**
- Les jetons du realm `master` durent 60 s, contre 300 s dans un realm normal : la durée se règle par realm.
- Le client `admin-cli` de Keycloak 26 émet des jetons « allégés », sans `sub` ni rôles.
- Le refresh token dure 1 800 s, soit la durée d'inactivité maximale de la session.
- Réutiliser un code renvoie « Code not valid » : le code est à usage unique.
- Un mauvais verifier renvoie « PKCE verification failed: Code mismatch ».
- `auth_time` est antérieur à `iat` : le SSO a réutilisé la session existante sans redemander de connexion.

**Prochaine étape** : étape 2, préparation du poste et proxy HTTPS.
