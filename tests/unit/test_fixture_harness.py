from tests.fixtures.harness import load_fixture_cases


def test_fixture_pairs_complete():
    cases = load_fixture_cases()
    assert cases


def test_fixture_loader_excludes_errors_when_requested():
    cases = load_fixture_cases(include_errors=False)
    assert cases
    assert all(not case.case_id.startswith("errors/") for case in cases)
