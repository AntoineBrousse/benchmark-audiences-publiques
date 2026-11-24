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
import subprocess
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
RESULTATS = RACINE / "resultats"
CATEGORIES = {"performance": "Performance", "accessibility": "Accessibilité",
              "best-practices": "Bonnes pratiques", "seo": "SEO"}
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


def lancer(url, preset, dest):
    cmd = ["npx", "--yes", "lighthouse@12", url, "--quiet", "--output=json", f"--output-path={dest}",
           "--chrome-flags=--headless=new --no-sandbox", "--only-categories=" + ",".join(CATEGORIES)]
    if preset == "desktop":
        cmd.append("--preset=desktop")
    subprocess.run(cmd, check=True, timeout=240)
    return json.loads(Path(dest).read_text(encoding="utf-8"))


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
        mesures = []
        for url in urls:
            for i in range(cfg["passages"]):
                try:
                    if a.rapports_json:
                        f = Path(a.rapports_json) / f"{site}__{i}.json"
                        rapport = json.loads(f.read_text(encoding="utf-8"))
                    else:
                        rapport = lancer(url, cfg["preset"], tmp / f"{site}__{i}.json")
                    mesures.append(extraire(rapport))
                except Exception as e:  # un site injoignable ne bloque pas les autres
                    print(f"ATTENTION : {url} passage {i + 1} : {e}", file=sys.stderr)
        if mesures:
            lignes.append({"site": site, "passages": len(mesures), **mediane(mesures)})
        else:
            echecs.append(site)

    if not lignes:
        print("ERREUR : aucune mesure Lighthouse réussie", file=sys.stderr)
        sys.exit(1)

    df = pd.DataFrame(lignes)
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
          f"Mesure Lighthouse ({cfg['preset']}), médiane de {cfg['passages']} passages par page. "
          "Scores de 0 à 100 (plus c'est haut, mieux c'est) ; LCP, TBT et CLS : plus c'est bas, mieux c'est.", "",
          "| Site | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for l in lignes:
        nom = f"**{l['site']}**" if l["site"] == ref else l["site"]
        md.append(f"| {nom} | " + " | ".join(fmt(l.get(c)) for c in cols) + " |")
    md.append("| *Médiane des sites comparables* | " + " | ".join(fmt(med.get(c)) for c in cols) + " |")
    md += ["", "Repères Lighthouse : 90-100 = bon, 50-89 = à améliorer, 0-49 = mauvais. "
               "LCP bon sous 2,5 s ; CLS bon sous 0,1.", ""]
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
