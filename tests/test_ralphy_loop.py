from src.synthia.ralphy_loop import RalphyLoop


def test_ralphy_loop_integration_priority():
    loop = RalphyLoop()
    decision = loop.classify({"task": "integrate agent mail and beads sync"})
    assert decision.priority == "integration"


def test_ralphy_loop_default_priority():
    loop = RalphyLoop()
    decision = loop.classify({"task": "write unit tests"})
    assert decision.priority in {"standard", "integration", "architectural", "unknown", "polish"}
