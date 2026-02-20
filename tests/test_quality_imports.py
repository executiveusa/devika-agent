import asyncio

from src.synthia.quality import check_quality


def test_check_quality_imports_do_not_crash():
    report = asyncio.run(check_quality("http://example.com", context={"test_coverage": 85.0}))
    assert report is not None
    assert hasattr(report, "scores")
