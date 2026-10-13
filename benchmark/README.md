# Rover performance workload proposal

Use `models/Rover-v7.solidcraft` as the pinned native fixture. Its SHA-256 is `fcb08540b1db08325f366fd0ff235f84f66d96406961482736bc097d7248c6d6`. Do not substitute the separately recorded variant: it has a different history and hash.

The approved fixture contains 1,395 bodies, 576 sketches, 3,792 sketch curves, 36 component definitions plus root, 17 revolute joints and 3,324 history entries, including 1,395 body transfers. It occupies 216,036 bytes and produces 1,025,680 display triangles in the 0.7.0 probe.

## Initial measurements (2026-10-13)

Official Windows x64 portable SolidCraft 0.7.0, Ryzen AI Max+ 395 (16 cores / 32 logical processors), Windows 11 Pro 10.0.26200, 28 GiB OS-visible RAM. Three sequential fresh CLI processes; no OS-cache flush. The desktop app remained open and background load was not controlled. These are preliminary local reference measurements, not a before/after comparison, a performance guarantee or a GUI benchmark.

| Phase | Median of three runs |
|---|---:|
| File read | 0.25 ms |
| Decode / validate / repair | 62.62 ms |
| Timeline evaluation | 23.434 s |
| World placement / display mesh preparation | 7.130 s |
| Whole CLI process wall time | 31.515 s |

The phase timers do not sum exactly to process wall time: process startup, feature-report output and teardown are included only in the latter. The mesh phase includes world-state preparation, not just triangle generation. It is not GPU frame time or time to the first visible desktop frame. Native decoding also includes container handling and document validation; it is not a pure JSON-parser microbenchmark.

All three runs returned 1,395 bodies and 1,025,680 triangles with no feature errors. [Raw JSONL, summary and environment](results/) are included. Exact CLI-binary and fixture hashes are recorded. Peak memory, CPU utilization and GPU timings were not measured.

Largest individually reported feature times (median):

| Feature | Time |
|---|---:|
| Shell2 | 5739.92 ms |
| Extrude18 | 858.20 ms |
| Extrude26 | 846.52 ms |
| Extrude22 | 790.26 ms |
| Extrude14 | 679.81 ms |
| Extrude10 | 667.90 ms |
| Extrude6 | 655.79 ms |
| Move2 | 303.82 ms |

Per-feature timing is diagnostic; the reported values do not necessarily account for all work in the total evaluation phase. Profile before attributing the remaining time to a particular subsystem.

## Reproduce the CLI probe

Requires Python 3 and a SolidCraft CLI with `bench-open` (verified with 0.7.0); no Python packages are needed.

```sh
python benchmark/bench_open.py --cli /path/to/solidcraft-cli --runs 5 --out benchmark-results
```

Some source builds retain the compatible `solvecraft-cli` executable name. A single invocation is:

```sh
solidcraft-cli bench-open models/Rover-v7.solidcraft
solidcraft-cli bench-open models/Rover-v7.solidcraft --parse-only
```

Each run starts a new process and therefore a fresh process-local geometry cache. The OS file cache is not cleared. The script stops on timeout, CLI failure, missing phases or feature errors; it retains successful raw output and records the fixture hash. Run candidate and baseline alternately on the same machine, build profile and file. Use at least five repetitions for comparisons; retain outliers and report median and range, rather than asserting a fixed CI wall-clock limit from this initial three-run sample.

## Proposed desktop and editing matrix

| Workload | Fixed procedure | Metrics |
|---|---|---|
| Native cold opening | Fresh desktop process; same settings and initial blank state; open the pinned native file | Request-to-ready and first presented frame, read/parse/evaluation/placement/mesh phases, peak memory |
| Reopening | Reopen in the same process; explicitly report which caches are warm | Same phase timings; keep separate from cold results |
| Viewport movement | Same window resolution, DPI, renderer/backend, MSAA, camera path and visible components; run orbit/pan/zoom after a warm-up | Frame-time median/p95, CPU and GPU time when available, input latency; control-channel round trips reported separately |
| Hover and selection | Fixed normalized cursor path over the same camera view; compare browser collapsed and expanded | Picking latency, frame-time median/p95, correct selection, unexpected geometry rebuilds |
| Component visibility | Hide/show the roof assemblies, then restore exactly the same set | Latency, allocation/memory changes, whether geometry/mesh caches rebuild unnecessarily |
| Late placement edit | On a disposable copy, edit the final `Move14` X translation from 4 mm to 5 mm, restore 4 mm, then undo/redo | Recomputed feature counts, wall time, cache reuse, final body placements and unchanged unrelated geometry |
| Early geometry edit | Define a small valid change and restore on a disposable copy; record the exact feature/input and validate it before adopting the case | Evaluation time and recomputed count, errors/warnings, shape and reference invariants |
| Joint drive | Use a documented safe limited angle near the saved pose, then restore it | Latency and placement/mesh work; check joint errors and final transforms |
| Save / reopen | Save a copy after restoration, close and reopen it | Save latency, file size, identities/appearances/geometry retained |

For desktop phase profiling, use the project's `SOLVECRAFT_PROFILE_OPEN=1` instrumentation where supported and verify the exact build. Record `ui.inspect` CPU frame timings separately from GPU presentation/FPS. Do not run screenshot capture or GIF encoding in the timed interval.

The desktop/interaction/edit matrix is **proposed, not measured in this release**. The build timelapse is visual evidence of the workload, not timing evidence: it includes transport, captures, waits and edited playback timing.

## Acceptance and scope

1. Keep immutable fixture hashes and exact build/OS/hardware/render settings with every result.
2. Compare body names/counts, component and joint structure, placements, appearances, error/warning state and geometry measurements before claiming a speedup. Full shape equivalence is not established by triangle count alone.
3. Start as an opt-in benchmark, then extract smaller focused regression fixtures when profiling identifies a bottleneck. Avoid flaky absolute timing gates in shared CI.
4. Keep geometry evaluation, placement, display meshing, UI picking/browser cost and serialization separate. A faster CLI opening does not by itself prove a faster desktop interaction.
5. This is a many-part native assembly workload. It does not replace Boolean-heavy, constrained-sketch, STEP-import or memory-stress fixtures. No claim that it reproduces every symptom in the linked issues.

Related upstream work: [performance umbrella #287](https://github.com/bherbruck/solidcraft/issues/287), [cold opening #255](https://github.com/bherbruck/solidcraft/issues/255), [desktop/MCP editing #611](https://github.com/bherbruck/solidcraft/issues/611).
