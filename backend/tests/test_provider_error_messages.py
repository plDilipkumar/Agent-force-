from app.provider_errors import provider_error_detail


def test_authentication_error_is_actionable():
    message = provider_error_detail(401, "UNAUTHENTICATED")
    assert "authentication failed" in message.lower()
    assert "valid, active" in message.lower()


def test_model_not_found_points_to_model_setting():
    message = provider_error_detail(404, "NOT_FOUND")
    assert "model" in message.lower()
    assert "available" in message.lower()
