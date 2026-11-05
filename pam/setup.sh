#!/usr/bin/env bash
until curl -sf --cacert certs/rootCA.pem https://sso.acmefin.test/realms/acmefin/.well-known/openid-configuration >/dev/null; do echo "En attente de Keycloak..."; sleep 3; done; echo "Keycloak prêt"
# Configure OpenBao. Mode développement : à relancer après chaque redémarrage du conteneur.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
bao() { docker compose exec -T -e BAO_ADDR=http://127.0.0.1:8200 -e BAO_TOKEN="$BAO_ROOT_TOKEN" openbao bao "$@"; }

echo "1. Autorité de certification SSH"
bao secrets enable -path=ssh-client ssh || true
bao write ssh-client/config/ca generate_signing_key=true || true
bao read -field=public_key ssh-client/config/ca > pam/srv-01/trusted-user-ca.pem

echo "2. Rôle de signature : compte admin, 30 minutes, identité du demandeur dans le certificat"
bao write ssh-client/roles/admin - <<'EOF'
{
  "key_type": "ca",
  "allow_user_certificates": true,
  "allowed_users": "admin",
  "default_user": "admin",
  "ttl": "30m",
  "max_ttl": "1h",
  "key_id_format": "{{token_display_name}}",
  "default_extensions": {"permit-pty": ""}
}
EOF

echo "3. Politique : le seul droit accordé est de faire signer une clé"
bao policy write ssh-admin - <<'EOF'
path "ssh-client/sign/admin" { capabilities = ["update"] }
EOF

echo "4. Connexion déléguée à Keycloak, réservée au rôle it-admin"
bao auth enable oidc || true
bao write auth/oidc/config \
  oidc_discovery_url="https://sso.acmefin.test/realms/acmefin" \
  oidc_discovery_ca_pem=@/certs/rootCA.pem \
  oidc_client_id=openbao oidc_client_secret="$OPENBAO_OIDC_SECRET" \
  default_role=it-admin
bao write auth/oidc/role/it-admin - <<'EOF'
{
  "user_claim": "preferred_username",
  "bound_claims": {"roles": ["it-admin"]},
  "allowed_redirect_uris": ["http://localhost:8250/oidc/callback"],
  "token_policies": ["ssh-admin"],
  "token_ttl": "30m",
  "oidc_scopes": ["openid"]
}
EOF

echo "5. Journal d'audit (dans les journaux du conteneur)"
bao audit enable file file_path=stdout || true

echo "6. Démarrage de srv-01 avec la clé de l'autorité"
docker compose up -d --build srv-01
echo "Terminé."
