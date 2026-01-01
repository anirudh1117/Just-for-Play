from mlapp.testing.fake_data_loader import FakeBacktestDataLoader


def test_fake_data_loader():
    loader = FakeBacktestDataLoader(
        symbol="TATAMOTORS",
        start_date="2023-01-01",
        end_date="2023-01-03"
    )

    data = loader.run()

    assert len(data.keys()) == 3
    first = list(data.values())[0]
    assert "open" in first.columns
