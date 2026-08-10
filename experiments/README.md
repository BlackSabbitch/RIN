# experiments

This directory holds the **process** side of graph-memory experiments: how a run
was set up and launched, not what it found.

What goes here:

* run configs and parameters (graph size, model, walker policy, seeds);
* command scripts and recipes to reproduce a run;
* prompt/config diffs between comparable runs;
* notes taken *during* a run (setup issues, deviations from plan).

What does not go here: processed results, comparisons, conclusions — see
[`reports/`](../reports/README.md) for those.

## Журнал экспериментов

Каждый эксперимент: `experiments/experiment_N.md` (как) +
`reports/experiment_N.md` (что вышло) + код в `src/experiments/expN_*`.

| # | Тема | Код | Статус |
|---|---|---|---|
| 1 | Hub concentration (π на хабах, синтетический BA-граф, Ярус 1) | [`src/experiments/exp1_hub_concentration.py`](../src/experiments/exp1_hub_concentration.py) | done |
| 2 | Embryonic graph (ConceptNet+ATOMIC+Numberbatch, реальный Tier-2 граф) | [`src/experiments/exp2_embryonic_graph.ipynb`](../src/experiments/exp2_embryonic_graph.ipynb) | done |
| 3 | Golden micro-world — baseline без семантического вентиля | [`src/experiments/exp3_golden_microworld.ipynb`](../src/experiments/exp3_golden_microworld.ipynb) | done |
| 4 | Семантический вентиль `rel(B|q)` в `diffuse()` — тот же микромир, с фиксом | [`src/experiments/exp4_semantic_gate.ipynb`](../src/experiments/exp4_semantic_gate.ipynb) | done — вентиль работает верно, тест-кейс оказался про причинность, не про близость эмбеддингов (открытый вопрос) |
| 5 | Write-path — `event_log -> gate -> commit -> forensic index`, сценарий «Азоры» | [`src/experiments/exp5_write_path.ipynb`](../src/experiments/exp5_write_path.ipynb) | done — нашли и починили баг с одновременным коммитом кандидатов в одном батче (см. `reports/experiment_5.md`) |
