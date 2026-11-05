#!/usr/bin/env python3
"""Chronologie d'un scénario.
Usage : python3 scenarios/chrono.py FICHIER TYPE [liste|premier|dernier|nombre|comptes|delai HH:MM:SS.mmm]
Si REVIEW_SECRET est défini, les userId sont traduits en noms d'utilisateur (API Admin, client access-review)."""
import datetime as dt, json, os, ssl, sys, urllib.parse, urllib.request
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
KC = "https://sso.acmefin.test"

def annuaire():
    secret = os.environ.get("REVIEW_SECRET")
    if not secret:
        return {}
    ctx = ssl.create_default_context(cafile="certs/rootCA.pem")
    corps = urllib.parse.urlencode({"grant_type": "client_credentials",
                                    "client_id": "access-review", "client_secret": secret}).encode()
    jeton = json.load(urllib.request.urlopen(f"{KC}/realms/acmefin/protocol/openid-connect/token",
                                             corps, context=ctx))["access_token"]
    req = urllib.request.Request(f"{KC}/admin/realms/acmefin/users?max=1000&briefRepresentation=true",
                                 headers={"Authorization": f"Bearer {jeton}"})
    return {u["id"]: u["username"] for u in json.load(urllib.request.urlopen(req, context=ctx))}

fichier, type_ = sys.argv[1], sys.argv[2]
quoi = sys.argv[3] if len(sys.argv) > 3 else "liste"
ev = sorted((e for e in map(json.loads, open(fichier, encoding="utf-8")) if e.get("type") == type_),
            key=lambda e: e["time"])
if not ev:
    sys.exit(f"Aucun événement {type_} dans {fichier}")
NOMS = annuaire() if quoi in ("liste", "comptes") else {}
heure = lambda e: dt.datetime.fromtimestamp(e["time"] / 1000, PARIS)
compte = lambda e: (e.get("details", {}).get("username") or NOMS.get(e.get("userId"))
                    or e.get("userId", "?")[:8])

if quoi == "premier":
    print(heure(ev[0]).strftime("%H:%M:%S"))
elif quoi == "dernier":
    print(heure(ev[-1]).strftime("%H:%M:%S"))
elif quoi == "nombre":
    print(len(ev))
elif quoi == "comptes":
    print(", ".join(sorted({compte(e) for e in ev})))
elif quoi == "delai":
    alerte = dt.datetime.combine(heure(ev[-1]).date(), dt.time.fromisoformat(sys.argv[4]), PARIS)
    print(round((alerte - heure(ev[-1])).total_seconds()))
else:
    for e in ev:
        print(heure(e).strftime("%H:%M:%S.%f")[:-3], compte(e), e.get("error", ""), e.get("ipAddress", ""))
