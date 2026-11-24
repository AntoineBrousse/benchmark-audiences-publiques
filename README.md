# Benchmark des audiences de sites publics

Situe les audiences d'aquagir (Banque des Territoires) face à des sites publics comparables, chaque mois.

## Méthode

1. **Sélection des sites comparables**, uniquement sur leurs caractéristiques, jamais sur leurs audiences :
   - public : collectivités ou professionnels du territoire ;
   - structure : plateforme de ressources et d'accompagnement.
2. **Comparaison** : durée moyenne, pages par visite et part sur ordinateur de chaque site, puis médiane du groupe.

Les sites retenus sont dans `config.json`.

## Source

Jeu de données data.gouv « Observatoire de l'écosystème numérique de l'État – Sites internet » (SIG, mesure Eulerian, publication mensuelle).
Codes appareil déduits par cohérence avec les totaux de l'observatoire : 6 = ordinateur, 5 = mobile, 1 = tablette, 2 = TV.

## Fonctionnement

- GitHub Actions lance `scripts/benchmark.py` le 2 de chaque mois, ou à la main (onglet Actions → Benchmark mensuel → Run workflow).
- Le script télécharge les CSV du mois via l'API data.gouv, vérifie leur format et écrit dans `resultats/` :
  - `aquagir_AAAA-MM.md` : le rapport lisible ;
  - `aquagir_AAAA-MM.json` : les chiffres ;
  - `aquagir_historique.csv` : l'historique mois par mois.
- En cas de format modifié ou de mois non publié, le script s'arrête avec une erreur explicite.

En local : `python scripts/benchmark.py --mois 2026-10`.

## Qualité technique (Lighthouse)

`scripts/lighthouse.py` lance chaque mois Lighthouse (outil public de Google, preset desktop) sur la page d'accueil d'aquagir et des sites comparables, 3 passages par page, médiane retenue. Même mesure pour tous les sites, donc comparaison directe.
Sorties : `resultats/lighthouse_AAAA-MM.md`, `.json` et `lighthouse_historique.csv`. Pages mesurées : `config.json` → `lighthouse`.

## Limites

Audience : mesure Eulerian (nos sites : Matomo), pas de taux de rebond publié, majorité de sites ADEME, petits volumes instables.
Lighthouse : page d'accueil seulement, score variable, accessibilité partielle par rapport au RGAA.
