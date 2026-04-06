# Описание Yao Meta Skill

`YAO = Yielding AI Outcomes` означает ориентацию на реальные результаты от ИИ. Цель здесь не в том, чтобы написать больше prompt-текста, а в том, чтобы получать переиспользуемые AI-активы и прикладные операционные результаты.

`yao-meta-skill` — это легкая, но строгая система для создания, оценки, упаковки и управления переиспользуемыми agent skills.

Он преобразует сырые workflows, transcripts, prompts, notes и runbooks в переиспользуемые skill-пакеты с:

- понятной поверхностью срабатывания
- компактным `SKILL.md`
- необязательными references, scripts и evals
- контролируемым benchmark/reference scan до глубокого authoring
- автоматически создаваемым минималистичным HTML-обзором на белом фоне для каждого нового skill
- нейтральными исходными метаданными и клиентскими адаптерами
- встроенными проверками governance, promotion и portability в стандартном потоке

## Архитектура

В hero-версии вся система сводится к одной линии: превратить разрозненный вход в управляемый и переиспользуемый skill package.

```mermaid
flowchart LR
    A["Входы<br/>workflow / prompt / transcript / docs / notes"] --> B["Маршрут<br/>SKILL.md"]
    B --> C["Проектирование<br/>method + gates"]
    C --> D["Исполнение<br/>create / validate / eval / promote"]
    D --> E["Выходы<br/>skill package + reports + adapters"]
```

Как читать это за 10 секунд:

- **Входы**: стартуем с workflow, prompt, документов и заметок.
- **Маршрут**: компактный `SKILL.md` сначала задает границу и trigger.
- **Проектирование**: выбираются нужные archetype, quality gates и разбиение ресурсов.
- **Исполнение**: единый CLI создает, проверяет, оптимизирует и продвигает skill.
- **Выходы**: результатом становится skill package плюс доказательства оценки, governance и portability.

## Quick Start

1. Опишите workflow, набор prompts или повторяющуюся задачу, которую хотите превратить в skill.
2. Сначала выполните короткий reference scan, где основными источниками будут GitHub и сильные публичные эталоны, а локальные файлы будут использоваться только для адаптации, приватности и совместимости.
3. Используйте `yao-meta-skill`, чтобы сгенерировать или улучшить пакет в режиме scaffold, production или library.
4. Каждый новый skill также получает `reports/skill-overview.html` и `reports/reference-scan.md`, чтобы быстро понять архитектуру, логику, способ использования и полезные ориентиры.

## Results

- `make test` сейчас проходит
- на текущем regression-наборе trigger eval дает `0` false positives и `0` false negatives
- все три набора train / dev / holdout проходят
- packaging contracts для `openai`, `claude` и `generic` проходят проверку

## Текущие сильные стороны

В последней взвешенной оценке проекта Yao сильнее всего выглядит в тех измерениях, которые действительно определяют production-grade meta-skill system:

- **Полнота методологии `9.8`**: в репозитории уже есть формальная skill engineering doctrine, covering gate selection, non-skill decisions, governance и resource boundaries.
- **Инженерная toolchain `9.8`**: инициализация, валидация, оптимизация, отчеты, promotion checks, packaging и CI связаны в единый operational flow.
- **Governance / maintenance / safety `9.8`**: важные skills могут иметь lifecycle state, review cadence, maturity score, trust boundaries и promotion evidence.
- **Evaluation loop `9.7`**: качество trigger проверяется через train/dev/holdout, blind holdout, adversarial holdout, judge-backed blind eval, drift history и promotion gates.
- **Portability / packaging `9.6`**: исходники остаются нейтральными, а adapters, degradation rules и packaging contracts сохраняют переносимую семантику между целевыми средами.
- **Trigger и boundary design `9.5`**: route confusion, anti-pattern regressions и promotion policy превращают качество trigger в аудируемую routing-задачу.
- **Context efficiency `9.4`**: entrypoint остается компактным, context budgets имеют tier-структуру, а quality density тоже измеряется.

Общий вектор здесь осознанный: легкий вход, строгий evaluation loop и governance как часть качества skill.

## Почему Yao

- **Легкий**: entrypoint остается компактным, context budgets заданы явно, а дополнительная структура добавляется только тогда, когда она действительно окупается.
- **Строгий**: качество trigger проверяется через family regressions, blind holdout, adversarial holdout, route confusion, judge-backed blind eval и promotion gates.
- **Управляемый**: важные skills рассматриваются как поддерживаемые активы с lifecycle, maturity expectation, owner и review cadence.
- **Портируемый**: source metadata остается нейтральной, а adapters, degradation rules и packaging contracts сохраняют переносимую семантику между средами.

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

- **Сначала метод, а не просто prompt**: skill creation рассматривается как формальный engineering workflow
- **Ориентация на trigger optimization**: description проходит через route confusion, blind holdout, adversarial families и promotion policy
- **Легкий entrypoint**: `SKILL.md` остается компактным, а references, scripts и evals добавляются только когда действительно нужны
- **Цельная toolchain**: init, validate, optimize, report, package и test проходят через единый CLI и CI path
- **Управляется как актив**: важные skills могут иметь owner, lifecycle, maturity expectation и review cadence
- **Портируемость по умолчанию**: исходники нейтральны, а совместимость обрабатывается через adapters и degradation rules
- **Высокая плотность доказательств**: route scorecards, regression history, context budgets, portability scores и promotion decisions публикуются как артефакты

## Для кого подходит

Проект лучше всего подходит для:

- agent builders
- команд внутреннего tooling
- prompt engineers, переходящих к skill engineering
- организаций, создающих библиотеки переиспользуемых skills

## Лицензия

MIT. См. [LICENSE](../LICENSE).
