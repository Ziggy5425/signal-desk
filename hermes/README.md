# Hermes agent buyer

A real [Hermes](https://github.com/NousResearch/hermes) agent is the **buyer** in this demo. In oneshot
mode (`hermes -z`) it reasons on **NVIDIA Nemotron 3 Ultra**, discovers the custom `signal-desk-buyer`
skill, and pays the desk's HTTP-402 — genuine agent-to-agent commerce, no human in the loop.

This folder holds the Hermes config + skill so you can reproduce it. It is kept **isolated** from any
production Hermes install via a dedicated `HERMES_HOME`.

## Setup

1. Pick an isolated home so this never touches a production Hermes:
   ```bash
   export HERMES_HOME=~/hermes-hack
   mkdir -p "$HERMES_HOME/skills/hackathon"
   ```
2. Copy this config + skill in:
   ```bash
   cp hermes/config.yaml "$HERMES_HOME/config.yaml"
   cp -r hermes/skills/hackathon/signal-desk-buyer "$HERMES_HOME/skills/hackathon/"
   ```
3. Set the model keys (the agent reasons on NVIDIA Nemotron; the `fast` alias uses OpenRouter):
   ```bash
   # config.yaml uses provider: custom pointed at NVIDIA's OpenAI-compatible NIM endpoint,
   # so the NVIDIA key goes in OPENAI_API_KEY.
   export OPENAI_API_KEY=nvapi-...          # your NVIDIA NIM key
   export OPENROUTER_API_KEY=sk-or-v1-...   # optional, only for `-m fast`
   ```
4. Start the Signal Desk in another terminal (see the repo root README), then let the agent buy:
   ```bash
   HERMES_HOME=~/hermes-hack hermes -z "Use the signal-desk-buyer skill to buy a premium NVDA signal."
   # if Nemotron's free tier is slow, put -m fast BEFORE -z:
   HERMES_HOME=~/hermes-hack hermes -m fast -z "Use the signal-desk-buyer skill to buy a premium NVDA signal."
   ```

The skill calls `agent_buy.py` from your clone of this repo. Point it at the right path by setting
`SIGNAL_DESK` to your checkout (see the skill file), or edit the one path line in `SKILL.md`.
