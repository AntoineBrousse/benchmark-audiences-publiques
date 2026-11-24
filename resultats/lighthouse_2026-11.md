# Qualité technique (Lighthouse) – 2026-11

Mesure Lighthouse via PageSpeed Insights (desktop), médiane de 3 passages par page. Scores de 0 à 100 (plus c'est haut, mieux c'est) ; LCP, TBT et CLS : plus c'est bas, mieux c'est.

| Site | Performance | Accessibilité | Bonnes pratiques | SEO | LCP (s) | TBT (ms) | CLS |
|---|---|---|---|---|---|---|---|
| **aquagir.fr** | 90 | 94 | 100 | 100 | 0.86 | 178 | 0.015 |
| territoires-climat.ademe.fr | 67 | 85 | 77 | 83 | 2.15 | 358 | 0 |
| avelo.ademe.fr | 59 | 95 | 77 | 100 | 0.66 | 1778 | 0.063 |
| economie-circulaire.ademe.fr | 92 | 97 | 100 | 92 | 1.13 | 0 | 0.014 |
| experimentationsurbaines.ademe.fr | 96 | 79 | 100 | 69 | 0.82 | 0 | 0.1 |
| *Médiane des sites comparables* | 79.5 | 90 | 88.5 | 87.5 | 0.975 | 179 | 0.038 |

Repères Lighthouse : 90-100 = bon, 50-89 = à améliorer, 0-49 = mauvais. LCP bon sous 2,5 s ; CLS bon sous 0,1.

## Vérifications ratées

Ce qui fait perdre des points à chaque site (ratées dans au moins la moitié des passages).

### aquagir.fr
- **SEO** : aucune
- **Accessibilité** : Les couleurs d'arrière-plan et de premier plan ne sont pas suffisamment contrastées; Les listes ne contiennent pas uniquement des éléments `<li>` et des éléments de type script (`<script>` et `<template>`).
- **Bonnes pratiques** : aucune

### territoires-climat.ademe.fr
- **SEO** : Le document ne contient pas d'attribut "meta description"; Les liens ne peuvent pas être explorés
- **Accessibilité** : La taille et l'espacement des zones cibles tactiles sont insuffisants.; Les boutons n'ont pas de nom accessible; Les couleurs d'arrière-plan et de premier plan ne sont pas suffisamment contrastées; Les liens n'ont pas de nom visible
- **Bonnes pratiques** : Des problèmes ont été enregistrés dans le panneau `Issues` des outils de développement Chrome; La page n'utilise pas le protocole HTTPS

### avelo.ademe.fr
- **SEO** : aucune
- **Accessibilité** : Les liens n'ont pas de nom visible; Les éléments d'en-tête ne sont pas classés séquentiellement par ordre décroissant
- **Bonnes pratiques** : Des problèmes ont été enregistrés dans le panneau `Issues` des outils de développement Chrome; Utilise des cookies tiers

### economie-circulaire.ademe.fr
- **SEO** : Le document ne contient pas d'attribut "meta description"
- **Accessibilité** : Les listes ne contiennent pas uniquement des éléments `<li>` et des éléments de type script (`<script>` et `<template>`).
- **Bonnes pratiques** : aucune

### experimentationsurbaines.ademe.fr
- **SEO** : Des éléments d'image n'ont pas d'attribut `[alt]`; Le document ne contient pas d'attribut "meta description"; Le document ne contient pas d'élément `<title>`; Le fichier robots.txt n'est pas valide
- **Accessibilité** : Des éléments d'image n'ont pas d'attribut `[alt]`; La taille et l'espacement des zones cibles tactiles sont insuffisants.; Le document ne contient pas d'élément `<title>`; Les couleurs d'arrière-plan et de premier plan ne sont pas suffisamment contrastées; Les liens n'ont pas de nom visible
- **Bonnes pratiques** : aucune


Limites : page d'accueil uniquement, score variable d'un passage à l'autre, l'accessibilité Lighthouse ne couvre qu'une partie du RGAA.
