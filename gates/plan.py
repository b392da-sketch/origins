"""Turn a gate request (gates/requests/*.json) into the job list for GitHub Actions.

A request looks like:
  {"gate": "g1", "label": "g1-check", "years": 5000, "planets": "1-5", "seeds": "1-15",
   "extras": ["groups"]}

Histories of the same kind are packed PER_JOB to a job (one runner of 4 CPUs runs them side by side; Ben, 14 November
2026: until then one history per job left three CPUs idle). "extras" adds the gate's paired experiments, one job per
planet; "nostore_seeds" adds knock-out histories with food storage turned off. A request may set "per_job" (1 restores
the old packing). Prints a JSON matrix for the workflow; each entry has "kind" and "jobs" ("planet:seed,...").
"""
from __future__ import annotations

import json
import sys

PER_JOB = 3


def _range(s) -> list:
    if isinstance(s, list):
        return [int(x) for x in s]
    a, _, b = str(s).partition("-")
    return list(range(int(a), int(b or a) + 1))


def _pack(jobs: list, per: int) -> list:
    """Group history jobs of the same kind into jobs of up to `per` histories; other kinds stay one per job."""
    out, groups = [], {}
    for j in jobs:
        if j["kind"].startswith("run"):
            groups.setdefault(j["kind"], []).append(j)
        else:
            out.append({"kind": j["kind"], "jobs": f"{j['ws']}:{j['rs']}", "name": j["name"]})
    for kind, js in groups.items():
        for i in range(0, len(js), per):
            part = js[i:i + per]
            out.append({"kind": kind, "jobs": ",".join(f"{j['ws']}:{j['rs']}" for j in part),
                        "name": kind + "-" + "-".join(f"w{j['ws']}s{j['rs']}" for j in part)})
    return out


def plan(req: dict) -> dict:
    return {"include": _pack(_plan(req)["include"], int(req.get("per_job", PER_JOB)))}


def _plan(req: dict) -> dict:
    if "jobs" in req or "nostore_jobs" in req or "noinst_jobs" in req:          # rerun only the named histories ("planet:seed")
        jobs = [{"kind": "run", "ws": int(j.split(":")[0]), "rs": int(j.split(":")[1])} for j in req.get("jobs", [])]
        jobs += [{"kind": "run_nostore", "ws": int(j.split(":")[0]), "rs": int(j.split(":")[1])}
                 for j in req.get("nostore_jobs", [])]
        jobs += [{"kind": "run_noinst", "ws": int(j.split(":")[0]), "rs": int(j.split(":")[1])}
                 for j in req.get("noinst_jobs", [])]
        for j in jobs:
            j["name"] = f"{j['kind']}-w{j['ws']}-s{j['rs']}"
        return {"include": jobs}
    jobs = [{"kind": "run", "ws": ws, "rs": rs} for rs in _range(req["seeds"]) for ws in _range(req["planets"])]
    if req.get("nostore_seeds"):
        jobs += [{"kind": "run_nostore", "ws": ws, "rs": rs}
                 for rs in _range(req["nostore_seeds"]) for ws in _range(req["planets"])]
    if req.get("noinst_seeds"):
        jobs += [{"kind": "run_noinst", "ws": ws, "rs": rs}
                 for rs in _range(req["noinst_seeds"]) for ws in _range(req["planets"])]
    for extra in req.get("extras", []):
        jobs += [{"kind": extra, "ws": ws, "rs": 0} for ws in _range(req["planets"])]
    for j in jobs:
        j["name"] = f"{j['kind']}-w{j['ws']}" + (f"-s{j['rs']}" if j["kind"].startswith("run") else "")
    return {"include": jobs}


if __name__ == "__main__":
    req = json.load(open(sys.argv[1]))
    print(json.dumps(plan(req), separators=(",", ":")))
