# Résultat — Scénario 01 : pulvérisation de mots de passe

- Date : 5 novembre 2026, de 15:21:50 à 15:22:34 (heure de Paris)
- Comptes visés (5) : alice.martin, bruno.leroy, camille.michel, chloe.dubois, david.moreau
- IP source vue par Keycloak : 172.18.0.1 — client : account-console

## Résultat obtenu
- Prévention : aucun compte verrouillé (un échec par compte, seuil à 5). **Conforme à l'attendu** : la limite du verrouillage par compte est démontrée.
- Détection : alerte R1 (100110, niveau 12, T1110.003) à 15:22:55, précédée des 5 échecs (100102, niveau 5).
- Délai de détection : **21 s** entre le 5e échec et l'alerte.

## Écarts et observations
1. Aucun écart avec le résultat attendu.
2. **L'IP source est la passerelle Docker (172.18.0.1).** Dans le lab, tout le trafic venant de Windows arrive par la passerelle du réseau Docker, et Caddy transmet cette adresse à Keycloak (X-Forwarded-For). Tous les utilisateurs partagent donc la même IP. R1 se déclencherait aussi si 5 vrais salariés se trompaient de mot de passe en 2 minutes. C'est le même risque de faux positif que derrière le NAT d'une entreprise. En production, il faut lister les IP de sortie connues, ou relever le seuil pour elles.
3. **Le délai dépend surtout de la collecte.** Wazuh horodate à l'ingestion : les lots arrivent à 15:21:51, 15:22:23 et 15:22:55, soit environ toutes les 32 s, ce qui correspond au relevé du collecteur toutes les 30 s. Les événements d'un même lot portent donc la même heure dans Wazuh. L'heure réelle se trouve dans le champ time de Keycloak. Un event listener Keycloak qui pousse les événements en temps réel réduirait ce délai à quelques secondes.
4. **Bruit RESTART_AUTHENTICATION (niveau 3).** Il est produit par le clic sur ↻ entre deux comptes. C'est un artefact de la méthode de test : un script d'attaque ne le produirait pas.

## Pistes d'amélioration
- Limiter le débit de connexion par IP en amont (WAF ou limitation de débit sur le reverse proxy) : Keycloak ne verrouille que par compte.
- Interdire les mots de passe courants : politique de mots de passe Keycloak « Password Blacklist ».
- Généraliser les passkeys : sans mot de passe, la pulvérisation n'a plus d'objet.

## Preuves
- captures/1-utilisateur.png — page « Invalid password. »
- captures/2-keycloak-events.png — 5 LOGIN_ERROR, 5 comptes, même IP
- captures/3-wazuh-alerte.png — alerte 100110 à 15:22:55
- captures/4-wazuh-detail-r1.png — détail de l'alerte (MITRE T1110.003, ipAddress)
- evenements.jsonl — événements Keycloak bruts
