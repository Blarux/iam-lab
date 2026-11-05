# Résultat — Scénario 02 : mot de passe volé

- Date : 5 novembre 2026, de 15:35:15 à 15:36:35 (heure de Paris)
- Compte visé : alice.martin — IP 172.18.0.1 — client account-console

## Chronologie (evenements.jsonl)
| Heure | Événement | Erreur |
| --- | --- | --- |
| 15:35:15.866 | 1er code TOTP faux (après le bon mot de passe) | invalid_user_credentials |
| 15:35:17.373 | 2e code faux | invalid_user_credentials |
| 15:35:18.610 | 3e code faux | invalid_user_credentials |
| 15:36:28.266 | 4e code faux | invalid_user_credentials |
| 15:36:28.284 | **Verrouillage temporaire** (USER_DISABLED_BY_TEMPORARY_LOCKOUT) | — |
| 15:36:29.872 | Nouvel essai pendant le verrouillage | user_temporarily_disabled |
| 15:36:35.969 | Nouvel essai pendant le verrouillage | user_temporarily_disabled |
| 15:36:35.975 | Session de connexion invalidée | invalid_authentication_session |

## Résultat obtenu
- Prévention : **connexion refusée au second facteur** malgré le bon mot de passe. Conforme à l'attendu.
- Détection : 100103 (niveau 6) pour chaque échec, R2 (100111, niveau 10, T1078 + T1621) à 15:36:45, et 100105 (verrouillage, niveau 10, T1110) à 15:36:45.
- Délai de détection : 17 s entre l'événement déclencheur (15:36:28) et les alertes R2 et 100105.

## Écarts et observations
1. **Écart : verrouillage alors que le protocole prévoyait « pas de verrouillage ».** alice.martin faisait partie des 5 comptes du scénario 01 (échec à 15:22:18). Keycloak conserve le compteur d'échecs (Failure Reset Time : 12 h par défaut), et ce compteur est commun au mot de passe et au second facteur. 1 + 4 = 5 échecs : le verrouillage s'est déclenché. **Conclusion : les échecs s'additionnent d'une attaque à l'autre.** Un attaquant qui pulvérise puis s'acharne sur un compte se fait verrouiller plus tôt. Le protocole n'a pas été modifié après coup : l'écart est documenté ici.
2. **Écart : R2 s'est déclenchée au 4e échec et non au 3e.** Les 3 premiers échecs sont arrivés ensemble dans Wazuh (lot de 15:35:41) sans déclencher R2. R2 s'est déclenchée sur le 4e (15:36:28), soit 87 s après le 3e échec. Si l'attaquant s'était arrêté à 3 essais, R2 ne se serait pas déclenchée, mais les trois alertes 100103 de niveau 6 resteraient visibles.
3. **Le verrouillage est invisible pour l'attaquant.** Pendant le verrouillage, l'écran affiche toujours « Invalid authenticator code. ». L'attaquant ne peut pas savoir s'il a été bloqué ni si un code était juste.
4. **Le verrouillage peut servir d'arme.** 5 essais suffisent à bloquer n'importe quel compte : un attaquant peut ainsi empêcher un salarié de travailler (déni de service, MITRE T1531). C'est pourquoi le verrouillage est **temporaire** et non permanent. La détection R1/R2 permet de repérer cet usage.

## Preuves
- captures/1-utilisateur.png — « Invalid authenticator code. »
- captures/2-keycloak-events.png — LOGIN_ERROR et USER_DISABLED_BY_TEMPORARY_LOCKOUT
- captures/3-wazuh-alerte.png — 100103, 100105 et 100111
- captures/4-wazuh-detail-r2.png — détail de R2 (selected_credential_id, MITRE T1078/T1621, previous_output)
- evenements.jsonl — événements Keycloak bruts

## Contre-essai : cause de l'écart 2
**Test A — règles isolées (wazuh-logtest).** On rejoue les événements un par un. Les 4 échecs d'Alice donnent 100103, 100103, **100111**, 100103 : R2 se déclenche sur le 3e. Les 5 échecs du scénario 01 donnent 100110 sur le 5e. **Les règles sont correctes.**

**Test B — 3 échecs espacés d'environ 35 s (15:48–15:50).** Chaque échec arrive dans un lot de collecte différent.

| Échec (Keycloak) | Lot Wazuh | Alerte |
| --- | --- | --- |
| 15:48:30.675 | 15:49:01 | 100103 (+ 100105 : compte reverrouillé) |
| 15:49:04.297 | 15:49:33 | 100103 (user_temporarily_disabled) |
| 15:49:42.622 | 15:50:04 | **100111 (R2)** (+ 100105) |

R2 se déclenche sur le 3e échec, 22 s après celui-ci.

**Conclusion.** Si les 3 échecs arrivent dans des lots différents, R2 se déclenche. S'ils arrivent dans le même lot (essai initial, 3 codes en 3 s), elle ne se déclenche pas. La cause la plus probable : wazuh-analysisd traite en parallèle les événements qui arrivent au même instant. En évaluant l'un d'eux, il ne compte pas encore les autres dans la fenêtre de corrélation. Limite de la démonstration : un seul essai de chaque sorte. Une seconde mesure est faite au scénario 03.

**Conséquence.** Un script qui enchaîne ses essais très vite passe sous R2, alors qu'un humain plus lent est détecté. Seules les règles de corrélation (frequency) sont touchées. Les règles qui portent sur un seul événement (100103, 100105) ne le sont pas.

**Parades.**
- Le filet de sécurité est déjà en place : verrouillage par Keycloak à 5 échecs et alerte 100105, qui porte sur un seul événement et ne dépend donc pas de l'arrivée en lot.
- Réduire l'intervalle de collecte (de 30 s à 5 s) : les lots seront plus petits, mais un script très rapide restera sous le seuil.
- Rendre la corrélation séquentielle (réglage du traitement en parallèle de wazuh-analysisd), ou faire la corrélation plus tôt, dans le collecteur.
- Leçon de méthode : valider une règle avec wazuh-logtest ne suffit pas. Il faut aussi la tester dans les conditions réelles de collecte.

5. **Observation : au-delà du seuil, chaque échec reverrouille le compte.** Le compteur ne revient à zéro qu'après une connexion réussie, un déverrouillage par l'administrateur ou 12 h d'attente (Failure Reset Time). Pendant le contre-essai, le compteur d'Alice était resté au-dessus de 5 : chaque échec l'a reverrouillée pour 1 minute (Wait Increment).

## Preuves du contre-essai
- captures/5-wazuh-contre-essai.png (capture non conservée) — trois lots distincts, R2 à 15:50:04
- evenements-contre-essai.jsonl
