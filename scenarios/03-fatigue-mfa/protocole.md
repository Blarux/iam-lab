# Scénario 03 — Fatigue MFA (MFA bombing)

## Objectif
Montrer que l'attaque par fatigue MFA n'a pas de prise sur le lab, et que les attaques qui s'en rapprochent (deviner le code, détourner une passkey) sont bloquées.

## Technique MITRE ATT&CK
T1621 — Multi-Factor Authentication Request Generation ; T1110 — Brute Force (sur le code TOTP).

## Hypothèse de l'attaquant
Il a le mot de passe d'Alice. Avec un second facteur à notification (Approuver / Refuser), il enverrait des demandes en boucle jusqu'à ce qu'elle accepte. Ici, le second facteur est un code TOTP ou une passkey : il n'y a **aucune notification à faire accepter**. Il lui reste deux options : deviner le code, ou piéger une passkey sur un faux site.

## Prérequis
- alice.martin a un TOTP enregistré. Son compteur d'échecs a été remis à zéro par une connexion réussie (elle a servi aux scénarios 01 et 02). chloe.dubois, prévue au départ, n'a qu'une passkey : il n'y a aucun code à deviner, l'attaque ne s'applique pas.
- Plus de 5 minutes se sont écoulées depuis la dernière alerte R2 (ignore="300").
- Verrouillage par Keycloak à 5 échecs ; règle 100105.

## Étapes
1. Fenêtre InPrivate, https://sso.acmefin.test/realms/acmefin/account, alice.martin, choisir mot de passe + OTP, saisir le bon mot de passe.
2. Saisir **5 codes faux le plus vite possible** (moins de 10 s).
3. Saisir ensuite le **bon** code TOTP : il doit être refusé, car le compte est verrouillé.
4. Ouvrir les Paramètres de Windows > Comptes > Clés d'accès : la passkey d'Alice est liée au domaine sso.acmefin.test.
5. Extraire les preuves, puis déverrouiller Alice (Users > alice.martin > Temporarily locked).

## Résultat attendu
- Fatigue MFA : **impossible par conception**, car il n'y a pas de notification. Si des notifications existaient un jour, la parade serait l'appariement par numéro (number matching).
- Deviner le code : verrouillage après 5 échecs ; même le bon code est ensuite refusé.
- Passkey : liée au domaine sso.acmefin.test. Le navigateur refuse de la présenter sur un autre domaine, donc un faux site ne peut pas l'obtenir.
- Détection : 100105 (verrouillage, niveau 10). R2 : **mesure de l'écart 2** du scénario 02. Avec 5 échecs dans le même lot, R2 ne devrait pas se déclencher.
