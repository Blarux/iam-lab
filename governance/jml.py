#!/usr/bin/env python3
"""Processus JML : applique les arrivées, mutations et départs du fichier RH.
Simulation par défaut ; l'option --apply applique réellement les changements."""
import subprocess
import os as _os
_os.environ.setdefault("REQUESTS_CA_BUNDLE", "certs/rootCA.pem")  # AC du lab, même sans export
import csv, datetime, json, os, secrets, sys

import requests
from ldap3 import MODIFY_ADD, MODIFY_DELETE, Connection, Server

BASE = "dc=acmefin,dc=test"
PEOPLE, GROUPS, DEPARTS = f"ou=people,{BASE}", f"ou=groups,{BASE}", f"ou=departs,{BASE}"
KC, REALM = "https://sso.acmefin.test", "acmefin"
INCOMPATIBLES = [{"grp-finance-saisie", "grp-finance-validation"}]
APPLY = "--apply" in sys.argv

ldap = Connection(Server("ldap://localhost:389"), f"cn=admin,{BASE}",
                  os.environ["LDAP_ADMIN_PASSWORD"], auto_bind=True)


def log(action, uid, **details):
    """Une ligne JSON par décision : c'est la piste d'audit du processus."""
    entry = {"time": datetime.datetime.now().isoformat(timespec="seconds"),
             "action": action, "uid": uid, "applied": APPLY, **details}
    print(json.dumps(entry, ensure_ascii=False))
    with open("governance/jml-log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def ldap_ok(uid, operation):
    if ldap.result["result"] != 0:
        log("LDAP_ERREUR", uid, operation=operation, message=ldap.result["description"])


def dn(uid):
    return f"uid={uid},{PEOPLE}"


def current_groups():
    """uid -> ensemble de ses groupes, d'après l'annuaire."""
    ldap.search(GROUPS, "(objectClass=groupOfNames)", attributes=["cn", "member"])
    state = {}
    for g in ldap.entries:
        for m in g.member.values:
            if m.endswith(PEOPLE):
                state.setdefault(m.split(",")[0][4:], set()).add(g.cn.value)
    return state


def set_membership(uid, group, op):
    ldap.modify(f"cn={group},{GROUPS}", {"member": [(op, [dn(uid)])]})
    ldap_ok(uid, f"groupe {group}")


def kc_sessions(uid, disable=False):
    """Ferme toutes les sessions Keycloak de la personne (et désactive son compte si demandé)."""
    tok = requests.post(f"{KC}/realms/{REALM}/protocol/openid-connect/token", data={
        "grant_type": "client_credentials", "client_id": "jml-bot",
        "client_secret": os.environ["JML_SECRET"]})
    tok.raise_for_status()
    h = {"Authorization": f"Bearer {tok.json()['access_token']}"}
    users = requests.get(f"{KC}/admin/realms/{REALM}/users", headers=h,
                         params={"username": uid, "exact": "true"}).json()
    if not users:
        log("KC_INTROUVABLE", uid, status=404)
    for u in users:
        if disable:
            r = requests.put(f"{KC}/admin/realms/{REALM}/users/{u['id']}", json={"enabled": False}, headers=h)
            log("KC_DESACTIVATION", uid, status=r.status_code)
        r = requests.post(f"{KC}/admin/realms/{REALM}/users/{u['id']}/logout", headers=h)
        log("KC_SESSIONS_FERMEES", uid, status=r.status_code)

def nextcloud_disable(uid):
    """Déprovisionnement applicatif : coupe aussi les sessions déjà ouvertes dans Nextcloud."""
    r = subprocess.run(["docker", "compose", "exec", "-T", "-u", "www-data", "nextcloud",
                        "php", "occ", "user:disable", uid], capture_output=True, text=True)
    log("NEXTCLOUD_DESACTIVATION", uid, status=r.returncode, message=(r.stdout or r.stderr).strip())

state = current_groups()
for row in csv.DictReader(open("governance/hr/rh.csv", encoding="utf-8")):
    uid, target = row["uid"], set(filter(None, row["groupes"].split(";")))
    before = state.get(uid)

    if row["statut"] == "parti":
        if before is not None:                                        # LEAVER
            log("LEAVER", uid, groupes_retires=sorted(before))
            if APPLY:
                # 1. Applications d'abord, tant que Keycloak voit encore le compte dans l'annuaire
                kc_sessions(uid, disable=True)
                nextcloud_disable(uid)
                # 2. Puis l'annuaire
                for g in before:
                    set_membership(uid, g, MODIFY_DELETE)
                ldap.modify(dn(uid), {"userPassword": [(MODIFY_DELETE, [])]})   # plus aucun mot de passe valide
                ldap_ok(uid, "suppression du mot de passe")
                ldap.modify_dn(dn(uid), f"uid={uid}", new_superior=DEPARTS)
                ldap_ok(uid, "déplacement vers ou=departs")
        continue

    if any(pair <= target for pair in INCOMPATIBLES):                 # séparation des tâches
        log("SOD_REFUSE", uid, groupes_demandes=sorted(target))
        continue

    if before is None:                                                # JOINER
        log("JOINER", uid, groupes=sorted(target))
        if APPLY:
            ldap.add(dn(uid), ["inetOrgPerson"], {
                "cn": f"{row['prenom']} {row['nom']}", "sn": row["nom"], "givenName": row["prenom"],
                "mail": f"{uid}@acmefin.test", "departmentNumber": row["service"], "title": row["poste"]})
            ldap_ok(uid, "création")
            ldap.extend.standard.modify_password(dn(uid), new_password=secrets.token_urlsafe(16))
            for g in target:
                set_membership(uid, g, MODIFY_ADD)
    elif before != target:                                            # MOVER : retirer avant d'ajouter
        log("MOVER", uid, retires=sorted(before - target), ajoutes=sorted(target - before))
        if APPLY:
            for g in before - target:
                set_membership(uid, g, MODIFY_DELETE)
            for g in target - before:
                set_membership(uid, g, MODIFY_ADD)
            kc_sessions(uid)                                          # les nouveaux droits s'appliquent tout de suite
