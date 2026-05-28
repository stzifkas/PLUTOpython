# Screenshots

Text captures of the `pluto-ecss` CLI. Used by the README, the docs site,
and the Finish-Up-A-Thon submission post. All files are plain UTF-8 so
they can be pasted into markdown code blocks without an image.

Re-record after CLI changes with:

```bash
./scripts/record_screenshots.sh
```

| File | Captures |
| --- | --- |
| `01_demo_original.txt`       | `pluto-ecss demo examples/01_original.pluto` final TUI frame |
| `02_demo_bringup.txt`        | `pluto-ecss demo examples/05_full_bringup.pluto` final TUI frame |
| `03_run_continuation.txt`    | `pluto-ecss run examples/10_continuation_test.pluto` |
| `04_run_step_subbodies.txt`  | `pluto-ecss run examples/14_step_sub_bodies.pluto` |
| `05_compile_python.txt`      | Default `pluto-ecss compile` (threaded runtime, functions style) |
| `06_compile_async.txt`       | `pluto-ecss compile --runtime async` |
| `07_compile_class.txt`       | `pluto-ecss compile --style class` |
| `08_compile_json.txt`        | `pluto-ecss compile --emit json` |
| `09_fmt_canonical.txt`       | `pluto-ecss fmt examples/01_original.pluto` |
| `10_parse_error.txt`         | Friendly parse error (deliberate `if` with no `then`) |
| `11_cli_help.txt`            | `pluto-ecss --help` |
