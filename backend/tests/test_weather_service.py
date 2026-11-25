from app.services.weather_service import _extract_weather


def test_extracts_weather_from_met_no_payload():
    payload = {
        "properties": {
            "meta": {
                "updated_at": "2026-11-24T12:00:00Z",
            },
            "timeseries": [
                {
                    "time": "2099-11-24T15:00:00Z",
                    "data": {
                        "instant": {
                            "details": {
                                "air_temperature": 28.5,
                                "wind_speed": 4.2,
                            }
                        },
                        "next_1_hours": {
                            "summary": {
                                "symbol_code": "rain",
                            },
                            "details": {
                                "precipitation_amount": 2.5,
                                "probability_of_precipitation": 70,
                            },
                        },
                    },
                }
            ],
        }
    }

    result = _extract_weather(
        payload=payload,
        is_stale=False,
    )

    assert result.temperature == 28.5
    assert result.wind_speed == 4.2
    assert result.precipitation_amount == 2.5
    assert result.precipitation_probability == 70
    assert result.symbol_code == "rain"
    assert result.is_stale is False


def test_marks_cached_forecast_as_stale():
    payload = {
        "properties": {
            "meta": {},
            "timeseries": [
                {
                    "time": "2099-11-24T15:00:00Z",
                    "data": {
                        "instant": {
                            "details": {
                                "air_temperature": 22,
                            }
                        }
                    },
                }
            ],
        }
    }

    result = _extract_weather(
        payload=payload,
        is_stale=True,
    )

    assert result.is_stale is True
    assert result.temperature == 22


def test_rejects_empty_forecast():
    payload = {
        "properties": {
            "meta": {},
            "timeseries": [],
        }
    }

    import pytest

    with pytest.raises(ValueError):
        _extract_weather(
            payload=payload,
            is_stale=False,
        )
