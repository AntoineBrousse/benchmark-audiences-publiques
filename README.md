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

`scripts/lighthouse.py` lance chaque mois Lighthouse via l'API PageSpeed Insights de Google (preset desktop ; certains sites bloquent les serveurs GitHub, la mesure est donc faite depuis les serveurs de Google) sur la page d'accueil d'aquagir et des sites comparables, 3 passages par page, médiane retenue. Même mesure pour tous les sites, donc comparaison directe.
Sorties : `resultats/lighthouse_AAAA-MM.md`, `.json` et `lighthouse_historique.csv`. Pages mesurées : `config.json` → `lighthouse`. Clé API facultative : secret `PSI_API_KEY`.

## Contenu des sites (sitemaps) et expérience réelle (CrUX)

- `scripts/sitemaps.py` lit le sitemap public d'aquagir (les sites ADEME refusent l'accès depuis GitHub) : nombre de pages, pages modifiées sur 30 et 90 jours, principales rubriques. Sorties : `resultats/sitemaps_AAAA-MM.md`, `.json`, `sitemaps_historique.csv`.
- Le rapport Lighthouse inclut les données terrain de Chrome (CrUX, 28 jours) quand Google les publie (trafic suffisant).

## Repère Matomo

`scripts/repere_matomo.py` récupère les statistiques publiques de collectivite.fr (Annuaire des collectivités) sur le Matomo de beta.gouv (accès anonyme). Ce n'est pas un site comparable (annuaire), mais un repère mesuré avec le même outil qu'aquagir, pour situer l'écart de mesure Eulerian / Matomo.

## Analyse mensuelle (Claude)

Une tâche planifiée Claude lit les résultats le 3 de chaque mois et écrit une analyse dans `analyses/analyse_AAAA-MM.md`, en suivant les consignes de `prompts/analyse_mensuelle.md` (modifiables sans toucher à la tâche).

## Limites

Audience : mesure Eulerian (nos sites : Matomo), pas de taux de rebond publié, majorité de sites ADEME, petits volumes instables.
Lighthouse : page d'accueil seulement, score variable, accessibilité partielle par rapport au RGAA.
