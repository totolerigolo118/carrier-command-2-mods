#!/bin/bash
# usage: auto_test.sh LABEL "modules to retire for this run (may be empty)"
LABEL="$1"; RETIRE="$2"; SRC="${3:-}"; PAT="${4:-AUTO RESULT\|AUTO FAIL}"
W=$HOME/Documents/ZClaude/mods/cc2-patchs/outil/tests_en_jeu
ATELIER="$HOME/Documents/ZClaude/mods/cc2-patchs"
ROM="$HOME/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents/Resources/rom_0"
EXE="$HOME/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents/MacOS/build_mac"
SUP="$HOME/Library/Application Support/Carrier Command 2"
TARGET="$ROM/scripts/library_custom_7.lua"
OUT="$W/auto_report_$LABEL.txt"
EMPTY=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
FULLMD5=ce8dafec115286d0412608224e42199c
: > "$OUT"
log() { echo "$(date +%H:%M:%S) $*" >> "$OUT"; }
BK="$W/saves_backup_$LABEL"
rm -rf "$BK"; mkdir -p "$BK"
cp -Rp "$SUP/saved_games" "$BK/saved_games"; cp -p "$SUP/persistent_data.xml" "$BK/persistent_data.xml"
RETIRED=0
cleanup() {
  : > "$TARGET"; rm -f "$SUP/vitesse_escadrille.txt"
  S=$(shasum -a 256 "$TARGET" | cut -d' ' -f1)
  [ "$S" = "$EMPTY" ] && log "library_custom_7.lua empty again" || log "WARNING library_custom_7 sha=$S"
  if [ $RETIRED -eq 1 ] && ! pgrep -x build_mac >/dev/null; then
    (cd "$ATELIER" && python3 outil/patchs_cc2.py --activer $RETIRE >> "$OUT" 2>&1)
  fi
  M=$(md5 -q "$EXE"); [ "$M" = "$FULLMD5" ] && log "program md5 back to the 14-module state ($M)" || log "WARNING program md5 is $M (expected $FULLMD5)"
  diff -rq "$BK/saved_games" "$SUP/saved_games" > "$W/saves_diff_$LABEL.txt" 2>&1
  [ -s "$W/saves_diff_$LABEL.txt" ] && log "saves CHANGED: $(tr '\n' ';' < "$W/saves_diff_$LABEL.txt" | cut -c1-300)" || log "saves unchanged"
  rm -rf "$SUP/saved_games"; cp -Rp "$BK/saved_games" "$SUP/saved_games"; cp -p "$BK/persistent_data.xml" "$SUP/persistent_data.xml"
  diff -rq "$BK/saved_games" "$SUP/saved_games" >/dev/null && log "saves restored identical" || log "WARNING saves restore mismatch"
}
trap cleanup EXIT
[ "$(shasum -a 256 "$TARGET" | cut -d' ' -f1)" = "$EMPTY" ] || { log "ABORT: library_custom_7.lua not empty"; trap - EXIT; exit 0; }
pgrep -x build_mac >/dev/null && { log "ABORT: game already running"; trap - EXIT; exit 0; }
if [ -n "$RETIRE" ]; then
  (cd "$ATELIER" && python3 outil/patchs_cc2.py --retirer $RETIRE >> "$OUT" 2>&1) && RETIRED=1
  log "retired modules: $RETIRE (md5 now $(md5 -q "$EXE"))"
fi
[ -n "$SRC" ] || SRC="$W/auto/library_custom_7.lua"
cp "$SRC" "$TARGET"
log "auto script installed"
READY=0
for i in $(seq 1 120); do
  IDLE=$(ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print int($NF/1000000000); exit}')
  if [ "${IDLE:-0}" -ge 120 ]; then READY=1; break; fi
  sleep 15
done
[ $READY -eq 1 ] || { log "NO LAUNCH: user stayed active 30 min"; exit 0; }
log "user idle ${IDLE}s: launching"
BEFORE=$(wc -c < "$SUP/releve_cc2.txt" 2>/dev/null || echo 0)
ls ~/Library/Logs/DiagnosticReports 2>/dev/null | sort > /tmp/cc2_diag_b_$LABEL.txt
open "steam://rungameid/1489630"
PID=""
for i in $(seq 1 40); do PID=$(pgrep -x build_mac | head -1); [ -n "$PID" ] && break; sleep 3; done
[ -n "$PID" ] || { log "game never started"; exit 0; }
log "started pid $PID"
T0=$(date +%s); DONE=0; LAST=""
while [ $(( $(date +%s) - T0 )) -lt 3000 ]; do
  sleep 20
  pgrep -x build_mac >/dev/null || { log "PROCESS GONE (crash?)"; break; }
  tail -c +$((BEFORE+1)) "$SUP/releve_cc2.txt" > "$W/auto_new_$LABEL.txt" 2>/dev/null
  if grep -q "$PAT" "$W/auto_new_$LABEL.txt"; then
    if [ $DONE -eq 0 ]; then DONE=$(date +%s); log "result line seen after $(( DONE - T0 ))s"; fi
    [ $(( $(date +%s) - DONE )) -ge 60 ] && break
  fi
  EL=$(( $(date +%s) - T0 ))
  [ $(( EL % 120 )) -lt 20 ] && log "t+${EL}s alive $(ps -o pcpu=,rss= -p $PID | tr -s ' ') | $(grep -o 'AUTO [A-Za-z ]*' "$W/auto_new_$LABEL.txt" | tail -1)"
done
if pgrep -x build_mac >/dev/null; then
  kill -TERM $PID
  for i in 1 2 3 4 5 6; do sleep 5; pgrep -x build_mac >/dev/null || break; done
  pgrep -x build_mac >/dev/null && log "still running after SIGTERM" || log "game closed cleanly"
fi
sleep 3
tail -c +$((BEFORE+1)) "$SUP/releve_cc2.txt" > "$W/auto_new_$LABEL.txt"
grep -E "^AUTO" "$W/auto_new_$LABEL.txt" > "$W/auto_lines_$LABEL.txt"
ls ~/Library/Logs/DiagnosticReports 2>/dev/null | sort > /tmp/cc2_diag_a_$LABEL.txt
log "new crash reports: $(comm -13 /tmp/cc2_diag_b_$LABEL.txt /tmp/cc2_diag_a_$LABEL.txt | tr '\n' ' ')"
log "AUTO lines: $(wc -l < "$W/auto_lines_$LABEL.txt")"
log "DONE"
