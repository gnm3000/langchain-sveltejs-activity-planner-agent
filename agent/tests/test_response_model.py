from interfaces import ResponseActivityModel


def test_response_activity_model_defaults() -> None:
    model = ResponseActivityModel(city="Madrid")
    assert model.city == "Madrid"
    assert model.greeting is None
    assert model.plan is None
    assert model.error is None
