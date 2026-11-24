"""Veille sur le contenu d'aquagir : nombre de pages et rythme de publication.

Les sites comparables (ADEME) refusent l'accès depuis les serveurs GitHub : la veille porte sur aquagir seul.

Lit le sitemap public de chaque site (le fichier que les sites publient pour les moteurs de recherche) :
nombre de pages, pages modifiées dans les 30 et 90 derniers jours, répartition par rubrique.

Usage :
    python scripts/sitemaps.py                  # mois courant
    python scripts/sitemaps.py --sitemaps-dir d/ # tests hors ligne : d/<site>.xml (ou index + fichiers)
"""
import argparse
import datetime as dt
import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

RACINE = Path(__file__).resolve().parent.parent
RESULTATS = RACINE / "resultats"
UA = "benchmark-audiences-publiques/1.0 (+https://github.com/AntoineBrousse/benchmark-audiences-publiques)"
CANDIDATS = ["/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml"]
MAX_SITEMAPS = 200          # garde-fou : nombre de sous-sitemaps lus par site
NS = re.compile(r"^\{.*\}")


class Lecteur:
    def __init__(self, dossier_test=None):
        self.test = Path(dossier_test) if dossier_test else None
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA

    def get(self, url):
        if self.test:
            f = self.test / (urlparse(url).netloc + urlparse(url).path.replace("/", "_"))
            return f.read_bytes() if f.exists() else None
        try:
            r = self.s.get(url, timeout=60)
        except requests.RequestException as e:
            print(f"ATTENTION : {url} : {e}", file=sys.stderr)
            return None
        if r.status_code != 200:
            print(f"ATTENTION : {url} : HTTP {r.status_code}", file=sys.stderr)
            return None
        data = r.content
        return gzip.decompress(data) if url.endswith(".gz") or data[:2] == b"\x1f\x8b" else data


def sitemaps_declares(lecteur, base):
    robots = lecteur.get(base + "/robots.txt")
    if robots:
        trouves = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots.decode("utf-8", "replace"))
        if trouves:
            return trouves
    return [base + c for c in CANDIDATS]


def lire(lecteur, base):
    """Renvoie la liste des (url, lastmod) du site, ou None si aucun sitemap lisible."""
    a_lire, vus, pages, lu = list(sitemaps_declares(lecteur, base)), set(), {}, False
    while a_lire and len(vus) < MAX_SITEMAPS:
        url = a_lire.pop(0)
        if url in vus:
            continue
        vus.add(url)
        data = lecteur.get(url)
        if not data:
            continue
        try:
            racine = ET.fromstring(data)
        except ET.ParseError:
            continue
        lu = True
        tag = NS.sub("", racine.tag)
        for el in racine:
            loc = lastmod = None
            for f in el:
                t = NS.sub("", f.tag)
                if t == "loc":
                    loc = (f.text or "").strip()
                elif t == "lastmod":
                    lastmod = (f.text or "").strip()
            if not loc:
                continue
            if tag == "sitemapindex":
                a_lire.append(loc)
            else:
                pages[loc] = lastmod
    if not lu:
        return None
    return list(pages.items())


def date(lastmod):
    try:
        return dt.date.fromisoformat(lastmod[:10])
    except (TypeError, ValueError):
        return None


def resumer(pages, aujourd_hui):
    dates = [date(m) for _, m in pages]
    avec_date = [d for d in dates if d]
    rubriques = Counter((urlparse(u).path.strip("/").split("/") or [""])[0] or "(accueil)" for u, _ in pages)
    return {
        "pages": len(pages),
        "part_avec_date": round(len(avec_date) / len(pages), 2) if pages else 0,
        "modifiees_30j": sum(1 for d in avec_date if (aujourd_hui - d).days <= 30),
        "modifiees_90j": sum(1 for d in avec_date if (aujourd_hui - d).days <= 90),
        "derniere_modif": max(avec_date).isoformat() if avec_date else None,
        "rubriques": dict(rubriques.most_common(5)),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mois", default=dt.date.today().strftime("%Y-%m"))
    p.add_argument("--sitemaps-dir")
    p.add_argument("--aujourdhui", help="date de référence AAAA-MM-JJ (tests)")
    a = p.parse_args()
    cfg = json.loads((RACINE / "config.json").read_text(encoding="utf-8"))["lighthouse"]
    jour = dt.date.fromisoformat(a.aujourdhui) if a.aujourdhui else dt.date.today()
    lecteur = Lecteur(a.sitemaps_dir)

    lignes, echecs = [], []
    sites = {cfg["site_reference"]: cfg["sites"][cfg["site_reference"]]}
    for site, urls in sites.items():
        u = urlparse(urls[0])
        pages = lire(lecteur, f"{u.scheme}://{u.netloc}")
        if not pages:
            echecs.append(site)
            continue
        lignes.append({"site": site, **resumer(pages, jour)})

    RESULTATS.mkdir(exist_ok=True)
    rapport = {"mois": a.mois, "date_mesure": jour.isoformat(), "sites": lignes, "sans_sitemap_lisible": echecs}
    (RESULTATS / f"sitemaps_{a.mois}.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")

    ref = cfg["site_reference"]
    md = [f"# Contenu d'aquagir (sitemap) – {a.mois}", "",
          f"Lu le {jour.isoformat()} dans le sitemap public de chaque site.", "",
          "| Site | Pages | Modifiées < 30 j | Modifiées < 90 j | Dernière modif. | Pages datées | Principales rubriques |",
          "|---|---|---|---|---|---|---|"]
    for l in lignes:
        nom = f"**{l['site']}**" if l["site"] == ref else l["site"]
        rub = ", ".join(f"{k} ({v})" for k, v in l["rubriques"].items())
        md.append(f"| {nom} | {l['pages']} | {l['modifiees_30j']} | {l['modifiees_90j']} | "
                  f"{l['derniere_modif'] or '–'} | {l['part_avec_date']:.0%} | {rub} |")
    if echecs:
        md += ["", "⚠️ Aucun sitemap lisible (absent ou accès refusé) : " + ", ".join(echecs) + "."]
    md += ["", "Limites : un sitemap peut être incomplet ; « modifiée » dépend de la date déclarée par le site "
               "(certains la mettent à jour à chaque republication technique). Si peu de pages sont datées, "
               "le rythme de publication n'est pas interprétable."]
    (RESULTATS / f"sitemaps_{a.mois}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    hist = RESULTATS / "sitemaps_historique.csv"
    nouv = pd.DataFrame([{k: v for k, v in l.items() if k != "rubriques"} for l in lignes]).assign(mois=a.mois)
    if hist.exists():
        anc = pd.read_csv(hist)
        nouv = pd.concat([anc[anc["mois"] != a.mois], nouv])
    if not nouv.empty:
        nouv.sort_values(["mois", "site"]).to_csv(hist, index=False)
    print(f"Écrit : resultats/sitemaps_{a.mois}.md, .json ({len(lignes)} sites lus, {len(echecs)} échecs)")


if __name__ == "__main__":
    main()
