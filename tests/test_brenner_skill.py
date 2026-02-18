import os
import json
from src.synthia.skills.brenner_skill.brenner_skill import BrennerSkill
from src.integrations.brenner_adapter.heart_soul import generate_heart_soul


def test_trigger_matches():
    assert BrennerSkill.trigger_matches("please brenner:deepreason about X")
    assert not BrennerSkill.trigger_matches("no trigger here")


def test_brenner_execute_simulated(tmp_path):
    skill = BrennerSkill()
    res = skill.execute("brenner:deepreason analyze the repo")
    assert isinstance(res, dict)
    assert "reply" in res or "error" not in res


def test_generate_heart_soul(tmp_path):
    out = generate_heart_soul(str(tmp_path))
    assert os.path.exists(out["heart"]) and os.path.exists(out["soul"])
    with open(out["heart"]) as f:
        h = json.load(f)
    assert h.get("name") == "Brenner Bot"
