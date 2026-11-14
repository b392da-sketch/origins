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
BUDGET=${BUDGET:-16200}          # 4.5 hours, leaving time to save a large world before the 5h50m limit
rm -rf gates/results_$GATE          # keep only this job's own results (the repository holds earlier ones)
mkdir -p "$CKPT"
TAG=""; [ "$KIND" = run_nostore ] && TAG="_nostore"; [ "$KIND" = run_noinst ] && TAG="_noinst"
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
  run|run_nostore|run_noinst)
    FLAG=""; [ "$KIND" = run_nostore ] && FLAG="--no-storage"; [ "$KIND" = run_noinst ] && FLAG="--no-institutions"
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
  fi
done
case "$KIND" in run*) ;; *) rm -rf "$CKPT"/* ;; esac
if [ "${FAIL:-0}" != 0 ]; then echo "a history failed: see its log above"; exit 1; fi
