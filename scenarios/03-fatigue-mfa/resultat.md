# Résultat — Scénario 03 : fatigue MFA

- Date : 5 novembre 2026, de 16:47:41 à 16:48:07 (heure de Paris)
- Compte : alice.martin (compteur d'échecs remis à zéro par une connexion réussie juste avant ; confirmé par num_failures = 2) — IP 172.18.0.1

## Chronologie (evenements.jsonl)
| Heure | Événement | Erreur |
| --- | --- | --- |
| 16:47:41.297 | 1er code TOTP faux | invalid_user_credentials |
| 16:47:42.025 | 2e code faux, 728 ms plus tard | invalid_user_credentials |
| 16:47:42.031 | **Verrouillage** (USER_DISABLED_BY_TEMPORARY_LOCKOUT, num_failures 2, levée à 16:48:42) | — |
| 16:47:42.593 → 16:47:43.679 | 3e à 5e codes faux, pendant le verrouillage | user_temporarily_disabled, invalid_authentication_session |
| 16:48:07.542 | **Le bon code** | **user_temporarily_disabled : refusé** |

## Résultat obtenu
- Fatigue MFA (notifications en boucle) : **impossible par conception**. Le lab n'envoie aucune notification à faire accepter. Si des notifications étaient ajoutées un jour, la parade serait l'appariement par numéro (number matching).
- Deviner le code TOTP : **bloqué dès le 2e essai** ; le bon code est ensuite refusé lui aussi. Prévention meilleure que prévu (voir écart 1).
- Passkey : liée au domaine sso.acmefin.test (capture 4). Le navigateur refuse de la présenter à tout autre domaine : un faux site ne peut pas l'obtenir.
- Détection : 100105 (niveau 10, T1110) à 16:47:45, **3 s** après le verrouillage. R2 ne s'est pas déclenchée (voir écart 2).

## Écarts et observations
1. **Écart : verrouillage après 2 échecs au lieu de 5.** Les deux premiers codes sont arrivés à 728 ms d'intervalle. Ce délai est inférieur au Quick Login Check de Keycloak (1 000 ms), une seconde protection anti-automatisation qui verrouille le compte pour au moins 1 minute (Minimum Quick Login Wait). Au scénario 02, les codes étaient espacés de 1,2 à 1,5 s : seul le seuil de 5 échecs s'appliquait. **Conséquence chiffrée** : un code TOTP à 6 chiffres compte 1 000 000 valeurs, dont environ 3 sont acceptées à un instant donné. Avec des verrouillages de plus en plus longs (jusqu'à 15 min), l'attaquant n'a que quelques essais par quart d'heure. Il lui faudrait de l'ordre de plusieurs années pour tomber sur le bon code, et il serait détecté dès les premières minutes.
2. **Écart : R2 ne s'est pas déclenchée (seconde mesure de l'écart 2 du scénario 02).** Sept échecs au second facteur en 26 s, répartis sur deux lots de collecte (16:47:45 et 16:48:15), sans aucune alerte R2. Cela confirme l'écart du scénario 02, et va plus loin : cette fois, même les événements du lot suivant n'ont pas déclenché la règle. L'explication « même lot » ne couvre donc pas tout. Le mécanisme exact dans wazuh-analysisd n'est pas établi (voir le test logtest ci-dessous). **Conclusion pratique : R2 n'est pas fiable face à une rafale rapide.** Le signal fiable est le verrouillage (100105), qui porte sur un seul événement et s'est déclenché en 3 s.
### Test logtest (écart 2)
Les 9 mêmes LOGIN_ERROR, rejoués un par un dans wazuh-logtest, donnent : 100103, 100103, **100111**, 100103, 100103, **100111**, 100103, 100103, **100111**. R2 se déclenche bien sur le 3e échec, tous types d'erreur confondus (invalid_user_credentials, user_temporarily_disabled, invalid_authentication_session). **La règle est correcte. Le défaut vient du traitement en temps réel par wazuh-analysisd**, reproduit dans deux scénarios (02 et 03). Seconde différence observée : logtest ignore le paramètre ignore="300" (trois déclenchements de suite), alors que le gestionnaire réel l'applique. Valider une règle avec logtest ne suffit donc pas.

3. **Le verrouillage reste invisible pour l'attaquant**, comme au scénario 02 : l'écran affiche le même message que pour un code faux.
4. **Méthode** : deux échecs étrangers au scénario (camille.michel à 16:41, clara.roux à 16:42) ont été retirés des preuves. Le fichier evenements.jsonl ne contient que les événements à partir de 16:47.

## Preuves
- captures/1-utilisateur.png — le bon code refusé
- captures/2-keycloak-events.png — LOGIN_ERROR et verrouillage
- captures/3-wazuh-alerte.png — 100105 et les 100103, sans R2
- captures/4-passkey-domaine.png — passkey liée à sso.acmefin.test
- evenements.jsonl
