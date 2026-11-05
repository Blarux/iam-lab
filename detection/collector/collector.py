#!/usr/bin/env python3
"""Collecteur : lit les événements de Keycloak toutes les 30 s et les écrit en JSON, une ligne par événement."""
import json, os, time

import requests

KC, REALM = "https://sso.acmefin.test", "acmefin"
OUT = "/var/log/keycloak-events/events.json"
jeton, expiration = None, 0


def entetes():
    """Réutilise le jeton tant qu'il est valide : moins d'événements CLIENT_LOGIN parasites."""
    global jeton, expiration
    if time.time() > expiration - 30:
        r = requests.post(f"{KC}/realms/{REALM}/protocol/openid-connect/token", data={
            "grant_type": "client_credentials", "client_id": "event-collector",
            "client_secret": os.environ["COLLECTOR_SECRET"]}, timeout=10)
        r.raise_for_status()
        jeton, expiration = r.json()["access_token"], time.time() + r.json()["expires_in"]
    return {"Authorization": f"Bearer {jeton}"}


last = {"events": time.time() * 1000, "admin-events": time.time() * 1000}
print("Collecteur démarré", flush=True)
while True:
    try:
        with open(OUT, "a", encoding="utf-8") as out:
            for path in last:
                r = requests.get(f"{KC}/admin/realms/{REALM}/{path}", params={"max": 500}, headers=entetes(), timeout=10)
                r.raise_for_status()
                for e in sorted(r.json(), key=lambda e: e["time"]):
                    if e["time"] > last[path]:
                        e["source"] = "keycloak-admin" if path == "admin-events" else "keycloak"
                        out.write(json.dumps(e, ensure_ascii=False) + "\n")
                        last[path] = e["time"]
    except Exception as exc:
        print(f"Erreur : {exc}", flush=True)
    time.sleep(30)
