# C161 Werewolf Agent

A self-hosted LLM agent for seven-player Werewolf on the [AltruAgent](https://altruagent-game.com/) platform, built for the UCLA Stats C161/C261 (Fall 2026) final project.

The agent runs Qwen2.5-3B-Instruct on the local machine through llama.cpp. You do not need a model API key. It plays through the official [AltruAgent starter SDK](https://github.com/UCLA-Trustworthy-AI-Lab/altruagent-starter/tree/2d7a11b04e0d4b9a60ce4b3aff0ad7dc45c1a2a3), pinned to commit `2d7a11b`. For every vote, night action and message, the LLM chooses from the legal actions the server offers.

> **Status:** this repository currently holds the runtime: the installer, the local model client, the command-line entry point and match scoring. The decision policy, its evaluation harness and results will be published here before the tournament.

## Setup (Windows x64)

You need Python 3.11+ and Git. From this folder, run:

```powershell
.\Setup.ps1
```

The script:
1. Downloads llama.cpp `b12635` (Vulkan build) and the Qwen2.5-3B-Instruct `Q4_K_M` GGUF (about 2.1 GB) into `.runtime/` and checks their SHA-256 hashes.
2. Creates `.venv`.
3. Installs this package and the pinned SDK.

On other systems, set `WEREWOLF_SERVER` and `WEREWOLF_MODEL_FILE` to point at a compatible `llama-server` binary and GGUF file.

## Configuration

Copy `.env.example` to `.env` and put your Official Agent Key in it. `.env` is git-ignored.

| Variable | Meaning |
| --- | --- |
| `ALTRUAGENT_OFFICIAL_AGENT_KEY` | Platform key from Agent Configuration |
| `ALTRUAGENT_CONTROL_URL` | Control plane, default `https://api.altruagent-game.com` |
| `WEREWOLF_PORT` | Local model port, default `18261` |
| `WEREWOLF_SERVER`, `WEREWOLF_MODEL_FILE` | Override the llama.cpp binary and weights |

## Scoring real matches

Log one row per platform game in a CSV with the header `match_id,mode,policy,seat,role,status,side_result,opponent_set`. Then run:

```powershell
.\.venv\Scripts\python.exe -m werewolf_agent.scoring match-log.csv
.\.venv\Scripts\python.exe -m pytest -q
```

The script uses the course scoring: village and seer score +1 for a win and 0 for a loss; wolves score +2 for a win and −1 for a loss. It reports, separately for each mode and policy, the course points and a Wilson 95% interval on each role's win rate.

## Layout

```
werewolf_agent/
  __init__.py   create_agent() for the SDK
  __main__.py   check / practice / tournament, starts the local model
  model.py      llama.cpp chat-completions client with a JSON-schema answer
  scoring.py    course-points summary for real matches
tests/          scoring tests
Setup.ps1       pinned model and runtime installer
```
