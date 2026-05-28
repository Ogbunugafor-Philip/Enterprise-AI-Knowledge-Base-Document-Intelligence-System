from datetime import datetime, timedelta, timezone

from app.core.security import (
    check_password_history,
    create_access_token,
    decode_access_token,
    generate_otp_code,
    hash_password,
    is_otp_expired,
    validate_password_strength,
    verify_password,
)


def test_password_hashing_and_verification():
    password = "StrongPass1!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPass1!", hashed)


def test_jwt_token_creation_and_decoding():
    token = create_access_token(
        {
            "sub": "11111111-1111-1111-1111-111111111111",
            "organization_id": "22222222-2222-2222-2222-222222222222",
            "email": "user@example.com",
            "role": "admin",
        }
    )
    payload = decode_access_token(token)

    assert payload["sub"] == "11111111-1111-1111-1111-111111111111"
    assert payload["organization_id"] == "22222222-2222-2222-2222-222222222222"
    assert payload["email"] == "user@example.com"
    assert payload["role"] == "admin"


def test_password_strength_validation_accepts_strong_passwords():
    valid, errors = validate_password_strength("StrongPass1!")

    assert valid
    assert errors == []


def test_password_strength_validation_rejects_weak_passwords():
    valid, errors = validate_password_strength("weak")

    assert not valid
    assert "Password must be at least 8 characters long" in errors
    assert "Password must contain at least 1 uppercase letter" in errors
    assert "Password must contain at least 1 number" in errors
    assert "Password must contain at least 1 special character" in errors


def test_otp_generation_produces_six_digit_codes():
    otp = generate_otp_code()

    assert len(otp) == 6
    assert otp.isdigit()


def test_otp_expiry_check():
    assert is_otp_expired(datetime.now(timezone.utc) - timedelta(seconds=1))
    assert not is_otp_expired(datetime.now(timezone.utc) + timedelta(minutes=10))


def test_password_history_check_blocks_reused_passwords():
    old_password = "OldStrong1!"
    history = [
        hash_password("OtherStrong1!"),
        hash_password(old_password),
        hash_password("AnotherStrong1!"),
    ]

    assert check_password_history(old_password, history)
    assert not check_password_history("BrandNewStrong1!", history)
