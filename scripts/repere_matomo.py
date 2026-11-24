"""Repère « même outil » : un site pour les collectivités mesuré avec Matomo, comme aquagir.

collectivite.fr (Annuaire des collectivités) publie ses statistiques Matomo en accès anonyme sur stats.beta.gouv.fr.
Ce n'est PAS un site comparable (c'est un annuaire) : il sert seulement à situer l'écart de mesure Eulerian / Matomo.

Usage :
    python scripts/repere_matomo.py                 # mois précédent
    python scripts/repere_matomo.py --mois 2026-10
    python scripts/repere_matomo.py --mois 2026-10 --reponses-json dossier/   # tests hors ligne
"""
import argparse
import datetime as dt
import json
from pathlib import Path

import pandas as pd
import requests

RACINE = Path(__file__).resolve().parent.parent
RESULTATS = RACINE / "resultats"
MATOMO = "https://stats.beta.gouv.fr/index.php"
SITE = {"id": 118, "nom": "collectivite.fr", "nature": "Annuaire des collectivités (beta.gouv) – repère de mesure, pas un site comparable"}
# Libellés Matomo (Referrers.getReferrerType) ramenés aux libellés de l'observatoire quand c'est possible
SOURCES = {"Entrées directes": "Accès direct", "Direct Entry": "Accès direct",
           "Moteurs de recherche": "Recherche organique", "Search Engines": "Recherche organique",
           "Sites web": "Sites référents", "Websites": "Sites référents",
           "Réseaux sociaux": "Social organique", "Social Networks": "Social organique",
           "Campagnes": "Campagnes", "Campaigns": "Campagnes",
           "Assistants IA": "Assistants IA", "AI Assistants": "Assistants IA"}


def appel(methode, mois, dossier_test=None):
    if dossier_test:
        return json.loads((Path(dossier_test) / f"{methode}.json").read_text(encoding="utf-8"))
    params = {"module": "API", "method": methode, "idSite": SITE["id"], "period": "month",
              "date": f"{mois}-01", "format": "json", "token_auth": "anonymous", "language": "fr"}
    r = requests.get(MATOMO, params=params, timeout=120)
    r.raise_for_status()
    d = r.json()
    if isinstance(d, dict) and d.get("result") == "error":
        raise RuntimeError(f"Matomo {methode} : {d.get('message')}")
    return d


def main():
    p = argparse.ArgumentParser()
    precedent = (dt.date.today().replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    p.add_argument("--mois", default=precedent)
    p.add_argument("--reponses-json")
    a = p.parse_args()

    v = appel("VisitsSummary.get", a.mois, a.reponses_json)
    if not v or not v.get("nb_visits"):
        raise SystemExit(f"ERREUR : aucune visite pour {SITE['nom']} en {a.mois}")
    visites = int(v["nb_visits"])
    res = {
        "mois": a.mois, "site": SITE["nom"], "nature": SITE["nature"], "outil": "Matomo",
        "visites": visites,
        "duree_moy_s": round(v["sum_visit_length"] / visites, 1),
        "pages_par_visite": round(v["nb_actions"] / visites, 2),
        "taux_rebond": round(v["bounce_count"] / visites, 3),
    }

    try:
        appareils = appel("DevicesDetection.getType", a.mois, a.reponses_json)
        est_ordi = lambda r: ("desktop" in r.get("segment", "").lower()
                              or any(m in r.get("label", "").lower() for m in ("ordinateur", "desktop")))
        ordi = sum(r["nb_visits"] for r in appareils if est_ordi(r))
        if not ordi:
            print("ATTENTION : libellés appareils : " + ", ".join(str(r.get("label")) for r in appareils))
        res["part_ordinateur"] = round(ordi / visites, 3)
    except Exception as e:
        print(f"ATTENTION : appareils indisponibles ({e})")
    try:
        sources = {}
        for r in appel("Referrers.getReferrerType", a.mois, a.reponses_json):
            nom = SOURCES.get(r.get("label"), r.get("label"))
            sources[nom] = sources.get(nom, 0) + r["nb_visits"]
        res["sources"] = {k: round(n / visites, 3) for k, n in sorted(sources.items(), key=lambda x: -x[1])}
    except Exception as e:
        print(f"ATTENTION : sources indisponibles ({e})")

    RESULTATS.mkdir(exist_ok=True)
    (RESULTATS / f"repere_matomo_{a.mois}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    s = int(res["duree_moy_s"] + 0.5)
    md = [f"# Repère Matomo – {a.mois}", "",
          f"**{SITE['nom']}** : {SITE['nature']}. Statistiques publiques (stats.beta.gouv.fr, accès anonyme).", "",
          "| Visites | Durée moy. | Pages/visite | Taux de rebond | Part ordinateur |", "|---|---|---|---|---|",
          f"| {visites:,} | {s // 60} min {s % 60:02d} | {res['pages_par_visite']:.2f} | {res['taux_rebond']:.0%} | "
          + (f"{res['part_ordinateur']:.0%}" if "part_ordinateur" in res else "–") + " |"]
    md[-1] = md[-1].replace(",", " ")
    if "sources" in res:
        md += ["", "Sources : " + " ; ".join(f"{k} {v:.0%}" for k, v in res["sources"].items()) + "."]
    md += ["", "À lire comme un repère de mesure (même outil qu'aquagir, même public), pas comme un site comparable : "
               "un annuaire génère des visites courtes de recherche d'information."]
    (RESULTATS / f"repere_matomo_{a.mois}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    hist = RESULTATS / "repere_matomo_historique.csv"
    nouv = pd.DataFrame([{k: v for k, v in res.items() if k not in ("sources", "nature")}])
    if hist.exists():
        anc = pd.read_csv(hist)
        nouv = pd.concat([anc[anc["mois"] != a.mois], nouv])
    nouv.sort_values("mois").to_csv(hist, index=False)
    print(f"Écrit : resultats/repere_matomo_{a.mois}.md, .json et repere_matomo_historique.csv")


if __name__ == "__main__":
    main()
