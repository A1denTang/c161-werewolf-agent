"""AltruAgent loads create_agent once for each assigned seat."""

import os
from pathlib import Path


def create_agent():
    from .model import LocalModel
    from .policy import WerewolfAgent

    memory = os.getenv("WEREWOLF_MEMORY", "carry")
    project_logs = Path(__file__).resolve().parent.parent / "logs"
    return WerewolfAgent(LocalModel(), memory=memory, log_dir=project_logs)
