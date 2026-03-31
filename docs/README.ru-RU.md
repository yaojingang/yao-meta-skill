# Описание Yao Meta Skill

`yao-meta-skill` — это meta-skill для создания других agent skills.

Он преобразует сырые workflows, transcripts, prompts, notes и runbooks в переиспользуемые skill-пакеты с:

- понятной поверхностью срабатывания
- компактным `SKILL.md`
- необязательными references, scripts и evals
- нейтральными исходными метаданными и клиентскими адаптерами

## Quick Start

1. Опишите workflow, набор prompts или повторяющуюся задачу, которую хотите превратить в skill.
2. Используйте `yao-meta-skill`, чтобы сгенерировать или улучшить пакет в режиме scaffold, production или library.
3. При необходимости запустите `context_sizer.py`, `trigger_eval.py` и `cross_packager.py`, чтобы проверить и экспортировать результат.

## Results

- `make test` сейчас проходит
- на текущем regression-наборе trigger eval дает `0` false positives и `0` false negatives
- все три набора train / dev / holdout проходят
- packaging contracts для `openai`, `claude` и `generic` проходят проверку

## Что делает проект

Этот проект помогает создавать, перерабатывать, оценивать и упаковывать skills как долговечные capability-пакеты, а не как одноразовые prompts.

Его логика проста:

1. определить реальную повторяющуюся задачу за пользовательским запросом
2. задать чистую границу skill, чтобы один пакет решал одну связанную задачу
3. оптимизировать trigger description до того, как раздувать основное тело
4. держать основной файл маленьким, а детали переносить в references или scripts
5. добавлять quality gates только тогда, когда они действительно окупаются
6. экспортировать compatibility artifacts только для реально нужных клиентов

## Зачем нужен этот проект

У большинства команд важные операционные знания разбросаны по чатам, личным prompts, устным привычкам и недокументированным workflows. Этот проект превращает такое скрытое знание в:

- обнаруживаемые skill-пакеты
- повторяемые execution flows
- инструкции с меньшей нагрузкой на контекст
- переиспользуемые командные активы
- готовые к совместимости дистрибутивы

## Структура репозитория

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

## Ключевые компоненты

### `SKILL.md`

Главная точка входа skill. Здесь задаются surface trigger, operating modes, compact workflow и output contract.

### `agents/interface.yaml`

Нейтральный единый источник метаданных. Он хранит display и compatibility metadata, не привязывая дерево исходников к vendor-specific path.

### `references/`

Длинные материалы, которые не должны раздувать основной skill-файл. Здесь находятся design rules, evaluation guidance, compatibility strategy и quality rubrics.

### `scripts/`

Утилиты, которые делают meta-skill по-настоящему рабочей:

- `trigger_eval.py`: проверяет, не слишком ли широкая или слабая trigger description
- `context_sizer.py`: оценивает вес контекста и предупреждает, если initial load становится слишком большим
- `cross_packager.py`: собирает client-specific export artifacts из нейтрального исходного пакета

### `templates/`

Стартовые шаблоны для простых и более сложных skill-пакетов.

## Как использовать

### 1. Использовать skill напрямую

Вызывайте `yao-meta-skill`, когда хотите:

- создать новую skill
- улучшить существующую skill
- добавить evals в skill
- превратить workflow в переиспользуемый пакет
- подготовить skill для более широкого использования в команде

### 2. Сгенерировать новый skill-пакет

Типичный поток:

1. описать workflow или capability
2. определить trigger phrases и expected outputs
3. выбрать режим scaffold, production или library
4. сгенерировать пакет
5. при необходимости запустить size и trigger checks
6. экспортировать targeted compatibility artifacts

### 3. Экспортировать compatibility artifacts

Примеры:

```bash
python3 scripts/cross_packager.py ./yao-meta-skill --platform openai --platform claude --zip
python3 scripts/context_sizer.py ./yao-meta-skill
python3 scripts/trigger_eval.py --description "Create and improve agent skills..." --cases ./cases.json
```

## Преимущества

- **Нейтральность по умолчанию**: исходники остаются vendor-neutral, а адаптеры создаются только при необходимости
- **Эффективность по контексту**: детали явно выносятся из главного skill-файла
- **Ориентация на оценку**: проверки trigger и размера встроены в workflow
- **Переиспользуемость**: результатом является пакет, а не просто абзац prompt-текста
- **Портируемость**: совместимость обеспечивается упаковкой, а не дублированием исходников под каждого клиента

## Для кого подходит

Проект лучше всего подходит для:

- agent builders
- команд внутреннего tooling
- prompt engineers, переходящих к skill engineering
- организаций, создающих библиотеки переиспользуемых skills

## Лицензия

MIT. См. [LICENSE](../LICENSE).
