#!/bin/bash
# One gate job on a GitHub machine: run (or continue from a checkpoint in $CKPT) one history or experiment.
# Usage: gates/run_job.sh REQUEST KIND WS RS
set -e
REQ=$1; KIND=$2; WS=$3; RS=$4
export ORIGINS_PARAMS=$(python3 -c "import json;print(json.dumps(json.load(open('$REQ')).get('params',{})))")
GATE=$(python3 -c "import json;print(json.load(open('$REQ'))['gate'])")
YEARS=$(python3 -c "import json;print(json.load(open('$REQ')).get('years',5000))")
CKPT=${CKPT:-/tmp/ckpt}
BUDGET=${BUDGET:-16200}          # 4.5 hours, leaving time to save a large world before the 5h50m limit
rm -rf gates/results_$GATE          # keep only this job's own results (the repository holds earlier ones)
mkdir -p "$CKPT"
case "$KIND" in
  run)         python -m gates.$GATE run --jobs $WS:$RS --years $YEARS --budget $BUDGET --workers 1 --ckpt "$CKPT" ;;
  run_nostore) python -m gates.$GATE run --jobs $WS:$RS --years $YEARS --budget $BUDGET --workers 1 --ckpt "$CKPT" --no-storage ;;
  *)           python -m gates.$GATE $KIND --worlds $WS ;;
esac
mkdir -p out
if ls gates/results_$GATE/*.json >/dev/null 2>&1; then
  cp gates/results_$GATE/*.json out/
  rm -rf "$CKPT"/*                   # finished: no checkpoint to carry on
else
  echo "not finished within this job's time; checkpoint kept for the next job"
fi
