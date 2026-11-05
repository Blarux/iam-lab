# Résultat — Scénario 06 : élévation de privilèges et séparation des tâches

- Date : 5 novembre 2026, de 17:23:14 à 17:32:41 (heure de Paris)
- Compte : alice.martin (finance-saisie, hérité du groupe grp-finance-saisie)

## Chronologie
| Heure | Action | Résultat | Trace |
| --- | --- | --- | --- |
| 17:23:14 | Ajout direct de finance-validation à Alice (console d'administration) | rôle attribué, hors groupe (Inherited = False) | admin event CREATE REALM_ROLE_MAPPING |
| 17:23:18 | — | **alerte 100132, niveau 12** (R5, rôle sensible) | Wazuh |
| 17:30:49 | Connexion d'Alice à l'API | jeton : finance-saisie **et** finance-validation | — |
| 17:31:12 | POST /paiements/10 (saisie) | 200, statut « saisi », par alice.martin | audit API : decision « accord » |
| 17:31:16 | POST /paiements/10/validation | **403 « on ne valide pas son propre paiement »** | audit API : decision « refus », raison « auto-validation » |
| ~17:32 | Revue des accès | alice.martin : **CONFLIT SoD, Rôle direct : finance-validation** | docs/revues/revue-acces-2026-11-05.html |
| 17:32:41 | Remédiation : retrait du rôle | rôle retiré | admin event DELETE REALM_ROLE_MAPPING |

## Résultat obtenu
**Conforme à l'attendu.** Trois couches de défense ont chacune joué leur rôle :
1. **Détection** : R5 (100132, niveau 12, T1098) **4 s** après l'attribution du rôle.
2. **Prévention dans l'application** : avec ses deux rôles, Alice ne peut quand même pas valider son propre paiement. La séparation des tâches est appliquée **par transaction** (qui a saisi, qui valide), pas seulement par rôle.
3. **Gouvernance** : la revue des accès signale le conflit et l'attribution hors processus. Le relecteur peut cocher « retirer ».

Comparaison avec le processus normal : la même demande, passée par le fichier RH, avait été **refusée en amont** par le JML (SOD_REFUSE, étape 10). Le contournement par un administrateur, lui, est **détecté** (R5) et **compensé** (contrôle dans l'API, revue des accès).

## Écarts et observations
1. **Aucun écart.**
2. **Durée d'exposition : 9 min 27 s** entre l'attribution (17:23:14) et le retrait (17:32:41). En production, cette durée dépend du temps de réaction de l'équipe à l'alerte de niveau 12. L'objectif est quelques minutes, à condition que l'alerte soit surveillée.
3. **Le retrait du rôle ne déclenche pas d'alerte** (R5 ne porte que sur CREATE), mais il reste tracé dans les admin events (DELETE). La remédiation est donc auditable.
4. **L'audit de l'API trace les décisions métier** (accord et refus, avec leur motif), contrairement aux refus d'authentification du scénario 05 (401), absents de cet audit. Une seule et même API, avec deux niveaux de traçabilité.
5. **La revue signale aussi des écarts hors scénario** : frank.garnier ORPHELIN (absent ou parti selon les RH), et trois comptes privilégiés à recertifier (david.moreau, ines.robert2, julie.lambert). Ils sont traités par la revue, pas dans ce scénario.

## Preuves
- captures/1-role-ajoute.png — finance-validation, Inherited = False
- captures/2-api-403.png — saisie 200 et validation 403
- captures/3-wazuh-r5.png — alerte 100132 à 17:23:18
- captures/4-revue-acces.png — ligne d'Alice dans la revue
- captures/5-role-retire.png
- evenements.jsonl — dont les deux admin events (CREATE et DELETE)
