# QSA reduce12: проверенный microbenchmark receipt

## Вывод

На обоих GPU reduce12 снизил latency **полного компонента QSA chunk + merge на 26.739792% и 26.579580%**. Полный путь включает softmax и value accumulation. Это component latency reduction, не whole-model gain и не прирост TPS. Micro завершён 2026-10-09T11:03:24.203394+00:00.

| GPU | A, ms | B, ms | Сэкономлено, ms | Снижение latency |
|---|---:|---:|---:|---:|
| 0 | 1.0351595 | 0.7583600 | 0.2767995 | 26.739792% |
| 1 | 1.0319200 | 0.7576400 | 0.2742800 | 26.579580% |

Основной случай: n_q=32, context=65536. Порядок отдельных процессов A1/B1/B2/A2. A и B в таблице — среднее двух соответствующих process medians; формула 100 × (A−B)/A. Цифры независимо пересчитаны из summary.json и совпали с его decision. Оба результата проходят ранее заданный component gate ≥12%.

## Полнота и parity

- Все 16 запусков имеют exit_code=0 и actual_route_trace=true.
- Полные attention outputs и все raw scores имеют одинаковые SHA256 между A/B и обоими GPU для каждого входного случая. Проверяется весь output, не prefix/sample.
- Основной случай: 8 запусков. Edge n_q=1/context=4: 4 запуска. Edge n_q=33/context=4096 с masked pages: 4 запуска, на обоих GPU.
- Полные hashes и все исходные timings сохранены в qsa-reduce12-micro-results.json. Повторная проверка отчёта сверяла hashes из завершённого run receipt; GPU или бинарные output-файлы заново не исполнялись/сравнивались.

## ISA и ресурсы полного kernel

Проверены специализации A <1,false,true,false> и B <1,false,true,true>, а не отдельный score-only kernel.

| Метрика | A | B |
|---|---:|---:|
| Score shuffles, ds_bpermute_b32 | 60 | 16 |
| Score adds, v_add_f32_e32 | 60 | 16 |
| Dot FMAC, v_fmac_f32_e32 | 84 | 84 |
| VGPR | 42 | 48 |
| SGPR | 42 | 43 |
| Occupancy, waves/SIMD | 4 | 4 |
| LDS, bytes/block | 15872 | 15872 |
| Scratch, bytes/lane | 0 | 0 |
| SGPR/VGPR spills | 0/0 | 0/0 |

Score counts независимо пересчитаны между первым и вторым s_barrier полного disassembly. Во всём kernel ds_bpermute_b32 70→26, v_add_f32_e32 66→22, FMAC 87→87. Остаточные 10 shuffles относятся к остальному kernel. Количество инструкций статическое, не hardware-counter measurement. VGPR выросли, но compiler-reported occupancy не снизилась.

## Guard, opt-in и source boundary

Production patch меняет только src/kernels/cuda/qsa_decode_attn.cu. Новый путь default-off: STRATA_GFX906_ATTN_REDUCE12 должен быть ровно "1". Значения unset, "0", "10", "1x" его не включают. STRATA_GFX906_ATTN_REDUCE12_TRACE также требует ровно "1"; trace печатается один раз на host thread при фактическом выборе новой специализации.

Новый путь вложен в прежний use_query_swizzle: HIP gfx906 build, query-swizzle enabled, lane-cell disabled, INT8 kv_mode=1; calling thread's current device должен иметь точную архитектуру gfx906 и wavefront=64. Guard использует thread-local cache последнего device ordinal, повторяет проверку при смене device и закрывает путь при HIP errors. Старые флаги/их parsing не изменены. Fallbacks, qsa_decode_attn_step, softmax/value body и merge сохранены. Source proof содержит 384 guard truth-table cases; это source-level проверка, а не 384 аппаратных прогона. Runtime route traces присутствуют во всех 16 micro-запусках.

Source proof подтверждает соответствие production helper/full kernel screened micro modulo names/whitespace и отсутствие probe/bench/test macro в production patch. Это не заменяет отдельную проверку production binary ISA.

## Build и provenance

- Micro build успешен: exit_code=0; gfx906, -O3 -DNDEBUG -std=c++20, STRATA_GFX906_REDUCE12_PROBE=1; linked qualified kernels archive. Полный build command хранится в build-linked.json.
- Micro binary SHA256: 968b440b9759d2d635057eafd1dd9be177b3334a4511fc7d88053391d917366f.
- Production patch SHA256: ff08b97d7c71d74e46c5776cb5705280eff7df94f361f3865fb6527f4c60c942.
- Production source SHA256: 278f6080871552da95f18ea5e5af6a3e2a4208bf4d330368a6f054d895e91faf.
- Base source SHA256: c2dad92763333743b6c76cf05948c6fdcf706e28a8884353f78f8abd3de5cfa3.
- Controller evidence: /home/opencode/ai/qsa-reduce12-probe-20261009/summary.json, build-linked.json, build-linked.log, isa-summary.json, qsa-A-full.isa, qsa-B-full.isa. Их hashes включены в JSON receipt; local production-source-proof также включён.

## Интерпретация и следующий gate

Score-only diagnostic имеет иные lifetimes и dispatch/batching. Его timing нельзя вычитать из full для атрибуции softmax/value или превращать в whole-model projection. Raw score-only timings оставлены в JSON как диагностические данные.

Model screen 4438 на момент задания ещё выполняется; результатов в этом отчёте нет. Binary SHA256: ff348b38ad9b531e8df701311b1ae736f1378a6aaef322eeaa86e78f685917d9; база qualified8900 плюс только новый production patch. Model screen отдельно сохраняет qualified8900 epoch: frozen base f152172332693c933b8a3104ce193d8a4315c2b4 плюс qualified HC/J32/dequant/QSA/empty-PCIe/primary-commit, без перехода на новый upstream. По переданному контексту обе стороны сохраняют STRATA_PRIMARY_COMMIT_OVERLAP=1 и весь прежний набор flags; меняется только STRATA_GFX906_ATTN_REDUCE12=0/1. Reduce12 trace отключён в performance arms и включался только в отдельном production smoke. Эти сведения о model screen предоставлены отдельно; его raw manifests/results ещё не включены в micro receipt. Whole-model gain/TPS можно заявлять только по отдельному завершённому model screen.

Отчёт подготовлен только по имеющимся controller/cloud artifacts, без новых сборок, GPU запусков или GitHub публикации.
