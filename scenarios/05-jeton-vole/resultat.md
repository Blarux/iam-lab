# Résultat — Scénario 05 : jeton volé ou rejoué

- Date : 5 novembre 2026, de 16:59:51 à 17:12:55 (heure de Paris)
- Compte : chloe.dubois (passkey) — client api-tester — jeton : aud acmefin-api, rôle finance-saisie

## Chronologie
| Heure | Étape | Réponse | Événement Keycloak |
| --- | --- | --- | --- |
| 16:59:51 | 1. Connexion, jetons mis de côté | — | — |
| ~17:00:00 | 2. Usage légitime du refresh token | OK, nouveaux jetons | **aucun** (REFRESH_TOKEN non enregistré) |
| 17:00:04.911 | 3. Rejeu du refresh token volé | 400 invalid_grant « Maximum allowed refresh token reuse exceeded » | REFRESH_TOKEN_ERROR (invalid_token) |
| 17:00:09.651 | 4. Nouveau refresh token légitime | 400 invalid_grant « Session doesn't have required client » | REFRESH_TOKEN_ERROR (invalid_token) |
| 17:00:21.588 | 5. redirect_uri vers https://attaquant.example/callback | « Invalid parameter: redirect_uri » | LOGIN_ERROR (invalid_redirect_uri) |
| 17:12:55 | 6. Access token de 13 min | 401 « jeton refusé : Signature has expired » | — (refus côté API) |

## Résultat obtenu
- Prévention : **les 4 tentatives sont bloquées.** Conforme à l'attendu.
- Détection : R4 (100106, niveau 8, T1550.001), deux alertes à 17:00:17, soit **8 s** après le second refus. Détournement de redirect_uri : 100102 seulement (niveau 5, générique). Jeton expiré : **aucune alerte**.

## Écarts et observations
1. **Un rejeu invalide toute la famille de jetons (étape 4).** Quand Keycloak détecte le rejeu, il retire le client api-tester de la session de Chloé : son refresh token légitime est refusé aussi. C'est la recommandation de l'OAuth 2.0 Security BCP (RFC 9700) : en cas de rejeu, on ne peut pas savoir qui est le voleur, donc on révoque tout. Si l'attaquant utilise le jeton volé **en premier**, il obtient des jetons valides. Mais le prochain rafraîchissement de la victime échoue : R4 se déclenche et la session est révoquée pour les deux. **La rotation transforme un vol silencieux en collision détectable.**
2. **Un access token volé reste utilisable jusqu'à son expiration.** L'API vérifie les jetons localement (signature, exp, aud, iss), sans interroger Keycloak : révoquer la session ne l'arrête pas. Sa durée de 5 min est la seule limite. C'est le compromis des jetons JWT autonomes (alternative : l'introspection, au prix d'un appel à chaque requête).
3. **Angle mort : l'usage réussi d'un refresh token n'est pas journalisé.** REFRESH_TOKEN ne fait pas partie des événements enregistrés : on voit la collision, pas l'usage du voleur. L'enregistrer coûterait un événement par utilisateur toutes les 5 min. Une piste : l'enregistrer pour l'investigation, avec une règle Wazuh de niveau 0.
4. **Les REFRESH_TOKEN_ERROR ne contiennent pas d'identifiant d'utilisateur.** R4 indique le client, pas la victime. Pour l'investigation, il faut recouper avec l'IP et l'heure.
5. **Le détournement de redirect_uri est bloqué avant toute authentification**, donc aucun code n'est émis. Mais il ne produit qu'une alerte générique de niveau 5, alors qu'un utilisateur légitime ne déclenche jamais cette erreur : c'est un signal fort. Amélioration : une règle dédiée à invalid_redirect_uri (T1528, niveau 8 ou plus).
6. **Angle mort : les refus de l'API.** Le 401 de l'étape 6 n'apparaît que dans le journal d'accès d'uvicorn (« GET /moi 401 »), sans identité, et les journaux de l'API ne sont pas transmis à Wazuh. Amélioration : journaliser chaque refus dans l'audit de l'API (motif, sub si disponible) et collecter ces journaux. **On ne détecte que ce qu'on journalise.**
7. **Méthode :** les trois alertes R4 de 16:58:17 viennent d'un essai antérieur au scénario et sont exclues.

## Preuves
- captures/1-powershell.png — étapes 1 à 4 (réponses de Keycloak)
- captures/2-redirect-uri.png — « Invalid parameter: redirect_uri »
- captures/3-api-401.png — « Signature has expired »
- captures/4-extraction.png — chronologie et journal de l'API
- captures/5-wazuh-r4.png — deux alertes R4 à 17:00:17
- evenements.jsonl
