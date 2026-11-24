"""Qualité technique mensuelle (Lighthouse) d'aquagir et des sites comparables.

Lance Lighthouse plusieurs fois par page et garde la médiane (les scores varient d'un passage à l'autre).

Usage :
    python scripts/lighthouse.py                 # mois courant
    python scripts/lighthouse.py --mois 2026-11
    python scripts/lighthouse.py --rapports-json dossier/   # recalcul à partir de rapports Lighthouse déjà produits (tests)
"""
import argparse
import datetime as dt
import json
import statistics
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

RACINE = Path(__file__).resolve().parent.parent
RESULTATS = RACINE / "resultats"
CATEGORIES = {"performance": "Performance", "accessibility": "Accessibilité",
              "best-practices": "Bonnes pratiques", "seo": "SEO"}
# Catégories pour lesquelles on liste les vérifications ratées (la performance est une mesure continue)
EXPLIQUEES = {"seo": "SEO", "accessibility": "Accessibilité", "best-practices": "Bonnes pratiques"}
METRIQUES = {"largest-contentful-paint": "LCP (s)", "total-blocking-time": "TBT (ms)",
             "cumulative-layout-shift": "CLS"}


def extraire(rapport):
    """Scores (0-100) et métriques clés d'un rapport Lighthouse JSON."""
    if rapport.get("runtimeError"):
        raise ValueError(rapport["runtimeError"].get("message", "erreur Lighthouse"))
    res = {}
    for cle, nom in CATEGORIES.items():
        score = rapport["categories"].get(cle, {}).get("score")
        res[nom] = None if score is None else round(score * 100)
    audits = rapport["audits"]
    lcp = audits.get("largest-contentful-paint", {}).get("numericValue")
    tbt = audits.get("total-blocking-time", {}).get("numericValue")
    cls = audits.get("cumulative-layout-shift", {}).get("numericValue")
    res["LCP (s)"] = None if lcp is None else round(lcp / 1000, 2)
    res["TBT (ms)"] = None if tbt is None else round(tbt)
    res["CLS"] = None if cls is None else round(cls, 3)
    return res


def verifications_ratees(rapport):
    """{catégorie: [titres des vérifications ratées]} (audits pondérés, score < 1)."""
    audits = rapport["audits"]
    out = {}
    for cle, nom in EXPLIQUEES.items():
        rates = []
        for ref in rapport["categories"].get(cle, {}).get("auditRefs", []):
            a = audits.get(ref["id"], {})
            if ref.get("weight", 0) > 0 and a.get("score") is not None and a["score"] < 1:
                rates.append(a.get("title", ref["id"]))
        out[nom] = rates
    return out


def ratees_majoritaires(listes):
    """Garde les vérifications ratées dans au moins la moitié des passages."""
    out = {}
    for nom in EXPLIQUEES.values():
        compte = {}
        for l in listes:
            for t in l.get(nom, []):
                compte[t] = compte.get(t, 0) + 1
        out[nom] = sorted(t for t, n in compte.items() if n * 2 >= len(listes))
    return out


PSI = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def lancer(url, preset, dest):
    """Lighthouse via PageSpeed Insights : Google lance la mesure depuis ses serveurs
    (les sites qui bloquent les serveurs d'hébergement comme GitHub restent mesurables)."""
    params = [("url", url), ("strategy", preset), ("locale", "fr")] + [("category", c.upper().replace("-", "_")) for c in CATEGORIES]
    if os.environ.get("PSI_API_KEY"):
        params.append(("key", os.environ["PSI_API_KEY"]))
    for essai in range(3):
        r = requests.get(PSI, params=params, timeout=180)
        if r.status_code == 429 and "per day" in r.text:
            raise RuntimeError("quota journalier PageSpeed Insights épuisé : ajouter le secret PSI_API_KEY")
        if r.status_code == 429 and essai < 2:  # limite par minute : on patiente
            time.sleep(30)
            continue
        if not r.ok:
            raise RuntimeError(f"PageSpeed Insights HTTP {r.status_code} : {r.text[:200]}")
        break
    rapport = r.json()["lighthouseResult"]
    Path(dest).write_text(json.dumps(rapport), encoding="utf-8")
    return rapport


def mediane(mesures):
    cles = mesures[0].keys()
    out = {}
    for k in cles:
        vals = [m[k] for m in mesures if m.get(k) is not None]
        out[k] = round(statistics.median(vals), 3) if vals else None
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mois", default=dt.date.today().strftime("%Y-%m"))
    p.add_argument("--rapports-json", help="dossier de rapports <site>__<n>.json (tests)")
    a = p.parse_args()
    cfg = json.loads((RACINE / "config.json").read_text(encoding="utf-8"))["lighthouse"]

    lignes, echecs = [], []
    tmp = RACINE / "donnees" / "lighthouse"
    tmp.mkdir(parents=True, exist_ok=True)
    for site, urls in cfg["sites"].items():
        mesures, ratees = [], []
        for url in urls:
            for i in range(cfg["passages"]):
                try:
                    if a.rapports_json:
                        f = Path(a.rapports_json) / f"{site}__{i}.json"
                        rapport = json.loads(f.read_text(encoding="utf-8"))
                    else:
                        rapport = lancer(url, cfg["preset"], tmp / f"{site}__{i}.json")
                    mesures.append(extraire(rapport))
                    ratees.append(verifications_ratees(rapport))
                except Exception as e:  # un site injoignable ne bloque pas les autres
                    print(f"ATTENTION : {url} passage {i + 1} : {e}", file=sys.stderr)
        if mesures:
            lignes.append({"site": site, "passages": len(mesures), **mediane(mesures),
                           "verifications_ratees": ratees_majoritaires(ratees)})
        else:
            echecs.append(site)

    if not lignes:
        print("ERREUR : aucune mesure Lighthouse réussie", file=sys.stderr)
        sys.exit(1)

    df = pd.DataFrame([{k: v for k, v in l.items() if k != "verifications_ratees"} for l in lignes])
    ref = cfg["site_reference"]
    pairs = df[df["site"] != ref]
    med = {k: round(float(pairs[k].median()), 3) for k in list(CATEGORIES.values()) + list(METRIQUES.values())
           if k in pairs and pairs[k].notna().any()}

    RESULTATS.mkdir(exist_ok=True)
    rapport = {"mois": a.mois, "preset": cfg["preset"], "sites": lignes, "mediane_pairs": med, "echecs": echecs}
    (RESULTATS / f"lighthouse_{a.mois}.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=2),
                                                        encoding="utf-8")

    cols = list(CATEGORIES.values()) + list(METRIQUES.values())
    fmt = lambda v: "–" if v is None or pd.isna(v) else (f"{v:g}")
    md = [f"# Qualité technique (Lighthouse) – {a.mois}", "",
          f"Mesure Lighthouse via PageSpeed Insights ({cfg['preset']}), médiane de {cfg['passages']} passages par page. "
          "Scores de 0 à 100 (plus c'est haut, mieux c'est) ; LCP, TBT et CLS : plus c'est bas, mieux c'est.", "",
          "| Site | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for l in lignes:
        nom = f"**{l['site']}**" if l["site"] == ref else l["site"]
        md.append(f"| {nom} | " + " | ".join(fmt(l.get(c)) for c in cols) + " |")
    md.append("| *Médiane des sites comparables* | " + " | ".join(fmt(med.get(c)) for c in cols) + " |")
    md += ["", "Repères Lighthouse : 90-100 = bon, 50-89 = à améliorer, 0-49 = mauvais. "
               "LCP bon sous 2,5 s ; CLS bon sous 0,1.", ""]
    md += ["## Vérifications ratées", "",
           "Ce qui fait perdre des points à chaque site (ratées dans au moins la moitié des passages).", ""]
    for l in lignes:
        md.append(f"### {l['site']}")
        for nom, rates in l["verifications_ratees"].items():
            md.append(f"- **{nom}** : " + ("; ".join(rates) if rates else "aucune"))
        md.append("")
    if echecs:
        md.append("⚠️ Mesure impossible ce mois : " + ", ".join(echecs) + ".")
    md += ["", "Limites : page d'accueil uniquement, score variable d'un passage à l'autre, "
               "l'accessibilité Lighthouse ne couvre qu'une partie du RGAA."]
    (RESULTATS / f"lighthouse_{a.mois}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    hist = RESULTATS / "lighthouse_historique.csv"
    nouv = df.assign(mois=a.mois)
    if hist.exists():
        anc = pd.read_csv(hist)
        nouv = pd.concat([anc[anc["mois"] != a.mois], nouv])
    nouv.sort_values(["mois", "site"]).to_csv(hist, index=False)
    print(f"Écrit : resultats/lighthouse_{a.mois}.md, .json et lighthouse_historique.csv")


if __name__ == "__main__":
    main()
