from tests.fixtures.harness import load_fixture_cases


def test_fixture_pairs_complete():
    cases = load_fixture_cases()
    assert cases
