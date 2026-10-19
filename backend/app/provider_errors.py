"""Actionable, non-secret diagnostics for Gemini provider errors."""


def provider_error_detail(status_code: int, provider_code: str) -> str:
    """Explain the likely fix without echoing provider response bodies or secrets."""
    if status_code == 401:
        return (
            "Gemini authentication failed (HTTP 401). Check that GEMINI_API_KEY "
            "is valid, active, and from the intended Google AI Studio project."
        )
    if status_code == 403:
        return (
            "Gemini access was denied (HTTP 403). Check API enablement, key "
            "restrictions, and Google project permissions."
        )
    if status_code == 404:
        return (
            "Gemini model or endpoint was not found (HTTP 404). Check GEMINI_MODEL "
            "and confirm the model is available to this API key."
        )
    if status_code == 429:
        return (
            "Gemini quota or rate limit reached (HTTP 429). Check usage limits "
            "and retry after the quota window resets."
        )
    if status_code >= 500:
        return (
            f"Gemini provider is temporarily unavailable (HTTP {status_code}, "
            f"{provider_code}). Retry later."
        )
    return (
        f"Gemini rejected the request (HTTP {status_code}, {provider_code}). "
        "Check the model and request format."
    )
