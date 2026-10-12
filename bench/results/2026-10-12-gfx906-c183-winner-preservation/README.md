# Preserved c183 combined winner: recovery checkpoint

Date: 2026-10-12. This checkpoint preserves the historical result and its artifacts; it is not a new benchmark or a claim about current upstream performance.

The original eight-arm combined experiment measured arithmetic-mean rates of **672.137075656 prompt tokens/s** and **53.728913301 generated tokens/s**. The [complete original report](https://github.com/0FL01/Strata/blob/9fbdfb0074ace398191d7b8d8298bd9fb9e43b97/bench/results/2026-10-12-gfx906-c183-peer-affinity-combined/README.md) retains all arms, including two negative TG pairs and the additional peer CPU cost. Later experiments use different baselines and do not replace this result.

## Secured and independently checked

- A separate private off-machine copy of the exact winning executable: SHA256 `48dba26a0951c85e44fe7124ef161e719495bad040b6d7d6d8e95f219b7100a8`, 21,625,872 bytes.
- A separate private copy of the original c183 control executable: SHA256 `c18316d678a669c309cb95e2f5de9af03fa5573256fd0e093aafc4b41000d049`.
- The compiled project link closure: 26 payload files (objects, archives and three build-metadata text files), 53,973,595 expanded bytes, including all 11 unique literal winning project link inputs. The private compressed archive is 14,633,395 bytes, SHA256 `4b32ad51a8fc4993ca4f6ee3a64a0a0715bb2cfa543270879609d94cb0962d4f`.
- All 121 members of the original raw-result archive and all 22 members of the runtime-source archive were rehashed against their existing copies. Original result archive SHA256: `ee42a48082f4fc4ae2fab07d20aedc93f28fc99d61b5f978c41ea4c5341fa573`.
- The actual per-arm controls and full historical output/work evidence remain preserved. Reproduction instructions use the executed B1 configuration and A1 control, cross-checked against the reviewed runtime. An inherited release manifest contains older spec/suffix metadata and is not the launch authority. The executed profile uses spec6/maxT4/suffix0.

Independent binary-copy review: `4a010ed722bce2d0e720e4f098c09dde32d96df5c52d0129a005077b1615951c`.
Independent compiled-closure review: `50a87fffa7f00e3ce68086a26466320fba7657b7960846663edb0f2b4e01d9d2`.
Original experiment review: `dd26a5916964a0780bd3f7ccee4325ca2c14141dd6cf19c2c02d0ab15250785c`.

These private backups contain no new executable behavior and were made without rerunning the model or modifying the originals. Binaries, model payloads and private deployment paths are not published here.

## Source/rebuild completeness still being checked

The retained integration and peer packages preserve the baseline-to-N4-to-affinity source changes, exact overlay headers and qualified kernel source. Original attention source and the original build receipt have also been recovered. The exact original selector source has now been found in a retained production package: SHA256 `8d836acd211b7e493cd50bd680d128489f3f25f94ea26725afbab2402ef899bc`, 69,575 bytes. Independent recovery review now verifies all seven recorded original compiled source pins, both full N4/affinity packages and their overlay headers: `6d128d06757be07865e3f1241666fb22887ad017e5376fd3908d67fc741c8fab`. A strictly scoped archive preserves campaign patches/scripts, the seven recovered source files, N4/peer overlays and receipts: **30 files / 4,018,347 expanded bytes**, archive **2,194,080 bytes**, SHA256 `dc118dd9434b1089e1c9931da9c87fe8c23606a80e6085401e211e5b6f4b8373`. Its manifest is `6b259706f05b08efc80cc0afe3c0037f0a1dc28f87d57fc87b0ec9ca936a1444`. It excludes the full working tree and Git history and must not be called a complete source checkout. Independent final readback verifies all 30 loose payloads and 31 archive entries (payloads plus manifest): review `136217f1ed39b833d0761a19e15dcda008a5a85554cdf4bc29280336c4fcac4d`. An earlier absent-directory lookup remains retained.

Complete header/dependency correspondence, availability of the pinned external compiler/runtime image and libraries, and a recovery/rebuild rehearsal remain separate open checks. The secured executable and compiled-link copies must not be described as a fully verified clean-source rebuild package yet. Further recovery will append evidence rather than overwrite the historical winner.

The small separate metadata/review/reproduction archive is an index of these private copies, not the payload backup itself. Original checkpoints are retained separately from future build and cleanup destinations.
