"""Summarize a focal contestant's real matches using the Fall 2026 course scoring."""

import argparse
import csv
from math import sqrt
from pathlib import Path


POINTS = {"villager": {"win": 1, "loss": 0}, "seer": {"win": 1, "loss": 0},
          "wolf": {"win": 2, "loss": -1}}
FIELDS = ("match_id", "mode", "policy", "seat", "role", "status", "side_result", "opponent_set")


def summarize(records):
    groups = {}
    seen = set()
    for line, row in enumerate(records, 2):
        if any(row.get(field) is None for field in FIELDS):
            raise ValueError(f"Row {line}: incomplete CSV row")
        row = {field: row[field].strip() for field in FIELDS}
        match_id = row["match_id"]
        if not match_id or match_id in seen:
            raise ValueError(f"Row {line}: each game needs one unique match ID for the focal agent")
        seen.add(match_id)
        mode, policy = row["mode"], row["policy"]
        if mode not in {"practice", "tournament"} or not policy:
            raise ValueError(f"Row {line}: expected practice/tournament and a policy name")
        group = groups.setdefault((mode, policy), {"pending_or_void": 0, "by_role": {}})
        if row["status"] in {"pending", "no_result"} and not row["side_result"]:
            group["pending_or_void"] += 1
            continue
        role, result = row["role"], row["side_result"]
        if (row["status"] != "completed" or role not in POINTS or result not in POINTS[role]
                or row["seat"] not in {"0", "1", "2", "3", "4", "5", "6"}):
            raise ValueError(f"Row {line}: check seat, role, status and the focal side's win/loss")
        stats = group["by_role"].setdefault(role, {"games": 0, "wins": 0, "points": 0})
        stats["games"] += 1
        stats["wins"] += int(result == "win")
        stats["points"] += POINTS[role][result]
    return groups


def wilson(wins, n):
    z = 1.96
    p = wins / n
    divisor = 1 + z*z/n
    midpoint = (p + z*z/(2*n)) / divisor
    half = z * sqrt(p*(1-p)/n + z*z/(4*n*n)) / divisor
    return max(0, midpoint - half), min(1, midpoint + half)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    with args.csv.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not set(FIELDS) <= set(reader.fieldnames or []):
            parser.error("Required columns: " + ",".join(FIELDS))
        try:
            groups = summarize(reader)
        except ValueError as error:
            parser.error(str(error))
    if not groups:
        print("No match rows recorded.")
    for (mode, policy), group in groups.items():
        roles = group["by_role"]
        n = sum(r["games"] for r in roles.values())
        points = sum(r["points"] for r in roles.values())
        print(f"{mode} / {policy}: {n} completed, {points} course points; "
              f"{group['pending_or_void']} pending or no result.")
        if n:
            print(f"  Mean points per completed game: {points/n:.2f}")
        for role in POINTS:
            if role not in roles:
                continue
            r = roles[role]
            lo, hi = wilson(r["wins"], r["games"])
            print(f"  {role}: {r['wins']}/{r['games']} team wins "
                  f"(95% Wilson interval {lo:.0%} to {hi:.0%}), {r['points']} points")


if __name__ == "__main__":
    main()
