# Mesures avant / après

« Avant » = valeurs observées pendant le projet, avant chaque correction, ou valeurs par défaut de Keycloak (voir le journal de bord). « Après » = valeurs mesurées pendant l'étape 11, le 5 novembre 2026.

| Indicateur | Avant | Après | Comment c'est mesuré |
| --- | --- | --- | --- |
| Connexions exigeant un second facteur | 0 % (mot de passe seul) | 100 % | Structure des flux acmefin-browser et acmefin-admin |
| Comptes ayant enregistré un second facteur | 0 |  | governance/mfa_coverage.py (enrôlement à la première connexion : seuls les comptes déjà utilisés) |
| Départ RH → plus de connexion SSO | manuel, non défini | < 1 s | Scénario 04, contre-essai (KC_DESACTIVATION) |
| Départ RH → perte de la session Nextcloud ouverte | session conservée (étape 10 ; scénario 04, essai 1) | 2 s | Scénario 04, contre-essai (NEXTCLOUD_DESACTIVATION, puis F5) |
| Départ RH → tous les accès coupés, délai réel du contre-essai | — | 3 min 13 s | Deux plantages du JML avant la correction finale (scénario 04) |
| Refresh token rejoué accepté | oui (rotation désactivée par défaut) | non, et toute la famille de jetons est révoquée | Scénario 05 |
| Access token volé : durée d'utilisation possible | 5 min (défaut Keycloak) | 5 min, non révocable (validation locale) | Scénario 05 |
| Rôles transmis à Nextcloud pour Alice | 7 | 1 | Fiche Nextcloud, étapes 5B et 7 |
| Accès à Gitea pour un profil non autorisé | oui (étape 5) | non | Test d'Alice, étape 7 |
| Accès permanents à srv-01 | clés permanentes (modèle classique) | 0 (certificats de 30 min) | Journal de srv-01, étape 8 |
| Rôle sensible attribué hors processus : délai de détection | non détecté | 4 s | Scénario 06 (R5) |
| Scénarios bloqués ou détectés | — | 6 / 6 | Dossiers scenarios/ (01 détecté mais non bloqué ; 04 après correction du JML) |
| Délai de détection par scénario | — | 01 : 21 s · 02 : 17 s · 03 : 3 s · 05 : 8 s · 06 : 4 s | Heure de l'événement Keycloak comparée à l'heure de l'alerte Wazuh |
| Délai moyen de détection | — | 10,6 s (médiane 8 s) | Moyenne des 5 scénarios ci-dessus ; la collecte toutes les 30 s en est la limite haute |
| Fiabilité de R2 (corrélation sur 3 échecs) | — | 2 essais sur 3 ; aucune détection pour une rafale de moins de 3 s | Scénarios 02, 02 bis et 03, avec le test logtest |
