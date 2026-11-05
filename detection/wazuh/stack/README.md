# Stack Wazuh (single-node)

Source : wazuh-docker, tag v4.14.10, images ramenées en 4.14.9 (les images 4.14.10 n'étaient pas publiées).

Modifications apportées :
- docker-compose.yml : ports liés à 127.0.0.1 ; montage de detection/events (lecture seule) et de detection/wazuh/rules (dossier entier, pour éviter le piège de l'inode).
- wazuh_manager.conf : bloc localfile (JSON) pour /var/log/keycloak-events/events.json ; détection de vulnérabilités désactivée (incident du 5 novembre : 10 Go retéléchargés en boucle, disque C: plein).

Les mots de passe sont masqués (A_DEFINIR_HORS_DEPOT) : les valeurs réelles restent dans ~/wazuh-docker. Les certificats de Wazuh ne sont pas versionnés.
