import requests

import internship_watch as watch


def test_fetch_company_retries_connection_errors(monkeypatch):
    calls = 0
    delays = []

    def fetcher(slug, company):
        nonlocal calls
        calls += 1
        if calls < 3:
            raise requests.exceptions.ConnectionError("connection reset")
        return [{"id": "job-1"}]

    monkeypatch.setitem(watch.BOARD_FETCHERS, "test-board", fetcher)
    monkeypatch.setattr(watch.time, "sleep", delays.append)

    company, jobs, error = watch.fetch_company(
        {"board": "test-board", "slug": "test", "name": "Test Company"}
    )

    assert company == "Test Company"
    assert jobs == [{"id": "job-1"}]
    assert error == ""
    assert calls == 3
    assert delays == [2.0, 3.0]
