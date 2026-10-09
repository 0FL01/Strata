# QSA reduce12: итог квалификации gfx906

## Результат

Reduce12 прошёл frozen-stack квалификацию: в matched 64K ABBA получены **+3.440197% PP** и **+1.581280% TG**, при точном совпадении всех 1024 output token IDs во всех четырёх arms. Обе пары положительные по обеим метрикам.

| 64K / 1024 outputs | Control A | Candidate B | Изменение |
|---|---:|---:|---:|
| PP, tokens/s | 625.033728419 | 646.536120162 | +3.440197% |
| TG, tokens/s | 52.280242284 | 53.106939053 | +1.581280% |

Результат относится к указанному workload и frozen epoch. Он не является универсальным приростом для всех запросов или оценкой качества модели.

## Что именно сравнивалось

Порядок: **A1/B1/B2/A2**. Один и тот же binary SHA256 `ff348b38ad9b531e8df701311b1ae736f1378a6aaef322eeaa86e78f685917d9`, INT8 KV, prompt=65536, output=1024; greedy sampling temperature=0, top_p=1, top_k=1, seed=12345. Prompt reuse выключен; placement фиксирован, layer split=27, adapt_every=0, resident KV=32768, context capacity=204800, MTP window=16384.

Обе стороны сохраняют qualified8900 HC/J32, dequant, QSA query-swizzle, empty-PCIe skip и primary-commit overlap. Frozen base: `f152172332693c933b8a3104ce193d8a4315c2b4`; перехода на новый upstream нет. В performance manifests набор env flags совпадает за исключением **STRATA_GFX906_ATTN_REDUCE12=0/1**. STRATA_PRIMARY_COMMIT_OVERLAP=1 остаётся на обеих сторонах. Reduce12 trace отсутствует в performance arms; он применялся отдельно в production smoke. Прежние диагностические flags одинаковы в A/B.

| Arm | Prompt ms | Decode ms | PP | TG |
|---|---:|---:|---:|---:|
| A1 | 104822.3 | 19590.4 | 625.210475252 | 52.270499837 |
| B1 | 101338.2 | 19278.4 | 646.705783209 | 53.116441198 |
| B2 | 101391.4 | 19285.3 | 646.366457116 | 53.097436908 |
| A2 | 104881.6 | 19583.1 | 624.856981587 | 52.289984732 |

Агрегация: среднее rates двух A и двух B; gain=100×(B_mean/A_mean−1). Парные сравнения B1/A1 и B2/A2:

- PP: +3.438091% и +3.442304%
- TG: +1.618392% и +1.544181%

PP = полный reported prompt count / native prompt_ms; последний prompt token исполняется в первом decode window. TG = actual output count / native decode_ms. Load и request wall times сохранены отдельно и в PP/TG не включены. Все четыре arms имеют одинаковые accepted/offered (648/872), cache hits/lookups (582049/600000), engine configuration и полные output IDs. Cost gate: PP≥1%, обе PP пары положительны, TG≥−1%, exact IDs; пройден.

## Дополнительные проверки

| Проверка | Результат | Ограничение |
|---|---|---|
| 4K / 1024 outputs | PP +3.070518%, TG +1.328129%; все 1024 IDs совпали | Одна пара, не ABBA |
| 200000 / 256 outputs | PP 616.858242275, TG 45.537016614; exact 256 IDs с архивным reference | Capacity/parity, **без fresh performance comparison** |
| Production smoke 4K / 32 | Пройден, 32 IDs совпадают с началом 4K qualification output | Отдельный smoke, не performance arm |
| API tools / vision / parking-cache | Passed; 2 vision trials | API summary + whitelisted verification evidence |
| Auth / UI | Unauthenticated models: HTTP 401; UI: HTTP 404 | Whitelisted verification evidence |
| API disconnect/cancel | Passed; 12 chunks до disconnect, 14 output tokens, follow-up «42», тот же engine process | Ранний разрыв HTTP stream и успешный следующий запрос |
| Восстановление | original_configuration_restored=true | Byte-for-byte equality и совпадающие before/after SHA256 config и compose сохранены |

Исходный `api/verification-evidence.json` (содержимое включено в поле `api.verification_evidence` архивного [JSON receipt](qsa-reduce12-results.json), отдельный raw файл здесь не публикуется) содержит whitelisted auth/UI status codes, число vision trials и реальные before/after SHA256 конфигурации и compose. Config: `779040cc1834777da4c316515f03fcda972e9c08201174227e5df562633c8499`; compose: `d524d2c65d1190e42a7d750b8ddf74ef20f0d1a81dbf50585d53e99af077a85d` (каждый hash одинаков до/после). Byte-for-byte equality проверена при квалификации; здесь независимо проверены сохранённые hashes и equality fields.

Просмотренный cancel helper фильтрует ожидаемый executable, требует ровно один процесс и сравнивает пару (PID, starttime) до disconnect и после follow-up. Его SHA256 совпал с verification evidence. Raw PID/starttime **не сохранялись**: подтверждена успешная проверка пары, но её исходные значения в receipt отсутствуют. Просмотренный main driver в finally возвращает исходные bytes config/compose, перезапускает сервис, проверяет health и byte equality. Hashes обоих просмотренных scripts включены в receipt. Ключи, приватные API-конфиги и содержимое .env не читались и не включены.

Обе полные 256-ID последовательности (candidate и архивный primary-commit reference) сохранены в JSON. Сохранены также все четыре отдельных 1024-ID массива ABBA и оба 1024-ID массива 4K. Сравнение не ограничивается префиксом или hash.

## Micro и production ISA

Отдельный завершённый micro: **latency полного QSA chunk+merge −26.739792% / −26.579580%** на двух GPU. Это component latency reduction; его нельзя считать приростом model TPS. Score-only diagnostic компилируется с иными lifetimes и не вычитается из full timing. Подробности и raw receipts сохранены отдельно в `qsa-reduce12-micro-report.md` и `qsa-reduce12-micro-results.json` без изменения исторического статуса того отчёта.

Production ISA gate подтверждает для полного kernel:

- Shuffles 70→26 по всему kernel; score region micro 60→16
- Dot FMAC score region 84→84; production full kernel FMAC 87→87
- VGPR 42→48, SGPR 42→43; LDS 15872 bytes, private segment 0 на обеих сторонах
- Micro compiler reports: occupancy 4→4 waves/SIMD, scratch и SGPR/VGPR spills равны нулю

Новый production путь default-off и включается только точным значением `STRATA_GFX906_ATTN_REDUCE12=1`. Guard сохраняет query-swizzle, INT8, disabled lane-cell, текущий gfx906 device и wavefront=64. Softmax/value, merge, fallbacks и decode-step не изменены; source proof и guard coverage описаны в micro report.

## Release и публикация

Immutable qualified release: `/home/radneon/strata/releases/gfx906-qualified-20261009-reduce12`.

Binary SHA256: `ff348b38ad9b531e8df701311b1ae736f1378a6aaef322eeaa86e78f685917d9`.

Release **не promoted**; live API остаётся на stablece. Public source port source-reviewed и apply-checked, но отдельно **не compiled/qualified и не pushed как implementation branch**. Здесь публикуется только patch artifact. Этот результат не означает upstream build pass; опубликованного PR нет. Статус release/public port передан отдельно от performance summaries.

## Проверяемость и границы доказательств

Основной источник: `/home/opencode/ai/qsa-reduce12-model-receipts-20261009`:

- `build.json`, `production-isa-gate.json`
- `model/summary.json`, `model/smoke.json`, четыре `model/runs/*.manifest.json`
- `qualification/summary.json`, `api/summary.json`, `api/cancel.json`, `api/verification-evidence.json`

Архивный 200K reference: `/home/opencode/ai/primary-commit-overlap-receipts-20261009/qualification/summary.json`.

`qsa-reduce12-results.json` содержит санитизированные числовые данные, все необходимые ID arrays, SHA256 исходных evidence files, сохранённые performance flags и пересчитанные gains. Build argv, private API health/config blobs, credentials и .env исключены. Production build exit_code=0 и sources_restored=true записаны в build receipt.

Из корня checkout архивной ветки: `python3 bench/check_gfx906_reduce12_results.py bench/results/2026-10-09-gfx906-qsa-reduce12/qsa-reduce12-results.json --selftest`. Проверены arithmetic, полный parity, счётчики, flags/binary/epoch isolation, ISA, API restore/cancel и scope 200K. Все 15 намеренных corruption cases отвергнуты, включая подмену auth status, vision coverage, restoration hashes/equality и helper hash. Validator проверяет согласованность сохранённых receipts, не повторяет аппаратные тесты и не доказывает происхождение файлов без доверия к исходным SHA256.

Это один 64K ABBA experiment и одна 4K pair; confidence intervals и широкая workload qualification не заявляются. Exact IDs доказывают parity данных fixtures, не general correctness для произвольных входов. При подготовке отчёта выполнялись только controller/cloud reads и offline обработка, без новых GPU запусков, сборок или GitHub writes.


## Архивные файлы

- [Числовой receipt и полные token IDs](qsa-reduce12-results.json)
- [Исторический micro report](qsa-reduce12-micro-report.md) и [micro receipt](qsa-reduce12-micro-results.json); его раздел о незавершённом model screen отражает более ранний момент, итог находится в этом отчёте.
- [Production patch для frozen qualified stack](qsa-reduce12-production.patch), SHA256 `ff08b97d7c71d74e46c5776cb5705280eff7df94f361f3865fb6527f4c60c942`.
- [Public-source patch для 1f555de86254cc01ec06882c70f9584c1f09ec39](qsa-reduce12-upstream.patch), SHA256 `8434022d2affa8309f4e2a0acc8182a7c28da52c9f814afbd04094b3e6f33e86`. Эти два patches — альтернативы для разных bases, не последовательные patches.
- [Будущий clean-rebase probe workflow](PROBE-REUSE.md), [wrapper](run-existing-probe.sh), [offline validator](../../check_gfx906_reduce12_results.py).

Source receipt paths выше — provenance labels; raw controller directories не включены. Поля publication/release в JSON описывают receipt-time state. Публикация этих bench artifacts не меняет runtime source, PR1661 или live API и не является upstream build pass.
