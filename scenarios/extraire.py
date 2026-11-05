#!/usr/bin/env python3
"""Extrait les événements Keycloak des N dernières minutes, comme preuve d'un scénario."""
import json, sys, time
minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 10
limite = (time.time() - minutes * 60) * 1000
for ligne in open("detection/events/events.json", encoding="utf-8"):
    e = json.loads(ligne)
    if e["time"] >= limite and e.get("type") != "CLIENT_LOGIN":
        print(json.dumps(e, ensure_ascii=False))
