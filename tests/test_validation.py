from app.validation import validate_lead


def test_valid_lead_passes():
    is_valid, errors, data = validate_lead({
        "first_name": "Anna", "last_name": "Becker", "company": "Nordstern GmbH",
        "email": "Anna.Becker@Example.COM", "message": "We need help automating our lead intake.",
    })
    assert is_valid
    assert errors == []
    assert data["email"] == "anna.becker@example.com"  # normalized to lowercase


def test_missing_email_fails():
    is_valid, errors, _ = validate_lead({"first_name": "Anna", "message": "Please contact me about automation."})
    assert not is_valid
    assert any("Email is required" in e for e in errors)


def test_invalid_email_format_fails():
    is_valid, errors, _ = validate_lead({
        "first_name": "Anna", "email": "anna[at]example", "message": "Please contact me about automation.",
    })
    assert not is_valid
    assert any("not valid" in e for e in errors)


def test_empty_message_fails():
    is_valid, errors, _ = validate_lead({"first_name": "Anna", "email": "anna@example.com", "message": ""})
    assert not is_valid
    assert any("Message is required" in e for e in errors)


def test_too_short_message_fails():
    is_valid, errors, _ = validate_lead({"first_name": "Anna", "email": "anna@example.com", "message": "hi"})
    assert not is_valid
    assert any("too short" in e for e in errors)


def test_missing_identity_fails():
    is_valid, errors, _ = validate_lead({"email": "anna@example.com", "message": "Please contact me soon."})
    assert not is_valid
    assert any("name or a company" in e for e in errors)


def test_garbage_phone_fails():
    is_valid, errors, _ = validate_lead({
        "first_name": "Anna", "email": "anna@example.com", "message": "Please contact me about automation.",
        "phone": "abc",
    })
    assert not is_valid
    assert any("Phone number looks invalid" in e for e in errors)
