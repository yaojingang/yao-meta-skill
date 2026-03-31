# Présentation de Yao Meta Skill

`yao-meta-skill` est une méta-skill conçue pour créer d'autres agent skills.

Il transforme des workflows bruts, des transcripts, des prompts, des notes et des runbooks en paquets de skills réutilisables avec :

- une surface de déclenchement claire
- un `SKILL.md` léger
- des references, scripts et evals optionnels
- des métadonnées sources neutres et des adaptateurs spécifiques au client

## Quick Start

1. Décrivez le workflow, l'ensemble de prompts ou la tâche répétée que vous voulez transformer en skill.
2. Utilisez `yao-meta-skill` pour générer ou améliorer le paquet en mode scaffold, production ou library.
3. Exécutez `context_sizer.py`, `trigger_eval.py` et `cross_packager.py` selon le besoin pour valider et exporter le résultat.

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

- **Neutre par défaut** : les fichiers source restent neutres, les adaptateurs ne sont générés qu'en cas de besoin
- **Efficace en contexte** : le projet pousse explicitement le détail hors du fichier principal
- **Pensé pour l'évaluation** : les contrôles de déclenchement et de taille font partie du workflow
- **Réutilisable** : la sortie est un paquet complet, pas juste un paragraphe de prompt
- **Portable** : la compatibilité passe par l'empaquetage, pas par la duplication des sources

## Public idéal

Ce projet est particulièrement adapté à :

- constructeurs d'agents
- équipes d'outillage interne
- prompt engineers évoluant vers des skills structurées
- organisations construisant des bibliothèques de skills réutilisables

## Licence

MIT. Voir [LICENSE](../LICENSE).
