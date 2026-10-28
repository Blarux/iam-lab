#!/usr/bin/env python3
"""Génère l'annuaire AcmeFin (LDIF) et le fichier RH (CSV), cohérents entre eux."""
import base64, csv, hashlib, os, random, secrets, unicodedata

random.seed(42)                      # mêmes noms à chaque exécution
BASE = "dc=acmefin,dc=test"
LAB_PASSWORD = os.environ["LAB_USER_PASSWORD"]

# Personnages fixes des scénarios : (prénom, nom, service, poste, groupes)
PERSONAS = [
    ("Alice", "Martin", "Finance", "Comptable", ["grp-finance-saisie"]),
    ("Bruno", "Leroy", "Finance", "Contrôleur financier", ["grp-finance-validation"]),
    ("Chloé", "Dubois", "Développement", "Développeuse", ["grp-dev"]),
    ("David", "Moreau", "IT", "Administrateur systèmes", ["grp-it-admin"]),
    ("Emma", "Petit", "RH", "Chargée RH", ["grp-rh"]),
]
# Salariés générés en plus : (service, poste, groupes, nombre)
POSTES = [
    ("RH", "Chargé RH", ["grp-rh"], 4),
    ("Finance", "Comptable", ["grp-finance-saisie"], 9),
    ("Finance", "Contrôleur financier", ["grp-finance-validation"], 4),
    ("Développement", "Développeur", ["grp-dev"], 16),
    ("Développement", "Lead développeur", ["grp-dev", "grp-dev-lead"], 3),
    ("IT", "Technicien support", ["grp-it-support"], 7),
    ("IT", "Administrateur systèmes", ["grp-it-admin"], 2),
]
PRENOMS = ["Léa", "Hugo", "Manon", "Lucas", "Camille", "Nathan", "Sarah", "Théo", "Inès", "Louis",
           "Julie", "Paul", "Clara", "Maxime", "Laura", "Antoine", "Pauline", "Julien", "Marie", "Yanis"]
NOMS = ["Bernard", "Thomas", "Robert", "Richard", "Durand", "Lefebvre", "Michel", "Garcia", "Roux", "Fournier",
        "Girard", "Bonnet", "Lambert", "Fontaine", "Rousseau", "Vincent", "Muller", "Faure", "Andre", "Mercier"]

def ascii_id(text):
    """Chloé -> chloe : les identifiants restent en ASCII."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()

def ssha(password):
    """Empreinte salée {SSHA}, le format natif d'OpenLDAP : jamais de mot de passe en clair."""
    salt = os.urandom(8)
    digest = hashlib.sha1(password.encode() + salt).digest()
    return "{SSHA}" + base64.b64encode(digest + salt).decode()

def ldif(attr, value):
    """En LDIF, une valeur avec des accents doit être encodée en base64 (attr:: valeur)."""
    if value.isascii():
        return f"{attr}: {value}"
    return f"{attr}:: {base64.b64encode(value.encode()).decode()}"

people, used = [], set()

def add(prenom, nom, service, poste, groupes, password):
    uid, n = f"{ascii_id(prenom)}.{ascii_id(nom)}", 2
    while uid in used:                                   # homonymes : jean.dupont2
        uid, n = f"{ascii_id(prenom)}.{ascii_id(nom)}{n}", n + 1
    used.add(uid)
    people.append({"uid": uid, "prenom": prenom, "nom": nom, "service": service, "poste": poste,
                   "groupes": groupes, "password": password, "num": 1001 + len(people)})

for p in PERSONAS:
    add(*p, LAB_PASSWORD)
for service, poste, groupes, nombre in POSTES:
    for _ in range(nombre):                              # mot de passe aléatoire, jamais utilisé
        add(random.choice(PRENOMS), random.choice(NOMS), service, poste, groupes, secrets.token_urlsafe(16))

out = []
for ou in ["people", "groups", "services", "departs"]:
    out += [f"dn: ou={ou},{BASE}", "objectClass: organizationalUnit", f"ou: {ou}", ""]
for p in people:
    out += [f"dn: uid={p['uid']},ou=people,{BASE}", "objectClass: inetOrgPerson", f"uid: {p['uid']}",
            ldif("cn", f"{p['prenom']} {p['nom']}"), ldif("sn", p["nom"]), ldif("givenName", p["prenom"]),
            f"mail: {p['uid']}@acmefin.test", f"employeeNumber: {p['num']}",
            ldif("departmentNumber", p["service"]), ldif("title", p["poste"]),
            f"userPassword: {ssha(p['password'])}", ""]
groups = sorted({g for p in people for g in p["groupes"]})
for g in groups:
    out += [f"dn: cn={g},ou=groups,{BASE}", "objectClass: groupOfNames", f"cn: {g}"]
    out += [f"member: uid={p['uid']},ou=people,{BASE}" for p in people if g in p["groupes"]]
    out.append("")

os.makedirs("ldap/bootstrap", exist_ok=True)
with open("ldap/bootstrap/50-acmefin.ldif", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
with open("governance/hr/rh.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["uid", "prenom", "nom", "service", "poste", "groupes", "statut"])
    for p in people:
        w.writerow([p["uid"], p["prenom"], p["nom"], p["service"], p["poste"], ";".join(p["groupes"]), "actif"])
print(f"{len(people)} personnes, {len(groups)} groupes")
