"""Benchmark mensuel des audiences de sites publics comparables.

Source : jeu de données data.gouv « Observatoire de l'écosystème numérique de l'État - Sites internet »
(mesure Eulerian, publication mensuelle par le SIG).

Usage :
    python scripts/benchmark.py                 # dernier mois publié
    python scripts/benchmark.py --mois 2026-10  # mois précis
    python scripts/benchmark.py --browser-csv f1.csv --liste-csv f2.csv --mois 2026-10   # fichiers locaux
"""
import argparse
import calendar
import json
import re
import sys
from pathlib import Path

import pandas as pd
import requests

RACINE = Path(__file__).resolve().parent.parent
RESULTATS = RACINE / "resultats"
API = "https://www.data.gouv.fr/api/1/datasets/{}/"

MOIS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
        "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12}
COLONNES_BROWSER = {"duree_visite", "nb_visite", "nb_page_vue", "date_visite", "id_site", "id_device"}
COLONNES_LISTE = {"id_site", "label_site"}


def erreur(msg):
    print(f"ERREUR : {msg}", file=sys.stderr)
    sys.exit(1)


def lister_ressources(dataset):
    """Renvoie {(fichier, 'AAAA-MM'): url} pour les CSV mensuels du jeu de données."""
    r = requests.get(API.format(dataset), timeout=60)
    r.raise_for_status()
    trouves = {}
    for res in r.json().get("resources", []):
        url = res.get("url", "")
        m = re.search(r"/(audience-[a-z-]+?)-([a-z]+)-(\d{4})\.csv$", url)
        if m and m.group(2) in MOIS:
            trouves[(m.group(1), f"{m.group(3)}-{MOIS[m.group(2)]:02d}")] = url
    if not trouves:
        erreur("aucun fichier mensuel trouvé via l'API data.gouv (format de publication modifié ?)")
    return trouves


def telecharger(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, timeout=300, stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for bloc in r.iter_content(1 << 20):
                f.write(bloc)
    return dest


def verifier_colonnes(df, attendues, nom):
    manquantes = attendues - set(df.columns)
    if manquantes:
        erreur(f"{nom} : colonnes manquantes {sorted(manquantes)} (format modifié par le SIG ?)")


def calculer(browser, liste, mois, cfg):
    verifier_colonnes(browser, COLONNES_BROWSER, "fichier visites")
    verifier_colonnes(liste, COLONNES_LISTE, "fichier liste des sites")

    annee, m = map(int, mois.split("-"))
    jours = browser["date_visite"].nunique()
    jours_mois = calendar.monthrange(annee, m)[1]

    g = browser.groupby("id_site").agg(visites=("nb_visite", "sum"),
                                       duree=("duree_visite", "sum"),
                                       pages=("nb_page_vue", "sum"))
    app = browser.pivot_table(index="id_site", columns="id_device", values="nb_visite",
                              aggfunc="sum", fill_value=0)
    app.columns = [cfg["codes_appareil"].get(str(c), f"appareil_{c}") for c in app.columns]
    g = g.join(app)

    # Contrôle de cohérence du décodage des appareils : l'ordinateur doit rester majoritaire au global
    total = g[[c for c in ("ordinateur", "mobile") if c in g]].sum()
    if "ordinateur" in total and "mobile" in total and total["ordinateur"] < total["mobile"]:
        print("ATTENTION : plus de mobile que d'ordinateur au global, vérifier les codes appareil.", file=sys.stderr)

    rapports = {}
    for nom, bench in cfg["benchmarks"].items():
        lignes, absents = [], []
        for id_site, info in bench["pairs"].items():
            id_site = int(id_site)
            if id_site not in g.index or g.loc[id_site, "visites"] == 0:
                absents.append(info["site"])
                continue
            s = g.loc[id_site]
            lignes.append({
                "id_site": id_site,
                "site": info["site"],
                "nature": info["nature"],
                "visites": int(s["visites"]),
                "duree_moy_s": round(s["duree"] / s["visites"], 1),
                "pages_par_visite": round(s["pages"] / s["visites"], 2),
                "part_ordinateur": round(s.get("ordinateur", 0) / s["visites"], 3),
            })
        if not lignes:
            erreur(f"benchmark {nom} : aucun site comparable n'a de données pour {mois}")
        df = pd.DataFrame(lignes)
        rapports[nom] = {
            "mois": mois,
            "jours_couverts": int(jours),
            "jours_du_mois": jours_mois,
            "sites": lignes,
            "sites_sans_donnees": absents,
            "mediane": {
                "duree_moy_s": round(float(df["duree_moy_s"].median()), 1),
                "pages_par_visite": round(float(df["pages_par_visite"].median()), 2),
                "part_ordinateur": round(float(df["part_ordinateur"].median()), 3),
            },
            "reference_etat": {
                "nb_sites": int((g["visites"] > 0).sum()),
                "duree_moy_mediane_s": round(float((g["duree"] / g["visites"]).median()), 1),
            },
        }
    return rapports


def fmt_duree(s):
    s = int(s + 0.5)
    return f"{s // 60} min {s % 60:02d}"


def ecrire(rapports, cfg):
    RESULTATS.mkdir(exist_ok=True)
    for nom, r in rapports.items():
        mois = r["mois"]
        (RESULTATS / f"{nom}_{mois}.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")

        md = [f"# Benchmark {nom} – {mois}", "",
              "Source : observatoire de l'écosystème numérique de l'État (SIG, mesure Eulerian), data.gouv.fr.", "",
              "Critères de sélection des sites comparables : " + " ; ".join(cfg["benchmarks"][nom]["criteres"]) + ".", "",
              "| Site | Nature | Visites | Durée moy. | Pages/visite | Part ordinateur |",
              "|---|---|---|---|---|---|"]
        for s in r["sites"]:
            visites = f"{s['visites']:,}".replace(",", " ")
            md.append(f"| {s['site']} | {s['nature']} | {visites} | {fmt_duree(s['duree_moy_s'])} | "
                      f"{s['pages_par_visite']:.2f} | {s['part_ordinateur']:.0%} |")
        med = r["mediane"]
        md += [f"| **Médiane** | | | **{fmt_duree(med['duree_moy_s'])}** | **{med['pages_par_visite']:.2f}** | "
               f"**{med['part_ordinateur']:.0%}** |", "",
               f"Repère : durée moyenne médiane de l'ensemble des {r['reference_etat']['nb_sites']} sites de l'État : "
               f"{fmt_duree(r['reference_etat']['duree_moy_mediane_s'])}.", ""]
        if r["jours_couverts"] < r["jours_du_mois"]:
            md.append(f"⚠️ Données sur {r['jours_couverts']} jours sur {r['jours_du_mois']}.")
        if r["sites_sans_donnees"]:
            md.append("⚠️ Sans données ce mois : " + ", ".join(r["sites_sans_donnees"]) + ".")
        md += ["", "Limites : mesure Eulerian (nos sites sont mesurés avec Matomo), pas de taux de rebond publié, "
               "majorité de sites ADEME, petits volumes instables."]
        (RESULTATS / f"{nom}_{mois}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

        # Historique : une ligne par site et par mois (remplace le mois s'il existe déjà)
        hist = RESULTATS / f"{nom}_historique.csv"
        nouv = pd.DataFrame(r["sites"]).assign(mois=mois)
        nouv = pd.concat([nouv, pd.DataFrame([{"mois": mois, "site": "MEDIANE", **med}])])
        if hist.exists():
            anc = pd.read_csv(hist)
            nouv = pd.concat([anc[anc["mois"] != mois], nouv])
        nouv["id_site"] = nouv["id_site"].astype("Int64")
        nouv.sort_values(["mois", "site"]).to_csv(hist, index=False)
        print(f"Écrit : resultats/{nom}_{mois}.md, .json et {nom}_historique.csv")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mois", help="AAAA-MM (défaut : dernier mois publié)")
    p.add_argument("--browser-csv")
    p.add_argument("--liste-csv")
    a = p.parse_args()
    cfg = json.loads((RACINE / "config.json").read_text(encoding="utf-8"))

    if a.browser_csv and a.liste_csv:
        if not a.mois:
            erreur("--mois est obligatoire avec des fichiers locaux")
        mois, f_browser, f_liste = a.mois, Path(a.browser_csv), Path(a.liste_csv)
    else:
        res = lister_ressources(cfg["dataset"])
        dispo = sorted(m for (f, m) in res if f == "audience-visites-browser-sites")
        if not dispo:
            erreur("aucun fichier audience-visites-browser-sites publié")
        mois = a.mois or dispo[-1]
        for fichier in ("audience-visites-browser-sites", "audience-liste-sites"):
            if (fichier, mois) not in res:
                erreur(f"{fichier} non publié pour {mois} (mois disponibles : {', '.join(dispo[-6:])})")
        tmp = RACINE / "donnees"
        f_browser = telecharger(res[("audience-visites-browser-sites", mois)], tmp / f"browser_{mois}.csv")
        f_liste = telecharger(res[("audience-liste-sites", mois)], tmp / f"liste_{mois}.csv")

    rapports = calculer(pd.read_csv(f_browser), pd.read_csv(f_liste), mois, cfg)
    ecrire(rapports, cfg)


if __name__ == "__main__":
    main()
