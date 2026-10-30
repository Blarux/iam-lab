"""API de paiements AcmeFin : un serveur de ressources qui vérifie lui-même les jetons."""
import json
import time

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ISSUER = "https://sso.acmefin.test/realms/acmefin"
AUDIENCE = "acmefin-api"
jwks = jwt.PyJWKClient(f"{ISSUER}/protocol/openid-connect/certs")   # clés publiques de Keycloak, mises en cache
bearer = HTTPBearer(auto_error=False)
app = FastAPI(title="API paiements AcmeFin")
paiements: dict[int, str] = {}   # numéro de paiement -> qui l'a saisi (en mémoire, suffisant pour la démo)


def audit(utilisateur, action, paiement, decision, raison=""):
    """Une ligne JSON par décision : la trace que Wazuh pourra lire plus tard."""
    print(json.dumps({"time": int(time.time()), "source": "acmefin-api", "user": utilisateur,
                      "action": action, "paiement": paiement, "decision": decision, "raison": raison}), flush=True)


def claims(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if cred is None:   # pas de jeton : on ne sait pas qui appelle -> 401
        raise HTTPException(401, "jeton absent", headers={"WWW-Authenticate": "Bearer"})
    try:
        key = jwks.get_signing_key_from_jwt(cred.credentials).key
        # signature, émetteur, audience et expiration vérifiés en un seul appel
        return jwt.decode(cred.credentials, key, algorithms=["RS256"], audience=AUDIENCE, issuer=ISSUER,
                          options={"require": ["exp", "iat", "iss", "aud", "sub"]})
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"jeton refusé : {e}", headers={"WWW-Authenticate": "Bearer"})


def require(role: str):
    def check(c: dict = Depends(claims)) -> dict:
        if role not in c.get("realm_access", {}).get("roles", []):   # authentifié mais pas autorisé -> 403
            audit(c.get("preferred_username"), f"exiger {role}", None, "refus", "rôle absent")
            raise HTTPException(403, f"rôle {role} requis")
        return c
    return check


@app.get("/moi")
def moi(c: dict = Depends(claims)):
    return {"utilisateur": c["preferred_username"], "roles": c.get("realm_access", {}).get("roles", []),
            "expire_dans_s": c["exp"] - int(time.time())}


@app.post("/paiements/{pid}")
def saisir(pid: int, c: dict = Depends(require("finance-saisie"))):
    paiements[pid] = c["preferred_username"]
    audit(c["preferred_username"], "saisir", pid, "accord")
    return {"paiement": pid, "statut": "saisi", "par": c["preferred_username"]}


@app.post("/paiements/{pid}/validation")
def valider(pid: int, c: dict = Depends(require("finance-validation"))):
    if pid not in paiements:
        raise HTTPException(404, "paiement inconnu")
    if paiements[pid] == c["preferred_username"]:   # séparation des tâches au niveau métier
        audit(c["preferred_username"], "valider", pid, "refus", "auto-validation")
        raise HTTPException(403, "on ne valide pas son propre paiement")
    audit(c["preferred_username"], "valider", pid, "accord")
    return {"paiement": pid, "statut": "validé", "par": c["preferred_username"]}
