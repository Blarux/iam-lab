#!/usr/bin/env python3
"""Revue des accès : croise Keycloak, le fichier RH et les connexions, puis produit un rapport HTML."""
import csv, datetime, html, os, time

import requests

KC, REALM = "https://sso.acmefin.test", "acmefin"
INACTIF_JOURS = float(os.environ.get("INACTIF_JOURS", "30"))
PRIVILEGIES = {"it-admin"}
INCOMPATIBLES = [{"finance-saisie", "finance-validation"}]
TECHNIQUES = {"default-roles-acmefin", "offline_access", "uma_authorization"}   # rôles par défaut, ignorés

tok = requests.post(f"{KC}/realms/{REALM}/protocol/openid-connect/token", data={
    "grant_type": "client_credentials", "client_id": "access-review",
    "client_secret": os.environ["REVIEW_SECRET"]})
tok.raise_for_status()
H = {"Authorization": f"Bearer {tok.json()['access_token']}"}


def get(path, **params):
    r = requests.get(f"{KC}/admin/realms/{REALM}/{path}", headers=H, params=params)
    r.raise_for_status()
    return r.json()


rh = {row["uid"]: row for row in csv.DictReader(open("governance/hr/rh.csv", encoding="utf-8"))}
now, lignes = time.time(), []

for u in get("users", max=1000, briefRepresentation="false"):
    uid = u["username"]
    groupes = sorted(g["name"] for g in get(f"users/{u['id']}/groups"))
    directs = sorted(r["name"] for r in get(f"users/{u['id']}/role-mappings/realm") if r["name"] not in TECHNIQUES)
    effectifs = {r["name"] for r in get(f"users/{u['id']}/role-mappings/realm/composite")} - TECHNIQUES
    login = get("events", type="LOGIN", user=u["id"], max=1)
    derniere = login[0]["time"] / 1000 if login else None

    anomalies = []
    if uid.startswith("service-account-"):
        anomalies.append("Compte technique : responsable à désigner")
    elif uid not in rh or rh[uid]["statut"] != "actif":
        anomalies.append("ORPHELIN : absent ou parti selon les RH")
    if u.get("enabled") and (derniere is None or now - derniere > INACTIF_JOURS * 86400):
        anomalies.append("Inactif ou jamais connecté")
    if any(pair <= effectifs for pair in INCOMPATIBLES):
        anomalies.append("CONFLIT SoD")
    if directs:
        anomalies.append("Rôle direct : " + ", ".join(directs))
    if effectifs & PRIVILEGIES:
        anomalies.append("Privilégié : à recertifier en priorité")

    service = (u.get("attributes", {}).get("department") or ["(inconnu)"])[0]
    quand = datetime.datetime.fromtimestamp(derniere).strftime("%Y-%m-%d %H:%M") if derniere else "—"
    lignes.append((service, uid, ", ".join(groupes), ", ".join(sorted(effectifs)), quand, anomalies))

lignes.sort()
os.makedirs("docs/revues", exist_ok=True)
fichier = f"docs/revues/revue-acces-{datetime.date.today()}.html"
with open(fichier, "w", encoding="utf-8") as f:
    f.write("<meta charset='utf-8'><title>Revue des accès AcmeFin</title>"
            "<style>body{font-family:sans-serif}td,th{border:1px solid #ccc;padding:4px 8px}"
            "table{border-collapse:collapse}.alerte{background:#fde2e2}</style>"
            f"<h1>Revue des accès AcmeFin, {datetime.date.today()}</h1>"
            "<table><tr><th>Service</th><th>Compte</th><th>Groupes</th><th>Rôles effectifs</th>"
            "<th>Dernière connexion</th><th>Anomalies</th><th>Décision du responsable</th></tr>")
    for service, uid, groupes, roles, quand, anomalies in lignes:
        classe = " class='alerte'" if any(a.split(" ")[0] in ("ORPHELIN", "CONFLIT", "Rôle") for a in anomalies) else ""
        f.write(f"<tr{classe}><td>{html.escape(service)}</td><td>{html.escape(uid)}</td>"
                f"<td>{html.escape(groupes)}</td><td>{html.escape(roles)}</td><td>{quand}</td>"
                f"<td>{'<br>'.join(html.escape(a) for a in anomalies)}</td><td>☐ conserver ☐ retirer</td></tr>")
    f.write("</table>")

print(f"{len(lignes)} comptes passés en revue ; rapport : {fichier}")
for service, uid, _, _, _, anomalies in lignes:
    graves = [a for a in anomalies if not a.startswith("Inactif")]
    if graves:
        print(f"  {uid:28} {' | '.join(graves)}")
