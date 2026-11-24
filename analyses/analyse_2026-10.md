# Analyse mensuelle aquagir – audience 2026-10, qualité technique 2026-11

Données : `resultats/aquagir_2026-10` (audience Eulerian des 4 sites comparables, 29 jours sur 31) et `resultats/lighthouse_2026-11` (Lighthouse desktop, page d'accueil, médiane de 3 passages).

## 1. En bref

Techniquement, la page d'accueil d'aquagir est au-dessus de la médiane des comparables sur les quatre scores Lighthouse (performance 90, accessibilité 94, bonnes pratiques 100, SEO 100) ; seuls deux défauts d'accessibilité restent à corriger. Côté audience, les comparables reçoivent environ 7 visites sur 10 depuis un moteur de recherche (médiane 71 %) et un visiteur y reste en moyenne 1 min 25 pour moins de 2 pages : le référencement est la porte d'entrée principale de ce public. Le site le plus proche d'aquagir (territoires-climat) fait mieux sur l'engagement (2 min 08, 2,41 pages) : c'est le repère à viser.

## 2. Qualité technique d'aquagir face aux comparables

**Constat.** Aquagir est devant la médiane des 4 comparables partout :

- Performance 90 contre 79,5 : la page principale s'affiche en 0,86 s (LCP), plus vite que la médiane (0,98 s). Le temps de blocage (TBT, période où la page ne répond pas aux clics) est de 178 ms, au niveau de la médiane (179 ms) mais nettement au-dessus d'economie-circulaire et experimentationsurbaines (0 ms). C'est la seule marge de progrès en performance.
- SEO 100 et bonnes pratiques 100 : aucune vérification ratée, alors que trois comparables sur quatre n'ont pas de meta description (le court texte affiché sous le titre dans Google).
- Accessibilité 94 contre 90 : bon score, mais deux vérifications ratées.

**Actions sur les deux vérifications ratées :**

- *Contrastes insuffisants* → foncer les textes clairs (ou éclaircir leur fond) sur la page d'accueil, au minimum un ratio 4,5:1 pour le texte courant. Effet attendu : lecture plus facile pour les malvoyants et sur écran en plein jour, et quelques points d'accessibilité gagnés.
- *Listes mal construites* (une liste `<ul>`/`<ol>` contient autre chose que des `<li>`) → corriger le gabarit HTML concerné pour que chaque élément soit dans un `<li>`. Effet attendu : les lecteurs d'écran annoncent correctement le nombre d'éléments. Correction simple, probablement dans un composant commun (menu, liste de ressources).

Avec ces deux corrections, aquagir viserait 100 en accessibilité Lighthouse (qui ne couvre qu'une partie du RGAA).

## 3. Ce que font les comparables

**Constat.** Sur octobre, les 4 sites ont des visites courtes (médiane 1 min 25, au-dessus du repère de 1 min 12 des 597 sites de l'État) et peu profondes (1,78 page par visite). Le public est très majoritairement sur ordinateur (86 % en médiane), ce qui colle à un public d'agents de collectivités au bureau. La recherche organique domine (71 %), l'accès direct suit (26 %), les sites référents pèsent peu (4 %) et les réseaux sociaux rien (0 %).

**Écarts marquants et hypothèses :**

- *territoires-climat* (jumeau le plus proche d'aquagir) a la visite la plus longue (2 min 08) et la plus profonde (2,41 pages), avec la plus forte part d'accès direct (38 %). Hypothèse : un parcours « par étapes » lié à une obligation (le PCAET) fait revenir des utilisateurs réguliers qui connaissent le site et l'explorent. C'est le modèle le plus pertinent pour aquagir.
- *avelo* est le plus dépendant de Google (77 %) avec la part d'ordinateur la plus faible (81 %). Hypothèse : des visiteurs qui arrivent sur une page précise (une aide, un appel à projets), trouvent l'information et repartent.
- *economie-circulaire* a de loin le plus de visites (9 507) mais l'engagement le plus faible (1,51 page). Hypothèse : un sujet plus large attire un public moins ciblé, qui consulte une seule page.

Ce que cela dit pour aquagir (hypothèse) : sur ce type de plateforme, le moteur de recherche amène la majorité des visiteurs, et la profondeur de visite dépend de la capacité à proposer une suite logique (étapes, ressources liées).

## 4. Évolution

Premier mois disponible dans les deux historiques (audience 2026-10, Lighthouse 2026-11) : pas encore de comparaison possible. Elle sera faite à partir de la prochaine analyse.

## 5. À faire

1. **Relever dans Matomo les chiffres d'aquagir d'octobre 2026** : durée moyenne de visite, pages par visite, part ordinateur et répartition des sources (moteurs de recherche, entrées directes, sites référents, réseaux sociaux). Les comparer à la médiane (1 min 25 ; 1,78 page ; 86 % ordinateur ; 71 % recherche) et surtout à territoires-climat (2 min 08 ; 2,41 pages).
2. **Corriger les contrastes et les listes HTML de la page d'accueil** : deux corrections rapides qui devraient porter l'accessibilité Lighthouse de 94 vers 100.
3. **Si la part de recherche organique d'aquagir est sous 71 %** : travailler les titres et meta descriptions des pages de ressources les plus consultées (pas seulement l'accueil, déjà à 100 en SEO), car c'est le premier canal d'acquisition de ce public.

## 6. Limites

Audience des comparables mesurée par Eulerian (aquagir par Matomo, méthodes de comptage différentes), sur 29 jours sur 31 et avec de petits volumes pour 3 sites sur 4, tous ADEME. Lighthouse ne mesure que la page d'accueil, et les scores varient de quelques points d'un passage à l'autre.
