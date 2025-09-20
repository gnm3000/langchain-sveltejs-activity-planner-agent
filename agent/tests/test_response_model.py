from interfaces import ResponseActivityModel


def test_response_activity_model_defaults() -> None:
    model = ResponseActivityModel(city="Berlin", plan="Test plan")
    assert model.city == "Berlin"
    assert model.plan == "Test plan"
    assert model.error is None
