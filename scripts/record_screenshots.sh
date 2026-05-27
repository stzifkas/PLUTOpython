#!/usr/bin/env bash
# Re-record the text captures committed under docs/screenshots/.
# Run from the repository root after any change that affects CLI output.
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p docs/screenshots

# `demo` exits after the procedure completes so a short timeout is plenty.
timeout 8  plutopy demo  examples/01_original.pluto    < /dev/null > docs/screenshots/01_demo_original.txt 2>&1
timeout 15 plutopy demo  examples/05_full_bringup.pluto < /dev/null > docs/screenshots/02_demo_bringup.txt 2>&1

plutopy run examples/10_continuation_test.pluto > docs/screenshots/03_run_continuation.txt    2>&1
plutopy run examples/14_step_sub_bodies.pluto    > docs/screenshots/04_run_step_subbodies.txt  2>&1

plutopy compile examples/10_continuation_test.pluto                     > docs/screenshots/05_compile_python.txt 2>&1
plutopy compile --runtime async examples/01_original.pluto              > docs/screenshots/06_compile_async.txt  2>&1
plutopy compile --style class   examples/04_events.pluto                > docs/screenshots/07_compile_class.txt  2>&1
plutopy compile --emit json     examples/08_watchdog.pluto              > docs/screenshots/08_compile_json.txt   2>&1
plutopy fmt examples/01_original.pluto                                  > docs/screenshots/09_fmt_canonical.txt  2>&1

# Deliberately broken script to capture the friendly parse-error output.
cat > /tmp/bad.pluto <<'EOF'
procedure
  main
    if x = 1
      log "hi"
    end if
  end main
end procedure
EOF
plutopy parse /tmp/bad.pluto > docs/screenshots/10_parse_error.txt 2>&1 || true
rm -f /tmp/bad.pluto

plutopy --help > docs/screenshots/11_cli_help.txt 2>&1

echo "captured $(ls docs/screenshots/ | wc -l) screenshots under docs/screenshots/"
