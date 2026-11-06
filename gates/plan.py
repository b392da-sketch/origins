"""Turn a gate request (gates/requests/*.json) into the job list for GitHub Actions.

A request looks like:
  {"gate": "g1", "label": "g1-check", "years": 5000, "planets": "1-5", "seeds": "1-15",
   "extras": ["groups"]}

Each history becomes one job (one runner). "extras" adds the gate's paired experiments,
one job per planet. Prints a JSON matrix for the workflow.
"""
from __future__ import annotations

import json
import sys


def _range(s) -> list:
    if isinstance(s, list):
        return [int(x) for x in s]
    a, _, b = str(s).partition("-")
    return list(range(int(a), int(b or a) + 1))


def plan(req: dict) -> dict:
    jobs = [{"kind": "run", "ws": ws, "rs": rs} for rs in _range(req["seeds"]) for ws in _range(req["planets"])]
    for extra in req.get("extras", []):
        jobs += [{"kind": extra, "ws": ws, "rs": 0} for ws in _range(req["planets"])]
    for j in jobs:
        j["name"] = f"{j['kind']}-w{j['ws']}" + (f"-s{j['rs']}" if j["kind"] == "run" else "")
    return {"include": jobs}


if __name__ == "__main__":
    req = json.load(open(sys.argv[1]))
    print(json.dumps(plan(req), separators=(",", ":")))
