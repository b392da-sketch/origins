#!/bin/bash
# One gate job on a GitHub machine: run (or continue from a checkpoint in $CKPT) up to three histories side by side
# (one process each: the machine has 4 CPUs), or one experiment.
# Usage: gates/run_job.sh REQUEST KIND JOBS      JOBS = "planet:seed[,planet:seed...]"
set -e
FAIL=0
REQ=$1; KIND=$2; JOBS=$3
WS=${JOBS%%:*}
export ORIGINS_PARAMS=$(python3 -c "import json;print(json.dumps(json.load(open('$REQ')).get('params',{})))")
GATE=$(python3 -c "import json;print(json.load(open('$REQ'))['gate'])")
YEARS=$(python3 -c "import json;print(json.load(open('$REQ')).get('years',5000))")
export ORIGINS_AFTER_FIRST=$(python3 -c "import json;print(json.load(open('$REQ')).get('after_first',6000))")
CKPT=${CKPT:-/tmp/ckpt}
# Temporary files and mapped arrays (origins/spill.py) on the runner's larger disk when it has one (29 Nov 2026)
if [ -d /mnt ] && sudo -n true 2>/dev/null; then
  sudo mkdir -p /mnt/origins-tmp && sudo chown "$(id -u)" /mnt/origins-tmp && export TMPDIR=/mnt/origins-tmp
fi
df -h / "${TMPDIR:-/tmp}" | sed 's/^/disk: /' || true
BUDGET=${BUDGET:-16200}          # 4.5 hours, leaving time to save a large world before the 5h50m limit
rm -rf gates/results_$GATE          # keep only this job's own results (the repository holds earlier ones)
mkdir -p "$CKPT"
TAG=""; case "$KIND" in run_*) TAG="_${KIND#run_}" ;; esac     # run_nostore -> _nostore; G4a arms: run_nopop -> _nopop
if [ -n "$(ls -A "$CKPT" 2>/dev/null)" ]; then
  # a later stage: continue only the histories that still have a checkpoint (the others finished earlier)
  KEEP=""
  for J in ${JOBS//,/ }; do
    W=${J%%:*}; R=${J##*:}
    if ls "$CKPT"/w${W}_s${R}${TAG}.zip >/dev/null 2>&1; then KEEP="$KEEP,$J"; else echo "history $J finished in an earlier stage"; fi
  done
  JOBS=${KEEP#,}
  [ -n "$JOBS" ] || { echo "nothing to continue"; mkdir -p out; exit 0; }
fi
case "$KIND" in
  run|run_*)
    case "$KIND" in
      run) FLAG="" ;;
      run_nostore) FLAG="--no-storage" ;;
      run_noinst) FLAG="--no-institutions" ;;
      *) FLAG="--arm ${KIND#run_}" ;;                  # G4a's named arms (gates/g4.py ARMS; Codex review 034)
    esac
    PIDS=""
    for J in ${JOBS//,/ }; do
      python -m gates.$GATE run --jobs $J --years $YEARS --budget $BUDGET --workers 1 --ckpt "$CKPT" $FLAG > "log_$J.txt" 2>&1 &
      PIDS="$PIDS $!"
    done
    FAIL=0
    for P in $PIDS; do wait $P || FAIL=1; done
    for J in ${JOBS//,/ }; do echo "== history $J"; tail -n 30 "log_$J.txt"; done
    ;;   # a failed history is reported at the end, after its siblings' results and checkpoints are kept (review 011)
  *)           python -m gates.$GATE $KIND --worlds $WS ;;
esac
mkdir -p out
if ls gates/results_$GATE/*.json >/dev/null 2>&1; then
  cp gates/results_$GATE/*.json out/
fi
# a finished history leaves no checkpoint; an unfinished one keeps its checkpoint for the next stage
for J in ${JOBS//,/ }; do
  W=${J%%:*}; R=${J##*:}
  if ls gates/results_$GATE/run_w${W}_s${R}${TAG}[._]*json >/dev/null 2>&1 || [ -f gates/results_$GATE/run_w${W}_s${R}${TAG}.json ]; then
    rm -f "$CKPT"/w${W}_s${R}${TAG}.*
  else
    echo "history $J not finished within this job's time; checkpoint kept for the next job"
    if [ "${FINAL_STAGE:-0}" = 1 ] && [ -f "$CKPT"/w${W}_s${R}${TAG}.json ]; then
      # the last stage: no next job, so record the history as incomplete (the report names it and the gate is not
      # decided) and keep the checkpoint as an artifact to continue by hand (Codex review 037, finding 1)
      python3 -c "import json,sys;m=json.load(open(sys.argv[1]));print(json.dumps({'status':'incomplete','world_seed':int(sys.argv[2]),'run_seed':int(sys.argv[3]),'arm':sys.argv[4] or None,'year':m.get('year'),'seconds':m.get('seconds')}))" \
        "$CKPT"/w${W}_s${R}${TAG}.json $W $R "${TAG#_}" > out/run_w${W}_s${R}${TAG}.json
      echo "history $J INCOMPLETE after the last stage (year $(python3 -c "import json;print(json.load(open('$CKPT/w${W}_s${R}${TAG}.json'))['year'])"))"
      INCOMPLETE=1
    fi
  fi
done
case "$KIND" in run*) ;; *) rm -rf "$CKPT"/* ;; esac
if [ "${INCOMPLETE:-0}" != 0 ]; then echo "a history did not finish in the last stage"; FAIL=1; fi
if [ "${FAIL:-0}" != 0 ]; then echo "a history failed: see its log above"; exit 1; fi
