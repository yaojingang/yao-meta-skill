# Présentation de Yao Meta Skill

`yao-meta-skill` est un système léger mais rigoureux pour créer, évaluer, empaqueter et gouverner des agent skills réutilisables.

Il transforme des workflows bruts, des transcripts, des prompts, des notes et des runbooks en paquets de skills réutilisables avec :

- une surface de déclenchement claire
- un `SKILL.md` léger
- des references, scripts et evals optionnels
- des métadonnées sources neutres et des adaptateurs spécifiques au client
- des contrôles de gouvernance, de promotion et de portabilité intégrés au flux standard

## Quick Start

1. Décrivez le workflow, l'ensemble de prompts ou la tâche répétée que vous voulez transformer en skill.
2. Utilisez `yao-meta-skill` pour générer ou améliorer le paquet en mode scaffold, production ou library.
3. Exécutez `context_sizer.py`, `trigger_eval.py` et `cross_packager.py` selon le besoin pour valider et exporter le résultat.

## Results

- `make test` passe actuellement
- sur le jeu de régression courant, trigger eval a `0` faux positifs et `0` faux négatifs
- les suites train / dev / holdout passent toutes
- les contrats de packaging `openai`, `claude` et `generic` sont validés

## Points forts actuels

Dans la dernière revue pondérée partagée pour le projet, Yao se distingue surtout sur les dimensions qui définissent une méta-skill réellement exploitable en production :

- **Complétude méthodologique `9.8`** : le dépôt possède désormais une doctrine explicite pour le skill engineering, la sélection des gates, les non-skills, la gouvernance et les frontières de ressource.
- **Chaîne d'outillage `9.8`** : initialisation, validation, optimisation, reporting, contrôle de promotion, packaging et CI sont reliés dans un flux unique.
- **Gouvernance / maintenance / sécurité `9.8`** : les skills importantes peuvent porter un état de cycle de vie, une cadence de revue, un score de maturité, des frontières de confiance et des preuves de promotion.
- **Boucle d'évaluation `9.7`** : la qualité de déclenchement est vérifiée via train/dev/holdout, blind holdout, adversarial holdout, judge-backed blind eval, drift history et promotion gates.
- **Portabilité / packaging `9.6`** : la source reste neutre tandis que les adaptateurs, règles de dégradation et contrats de packaging préservent la sémantique réutilisable selon l'environnement cible.
- **Déclenchement et frontières `9.5`** : route confusion, régressions anti-pattern et promotion policy transforment le déclenchement en problème de routage auditable.
- **Efficacité de contexte `9.4`** : le point d'entrée reste compact, les budgets de contexte sont hiérarchisés et la densité de qualité est suivie.

La direction est volontaire : garder une entrée légère, rendre l'évaluation stricte, et traiter la gouvernance comme une partie de la qualité d'une skill.

## Ce que fait le projet

Ce projet permet de créer, refactoriser, évaluer et empaqueter des skills comme des briques de capacité durables plutôt que comme des prompts ponctuels.

Sa logique de conception est simple :

1. identifier le vrai travail récurrent derrière la demande
2. définir une frontière propre pour que chaque paquet fasse un travail cohérent
3. optimiser la description de déclenchement avant d'allonger le corps
4. garder le fichier principal compact et déplacer le détail vers les references ou les scripts
5. ajouter des garde-fous qualité seulement lorsqu'ils sont utiles
6. exporter des artefacts de compatibilité uniquement pour les clients nécessaires

## Pourquoi ce projet existe

Dans la plupart des équipes, la connaissance opérationnelle utile est dispersée dans les chats, les prompts personnels, les habitudes orales et les workflows non documentés. Ce projet convertit cette connaissance implicite en :

- paquets de skills découvrables
- flux d'exécution répétables
- instructions à faible coût de contexte
- actifs réutilisables pour l'équipe
- distributions prêtes pour la compatibilité

## Structure du dépôt

```text
yao-meta-skill/
├── SKILL.md
├── README.md
├── LICENSE
├── .gitignore
├── agents/
│   └── interface.yaml
├── references/
├── scripts/
└── templates/
```

## Composants principaux

### `SKILL.md`

Le point d'entrée principal. Il définit la surface de déclenchement, les modes opératoires, le workflow compact et le contrat de sortie.

### `agents/interface.yaml`

La source de vérité neutre pour les métadonnées. Ce fichier stocke les informations d'affichage et de compatibilité sans lier l'arborescence source à un chemin spécifique à un fournisseur.

### `references/`

Les documents longs qui ne doivent pas gonfler le fichier principal. On y trouve les règles de conception, les guides d'évaluation, la stratégie de compatibilité et les rubriques de qualité.

### `scripts/`

Des utilitaires qui rendent la méta-skill opérationnelle :

- `trigger_eval.py` : vérifie si une description de déclenchement est trop large ou trop faible
- `context_sizer.py` : estime le poids de contexte et avertit si le chargement initial devient trop grand
- `cross_packager.py` : génère des artefacts d'export spécifiques au client à partir du paquet source neutre

### `templates/`

Des modèles de départ pour des paquets simples ou plus avancés.

## Comment l'utiliser

### 1. Utiliser directement la skill

Invoquez `yao-meta-skill` lorsque vous souhaitez :

- créer une nouvelle skill
- améliorer une skill existante
- ajouter des evals à une skill
- transformer un workflow en paquet réutilisable
- préparer une skill pour une adoption plus large dans l'équipe

### 2. Générer un nouveau paquet de skill

Le flux typique est :

1. décrire le workflow ou la capacité
2. identifier les phrases de déclenchement et les sorties attendues
3. choisir le mode scaffold, production ou library
4. générer le paquet
5. lancer les vérifications de taille et de déclenchement si nécessaire
6. exporter les artefacts de compatibilité ciblés

### 3. Exporter des artefacts de compatibilité

Exemples :

```bash
python3 scripts/cross_packager.py ./yao-meta-skill --platform openai --platform claude --zip
python3 scripts/context_sizer.py ./yao-meta-skill
python3 scripts/trigger_eval.py --description "Create and improve agent skills..." --cases ./cases.json
```

## Avantages

- **Méthode d'abord, pas prompt d'abord** : la création de skill est traitée comme un workflow d'ingénierie formel
- **Pensé pour l'optimisation du déclenchement** : les descriptions passent par route confusion, blind holdout, familles adversariales et promotion policy
- **Léger au point d'entrée** : `SKILL.md` reste compact et les references, scripts, evals ne sont ajoutés que lorsqu'ils sont utiles
- **Outillage cohérent** : initialisation, validation, optimisation, reporting, packaging et test passent par un CLI et un chemin CI unifiés
- **Gouverné comme un actif** : les skills importantes peuvent porter ownership, lifecycle, attentes de maturité et cadence de revue
- **Portable par défaut** : les sources restent neutres et la compatibilité est gérée par des adaptateurs et des règles de dégradation
- **Riche en preuves** : route scorecards, regression history, context budgets, portability scores et promotion decisions sont publiés comme artefacts

## Public idéal

Ce projet est particulièrement adapté à :

- constructeurs d'agents
- équipes d'outillage interne
- prompt engineers évoluant vers des skills structurées
- organisations construisant des bibliothèques de skills réutilisables

## Licence

MIT. Voir [LICENSE](../LICENSE).
