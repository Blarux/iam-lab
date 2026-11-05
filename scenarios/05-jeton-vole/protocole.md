# Scénario 05 — Jeton volé ou rejoué

## Objectif
Montrer qu'un jeton volé a une valeur limitée : un refresh token ne sert qu'une fois, un access token expire en 5 minutes, et on ne peut pas détourner le code d'autorisation vers un site de l'attaquant.

## Technique MITRE ATT&CK
T1550.001 — Use Alternate Authentication Material: Application Access Token ; T1528 — Steal Application Access Token.

## Hypothèse de l'attaquant
Il a copié les jetons de Chloé (poste infecté, journal mal protégé, proxy). Il essaie de les réutiliser, ou de faire envoyer le code d'autorisation vers son propre site.

## Prérequis
- Client api-tester (public, PKCE). Access token : 5 min. Rotation des refresh tokens : Revoke Refresh Token ON, Max Reuse 0.
- REFRESH_TOKEN_ERROR enregistré dans les événements ; règle R4 (100106).
- Fonctions PowerShell Connexion-Api, Recuperer-Jeton, Rafraichir-Jeton et Appeler-Api chargées.

## Étapes
1. Connexion-Api, connexion de chloe.dubois par passkey, puis Recuperer-Jeton. Noter l'heure. Mettre de côté `$vieux = $global:jeton` et `$vole = $global:refresh`.
2. Usage légitime : `Rafraichir-Jeton $vole` → succès, nouveaux jetons (rotation).
3. Rejeu par l'attaquant : `Rafraichir-Jeton $vole` une seconde fois → refus attendu.
4. Observation : le nouveau refresh token légitime (`Rafraichir-Jeton $global:refresh`) fonctionne-t-il encore après la tentative de rejeu ?
5. Détournement : ouvrir l'URL d'autorisation avec redirect_uri=https://attaquant.example/callback → refus attendu.
6. Plus de 5 minutes après l'étape 1 : `$global:jeton = $vieux ; Appeler-Api GET /moi` → refus attendu.
7. Extraire les événements Keycloak et les journaux de l'API.

## Résultat attendu
- Étape 3 : invalid_grant (« Maximum allowed refresh token reuse exceeded ») ; détection R4 (100106, niveau 8, T1550.001).
- Étape 5 : page Keycloak « Invalid parameter: redirect_uri » ; aucun code n'est émis.
- Étape 6 : 401 de l'API (jeton expiré).
- Étape 4 : à observer (Keycloak révoque-t-il toute la session quand il détecte un rejeu ?).
