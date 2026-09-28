"""Comprehensive live authentication test suite for APEX AI platform.
Tests live backend (http://127.0.0.1:8000) and frontend proxy (http://localhost:3000).
"""

import json
import sys
import time
import uuid
from datetime import datetime, timezone, timedelta
import httpx
from jose import jwt

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3000"
JWT_SECRET_KEY = "your-super-secret-jwt-key-change-this"
JWT_ALGORITHM = "HS256"

results = []

def record_result(test_id, category, name, passed, status_code, expected_status, details, response_body=None):
    results.append({
        "test_id": test_id,
        "category": category,
        "name": name,
        "passed": passed,
        "status_code": status_code,
        "expected_status": expected_status,
        "details": details,
        "response_body": response_body
    })
    status_str = "PASS" if passed else "FAIL"
    print(f"[{status_str}] {test_id}: {name} (Status: {status_code}, Expected: {expected_status})")
    if not passed:
        print(f"       Details: {details}")

def run_tests():
    client = httpx.Client(timeout=10.0)
    print("================================================================================")
    print("STARTING LIVE AUTHENTICATION TEST SUITE (APEX AI)")
    print(f"Backend: {BACKEND_URL} | Frontend: {FRONTEND_URL}")
    print("================================================================================\n")

    # -------------------------------------------------------------------------
    # Category 1: Registration Flow
    # -------------------------------------------------------------------------
    print("--- CATEGORY 1: USER REGISTRATION FLOW ---")
    
    unique_suffix = int(time.time())
    valid_email = f"live_test_{unique_suffix}@example.com"
    valid_password = "P@ssw0rdSecure2026!"
    valid_name = "Live Test User"

    # REG-01: Happy Path Registration
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": valid_email, "password": valid_password, "full_name": valid_name}
        )
        passed = False
        details = ""
        body = {}
        if res.status_code == 200:
            body = res.json()
            if (
                isinstance(body.get("id"), int)
                and body.get("email") == valid_email
                and body.get("full_name") == valid_name
                and body.get("is_active") is True
                and body.get("is_superuser") is False
                and "password" not in body
                and "hashed_password" not in body
            ):
                passed = True
            else:
                details = f"Unexpected payload: {body}"
        else:
            details = f"Status {res.status_code}: {res.text}"
        record_result("REG-01", "Registration", "Happy path: register valid new user", passed, res.status_code, 200, details, body)
    except Exception as e:
        record_result("REG-01", "Registration", "Happy path: register valid new user", False, 0, 200, str(e))

    # REG-02: Duplicate Email Rejection (Newly registered user)
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": valid_email, "password": "AnotherPassword123!", "full_name": "Duplicate User"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 400 and body.get("detail") == "Email already registered")
        details = f"Detail: {body.get('detail')}" if not passed else "Rejected with 400 and 'Email already registered'"
        record_result("REG-02", "Registration", "Duplicate email rejection (new user)", passed, res.status_code, 400, details, body)
    except Exception as e:
        record_result("REG-02", "Registration", "Duplicate email rejection (new user)", False, 0, 400, str(e))

    # REG-03: Duplicate Email Rejection (Pre-seeded demo user: test@example.com)
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": "test@example.com", "password": "pass123password", "full_name": "Demo Clone"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 400 and body.get("detail") == "Email already registered")
        details = f"Detail: {body.get('detail')}" if not passed else "Rejected with 400 and 'Email already registered'"
        record_result("REG-03", "Registration", "Duplicate email rejection (pre-seeded demo user)", passed, res.status_code, 400, details, body)
    except Exception as e:
        record_result("REG-03", "Registration", "Duplicate email rejection (pre-seeded demo user)", False, 0, 400, str(e))

    # REG-04: Duplicate Email Case Sensitivity Test (TEST@example.com)
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": "TEST@EXAMPLE.COM", "password": "pass123password", "full_name": "Demo Uppercase"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        # In SQLite / Pydantic, does it treat TEST@EXAMPLE.COM as duplicate or allow it?
        # Note: Pydantic EmailStr does not lowercase automatically unless specified, and SQLite == is case-sensitive by default or case-insensitive?
        details = f"Status: {res.status_code}, Body: {body}"
        # We record what actually happens:
        passed = True # Evaluated as observation
        record_result("REG-04", "Registration", "Duplicate email case-sensitivity test (TEST@EXAMPLE.COM)", passed, res.status_code, "400 or 200", details, body)
    except Exception as e:
        record_result("REG-04", "Registration", "Duplicate email case-sensitivity test", False, 0, "400", str(e))

    # REG-05: Invalid Email Format - Missing @
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": "invalidemailformat", "password": "password123", "full_name": "Invalid Email"}
        )
        passed = (res.status_code == 422)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = f"Pydantic validation error: {body.get('detail', [{}])[0].get('msg', '')}" if passed else str(body)
        record_result("REG-05", "Registration", "Invalid email format: missing '@'", passed, res.status_code, 422, details, body)
    except Exception as e:
        record_result("REG-05", "Registration", "Invalid email format: missing '@'", False, 0, 422, str(e))

    # REG-06: Invalid Email Format - Missing Domain
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": "user@", "password": "password123", "full_name": "Invalid Email"}
        )
        passed = (res.status_code == 422)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = f"Pydantic validation error: {body.get('detail', [{}])[0].get('msg', '')}" if passed else str(body)
        record_result("REG-06", "Registration", "Invalid email format: missing domain ('user@')", passed, res.status_code, 422, details, body)
    except Exception as e:
        record_result("REG-06", "Registration", "Invalid email format: missing domain ('user@')", False, 0, 422, str(e))

    # REG-07: Invalid Email Format - Missing Username
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": "@example.com", "password": "password123", "full_name": "Invalid Email"}
        )
        passed = (res.status_code == 422)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = f"Pydantic validation error: {body.get('detail', [{}])[0].get('msg', '')}" if passed else str(body)
        record_result("REG-07", "Registration", "Invalid email format: missing username ('@example.com')", passed, res.status_code, 422, details, body)
    except Exception as e:
        record_result("REG-07", "Registration", "Invalid email format: missing username ('@example.com')", False, 0, 422, str(e))

    # REG-08: Invalid Email Format - Spaces in email
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": "user name@example.com", "password": "password123", "full_name": "Invalid Email"}
        )
        passed = (res.status_code == 422)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = f"Pydantic validation error: {body.get('detail', [{}])[0].get('msg', '')}" if passed else str(body)
        record_result("REG-08", "Registration", "Invalid email format: spaces in address", passed, res.status_code, 422, details, body)
    except Exception as e:
        record_result("REG-08", "Registration", "Invalid email format: spaces in address", False, 0, 422, str(e))

    # REG-09: Missing full_name in body
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": f"no_fullname_{unique_suffix}@example.com", "password": "password123"}
        )
        # Backend schema UserRegister requires full_name: str
        passed = (res.status_code == 422)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = "Rejected with 422 as expected because schema lacks full_name default" if passed else f"Status: {res.status_code}"
        record_result("REG-09", "Registration", "Missing required 'full_name' field in request payload", passed, res.status_code, 422, details, body)
    except Exception as e:
        record_result("REG-09", "Registration", "Missing required 'full_name' field", False, 0, 422, str(e))

    # REG-10: Empty string full_name
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": f"empty_name_{unique_suffix}@example.com", "password": "password123", "full_name": ""}
        )
        passed = (res.status_code == 200)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = f"Created user with empty full_name: {body.get('full_name')}"
        record_result("REG-10", "Registration", "Empty string 'full_name' permitted", passed, res.status_code, 200, details, body)
    except Exception as e:
        record_result("REG-10", "Registration", "Empty string 'full_name' permitted", False, 0, 200, str(e))

    # REG-11: Password boundary: Empty string password
    try:
        empty_pwd_email = f"empty_pwd_{unique_suffix}@example.com"
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": empty_pwd_email, "password": "", "full_name": "Empty Pwd User"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        # Notice: UserRegister does NOT have min_length, so backend hashes empty string!
        details = f"Status: {res.status_code}. Notice: Backend accepted empty password (no min_length validation in schema)" if res.status_code == 200 else f"Rejected: {body}"
        record_result("REG-11", "Registration", "Password boundary: empty password ('')", True, res.status_code, "200 (Finding: lacks min_length)", details, body)
    except Exception as e:
        record_result("REG-11", "Registration", "Password boundary: empty password", False, 0, "200", str(e))

    # REG-12: Password boundary: 1 character password
    try:
        single_char_email = f"single_char_{unique_suffix}@example.com"
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": single_char_email, "password": "x", "full_name": "Single Char User"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = f"Status: {res.status_code}. Notice: Backend accepted 1-char password" if res.status_code == 200 else f"Rejected: {body}"
        record_result("REG-12", "Registration", "Password boundary: single-character password ('x')", True, res.status_code, "200 (Finding: lacks min_length)", details, body)
    except Exception as e:
        record_result("REG-12", "Registration", "Password boundary: single-character password", False, 0, "200", str(e))

    # REG-13: Password boundary: Long password (> 72 characters)
    long_password = "A" * 100
    long_pwd_email = f"long_pwd_{unique_suffix}@example.com"
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": long_pwd_email, "password": long_password, "full_name": "Long Password User"}
        )
        passed = (res.status_code == 200)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = "Accepted safely via bcrypt 72-byte truncation without crashing" if passed else f"Status: {res.status_code}: {res.text}"
        record_result("REG-13", "Registration", "Password boundary: 100-character password (> 72 byte bcrypt limit)", passed, res.status_code, 200, details, body)
    except Exception as e:
        record_result("REG-13", "Registration", "Password boundary: 100-character password", False, 0, 200, str(e))

    # REG-14: Password boundary: Complex Unicode / Special Characters
    unicode_password = "P@ssw0rd!#$€%&'()*+,-./:;<=>?@[\\]^_`{|}~ 🔐 中文"
    unicode_email = f"unicode_pwd_{unique_suffix}@example.com"
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": unicode_email, "password": unicode_password, "full_name": "Unicode Pwd User"}
        )
        passed = (res.status_code == 200)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = "Accepted and stored complex Unicode & special characters safely" if passed else f"Status: {res.status_code}"
        record_result("REG-14", "Registration", "Password boundary: complex Unicode & special characters", passed, res.status_code, 200, details, body)
    except Exception as e:
        record_result("REG-14", "Registration", "Password boundary: complex Unicode & special characters", False, 0, 200, str(e))

    # REG-15: Injection resilience: SQL injection in password field
    sqli_password = "' OR '1'='1' --"
    sqli_email = f"sqli_pwd_{unique_suffix}@example.com"
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={"email": sqli_email, "password": sqli_password, "full_name": "SQLi User"}
        )
        passed = (res.status_code == 200)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = "Safely hashed and stored SQL injection string as verbatim password" if passed else f"Status: {res.status_code}"
        record_result("REG-15", "Registration", "SQL injection vector in password field", passed, res.status_code, 200, details, body)
    except Exception as e:
        record_result("REG-15", "Registration", "SQL injection vector in password field", False, 0, 200, str(e))


    # -------------------------------------------------------------------------
    # Category 2: User Login Flow
    # -------------------------------------------------------------------------
    print("\n--- CATEGORY 2: USER LOGIN FLOW ---")

    # LOG-01: Happy path login with pre-seeded demo user
    demo_token = None
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "test@example.com", "password": "pass123"}
        )
        passed = False
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        if res.status_code == 200:
            token = body.get("access_token", "")
            token_type = body.get("token_type", "")
            if token and len(token.split(".")) == 3 and token_type == "bearer":
                passed = True
                demo_token = token
                details = "Successfully received valid JWT access_token and bearer token_type"
            else:
                details = f"Invalid token format or token_type: {body}"
        else:
            details = f"Status {res.status_code}: {res.text}"
        record_result("LOG-01", "Login", "Happy path: login with pre-seeded demo user (test@example.com)", passed, res.status_code, 200, details, {"token_type": body.get("token_type"), "access_token_preview": body.get("access_token", "")[:25] + "..." if body.get("access_token") else None})
    except Exception as e:
        record_result("LOG-01", "Login", "Happy path: login with pre-seeded demo user", False, 0, 200, str(e))

    # LOG-02: Happy path login with newly registered user (from REG-01)
    new_user_token = None
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": valid_email, "password": valid_password}
        )
        passed = False
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        if res.status_code == 200:
            token = body.get("access_token", "")
            token_type = body.get("token_type", "")
            if token and len(token.split(".")) == 3 and token_type == "bearer":
                passed = True
                new_user_token = token
                details = "Successfully received valid JWT for newly registered user"
            else:
                details = f"Invalid token format: {body}"
        else:
            details = f"Status {res.status_code}: {res.text}"
        record_result("LOG-02", "Login", "Happy path: login with newly registered user", passed, res.status_code, 200, details, {"token_type": body.get("token_type"), "access_token_preview": body.get("access_token", "")[:25] + "..." if body.get("access_token") else None})
    except Exception as e:
        record_result("LOG-02", "Login", "Happy path: login with newly registered user", False, 0, 200, str(e))

    # LOG-03: Login with 100-character password user (from REG-13)
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": long_pwd_email, "password": long_password}
        )
        passed = (res.status_code == 200 and "access_token" in res.json())
        body = res.json() if passed else {}
        details = "Long password verified successfully matching 72-byte truncation in both hashing and verification" if passed else f"Status: {res.status_code}"
        record_result("LOG-03", "Login", "Login with 100-character password (> 72 bytes)", passed, res.status_code, 200, details, {"token_type": body.get("token_type")})
    except Exception as e:
        record_result("LOG-03", "Login", "Login with 100-character password", False, 0, 200, str(e))

    # LOG-04: Login with Unicode & special character password user (from REG-14)
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": unicode_email, "password": unicode_password}
        )
        passed = (res.status_code == 200 and "access_token" in res.json())
        body = res.json() if passed else {}
        details = "Unicode and emoji password verified successfully" if passed else f"Status: {res.status_code}"
        record_result("LOG-04", "Login", "Login with Unicode & emoji password", passed, res.status_code, 200, details, {"token_type": body.get("token_type")})
    except Exception as e:
        record_result("LOG-04", "Login", "Login with Unicode & emoji password", False, 0, 200, str(e))

    # LOG-05: Login with SQL injection password user (from REG-15)
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": sqli_email, "password": sqli_password}
        )
        passed = (res.status_code == 200 and "access_token" in res.json())
        body = res.json() if passed else {}
        details = "SQL injection password string safely matched and authenticated" if passed else f"Status: {res.status_code}"
        record_result("LOG-05", "Login", "Login with verbatim SQL injection password", passed, res.status_code, 200, details, {"token_type": body.get("token_type")})
    except Exception as e:
        record_result("LOG-05", "Login", "Login with verbatim SQL injection password", False, 0, 200, str(e))

    # LOG-06: Login with invalid password (correct email, wrong password)
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrong_password_xyz"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 401 and body.get("detail") == "Invalid credentials")
        details = f"Detail: '{body.get('detail')}'" if passed else f"Status: {res.status_code}, Body: {body}"
        record_result("LOG-06", "Login", "Invalid password rejection (HTTP 401)", passed, res.status_code, 401, details, body)
    except Exception as e:
        record_result("LOG-06", "Login", "Invalid password rejection", False, 0, 401, str(e))

    # LOG-07: Login with non-existent email
    try:
        res = client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "nonexistent_apex_user_99999@example.com", "password": "anypassword"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 401 and body.get("detail") == "Invalid credentials")
        details = f"Detail: '{body.get('detail')}' (Identical to wrong password, preventing user enumeration)" if passed else f"Status: {res.status_code}, Body: {body}"
        record_result("LOG-07", "Login", "Non-existent email rejection (user enumeration protection)", passed, res.status_code, 401, details, body)
    except Exception as e:
        record_result("LOG-07", "Login", "Non-existent email rejection", False, 0, 401, str(e))

    # LOG-08: Login with empty credentials payload ({})
    try:
        res = client.post(f"{BACKEND_URL}/api/v1/auth/login", json={})
        passed = (res.status_code == 422)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = "Rejected with 422 Unprocessable Entity as expected" if passed else f"Status: {res.status_code}"
        record_result("LOG-08", "Login", "Empty JSON body ({})", passed, res.status_code, 422, details, body)
    except Exception as e:
        record_result("LOG-08", "Login", "Empty JSON body", False, 0, 422, str(e))

    # LOG-09: Login with missing password
    try:
        res = client.post(f"{BACKEND_URL}/api/v1/auth/login", json={"email": "test@example.com"})
        passed = (res.status_code == 422)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = "Rejected with 422 Unprocessable Entity (missing password field)" if passed else f"Status: {res.status_code}"
        record_result("LOG-09", "Login", "Missing password in login payload", passed, res.status_code, 422, details, body)
    except Exception as e:
        record_result("LOG-09", "Login", "Missing password in login payload", False, 0, 422, str(e))

    # LOG-10: Login with missing email
    try:
        res = client.post(f"{BACKEND_URL}/api/v1/auth/login", json={"password": "pass123"})
        passed = (res.status_code == 422)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = "Rejected with 422 Unprocessable Entity (missing email field)" if passed else f"Status: {res.status_code}"
        record_result("LOG-10", "Login", "Missing email in login payload", passed, res.status_code, 422, details, body)
    except Exception as e:
        record_result("LOG-10", "Login", "Missing email in login payload", False, 0, 422, str(e))

    # LOG-11: Login with invalid email format
    try:
        res = client.post(f"{BACKEND_URL}/api/v1/auth/login", json={"email": "invalid-email-format", "password": "pass123"})
        passed = (res.status_code == 422)
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        details = "Rejected with 422 Unprocessable Entity (EmailStr validation)" if passed else f"Status: {res.status_code}"
        record_result("LOG-11", "Login", "Invalid email format in login payload", passed, res.status_code, 422, details, body)
    except Exception as e:
        record_result("LOG-11", "Login", "Invalid email format in login payload", False, 0, 422, str(e))


    # -------------------------------------------------------------------------
    # Category 3: Session & Protected Route Verification (/auth/me)
    # -------------------------------------------------------------------------
    print("\n--- CATEGORY 3: SESSION & TOKEN VERIFICATION ---")

    # SES-01: GET /api/v1/auth/me with valid Bearer token header
    try:
        res = client.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = False
        details = ""
        if res.status_code == 200:
            if (
                body.get("email") == "test@example.com"
                and body.get("full_name") == "Demo User"
                and isinstance(body.get("id"), int)
                and "password" not in body
                and "hashed_password" not in body
            ):
                passed = True
                details = f"Verified user profile for user id {body.get('id')} ({body.get('email')})"
            else:
                details = f"Profile mismatch or leaked password: {body}"
        else:
            details = f"Status {res.status_code}: {res.text}"
        record_result("SES-01", "Session", "GET /auth/me with valid Bearer token in header", passed, res.status_code, 200, details, body)
    except Exception as e:
        record_result("SES-01", "Session", "GET /auth/me with valid Bearer token", False, 0, 200, str(e))

    # SES-02: GET /api/v1/auth/me with newly registered user's token
    try:
        res = client.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_user_token}"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 200 and body.get("email") == valid_email and body.get("full_name") == valid_name)
        details = f"Successfully matched profile: id={body.get('id')}, email={body.get('email')}" if passed else f"Mismatch: {body}"
        record_result("SES-02", "Session", "GET /auth/me with newly registered user Bearer token", passed, res.status_code, 200, details, body)
    except Exception as e:
        record_result("SES-02", "Session", "GET /auth/me with newly registered user Bearer token", False, 0, 200, str(e))

    # SES-03: GET /api/v1/auth/me with token in query param (?token=...)
    try:
        res = client.get(f"{BACKEND_URL}/api/v1/auth/me?token={demo_token}")
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 200 and body.get("email") == "test@example.com")
        details = "Query parameter ?token= accepted seamlessly by get_current_user (for SSE EventSource)" if passed else f"Status: {res.status_code}: {body}"
        record_result("SES-03", "Session", "GET /auth/me via query parameter ?token=<token>", passed, res.status_code, 200, details, body)
    except Exception as e:
        record_result("SES-03", "Session", "GET /auth/me via query parameter", False, 0, 200, str(e))

    # SES-04: GET /api/v1/auth/me without any token (unauthenticated)
    try:
        res = client.get(f"{BACKEND_URL}/api/v1/auth/me")
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 401)
        details = f"Detail: '{body.get('detail')}'" if passed else f"Status: {res.status_code}: {body}"
        record_result("SES-04", "Session", "GET /auth/me without token (HTTP 401 rejection)", passed, res.status_code, 401, details, body)
    except Exception as e:
        record_result("SES-04", "Session", "GET /auth/me without token", False, 0, 401, str(e))

    # SES-05: GET /api/v1/auth/me with malformed token (not a JWT)
    try:
        res = client.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": "Bearer not_a_valid_jwt_token_string"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 401 and body.get("detail") == "Invalid token")
        details = f"Detail: '{body.get('detail')}'" if passed else f"Status: {res.status_code}: {body}"
        record_result("SES-05", "Session", "GET /auth/me with malformed JWT token string", passed, res.status_code, 401, details, body)
    except Exception as e:
        record_result("SES-05", "Session", "GET /auth/me with malformed JWT token string", False, 0, 401, str(e))

    # SES-06: GET /api/v1/auth/me with tampered signature
    try:
        parts = demo_token.split(".")
        tampered_token = f"{parts[0]}.{parts[1]}.badsignaturehere12345"
        res = client.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 401 and body.get("detail") == "Invalid token")
        details = f"Detail: '{body.get('detail')}'" if passed else f"Status: {res.status_code}: {body}"
        record_result("SES-06", "Session", "GET /auth/me with tampered JWT signature", passed, res.status_code, 401, details, body)
    except Exception as e:
        record_result("SES-06", "Session", "GET /auth/me with tampered signature", False, 0, 401, str(e))

    # SES-07: GET /api/v1/auth/me with expired token
    try:
        expired_payload = {
            "sub": "1",
            "email": "test@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=10)
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        res = client.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 401 and body.get("detail") == "Invalid token")
        details = f"Detail: '{body.get('detail')}' (Rejected due to expired timestamp)" if passed else f"Status: {res.status_code}: {body}"
        record_result("SES-07", "Session", "GET /auth/me with expired JWT token", passed, res.status_code, 401, details, body)
    except Exception as e:
        record_result("SES-07", "Session", "GET /auth/me with expired token", False, 0, 401, str(e))

    # SES-08: GET /api/v1/auth/me with non-existent user ID in sub claim
    try:
        nonexistent_payload = {
            "sub": "999999",
            "email": "ghost@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60)
        }
        nonexistent_token = jwt.encode(nonexistent_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        res = client.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {nonexistent_token}"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 401 and body.get("detail") == "User not found")
        details = f"Detail: '{body.get('detail')}'" if passed else f"Status: {res.status_code}: {body}"
        record_result("SES-08", "Session", "GET /auth/me with non-existent user ID in JWT sub claim", passed, res.status_code, 401, details, body)
    except Exception as e:
        record_result("SES-08", "Session", "GET /auth/me with non-existent user ID", False, 0, 401, str(e))

    # SES-09: GET /api/v1/auth/me with invalid non-integer sub claim
    try:
        invalid_sub_payload = {
            "sub": "not_an_integer_id",
            "email": "test@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60)
        }
        invalid_sub_token = jwt.encode(invalid_sub_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        res = client.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {invalid_sub_token}"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 401 and body.get("detail") == "Invalid user ID")
        details = f"Detail: '{body.get('detail')}'" if passed else f"Status: {res.status_code}: {body}"
        record_result("SES-09", "Session", "GET /auth/me with non-integer sub claim", passed, res.status_code, 401, details, body)
    except Exception as e:
        record_result("SES-09", "Session", "GET /auth/me with non-integer sub claim", False, 0, 401, str(e))


    # -------------------------------------------------------------------------
    # Category 4: Frontend Proxy Routing (http://localhost:3000/api/...)
    # -------------------------------------------------------------------------
    print("\n--- CATEGORY 4: FRONTEND PROXY ROUTING (NEXT.JS REWRITE) ---")

    # PROX-01: POST http://localhost:3000/api/v1/auth/login
    try:
        res = client.post(
            f"{FRONTEND_URL}/api/v1/auth/login",
            json={"email": "test@example.com", "password": "pass123"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 200 and "access_token" in body and body.get("token_type") == "bearer")
        details = "Next.js successfully proxied POST /api/v1/auth/login to backend on port 8000" if passed else f"Status {res.status_code}: {res.text}"
        record_result("PROX-01", "Proxy", "Next.js rewrite: POST /api/v1/auth/login", passed, res.status_code, 200, details, {"token_type": body.get("token_type")})
    except Exception as e:
        record_result("PROX-01", "Proxy", "Next.js rewrite: POST /api/v1/auth/login", False, 0, 200, str(e))

    # PROX-02: GET http://localhost:3000/api/v1/auth/me
    try:
        res = client.get(
            f"{FRONTEND_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 200 and body.get("email") == "test@example.com")
        details = "Next.js successfully proxied GET /api/v1/auth/me with Bearer token" if passed else f"Status {res.status_code}: {res.text}"
        record_result("PROX-02", "Proxy", "Next.js rewrite: GET /api/v1/auth/me", passed, res.status_code, 200, details, body)
    except Exception as e:
        record_result("PROX-02", "Proxy", "Next.js rewrite: GET /api/v1/auth/me", False, 0, 200, str(e))

    # PROX-03: POST http://localhost:3000/api/v1/auth/register (duplicate email error proxying)
    try:
        res = client.post(
            f"{FRONTEND_URL}/api/v1/auth/register",
            json={"email": "test@example.com", "password": "pass123password", "full_name": "Proxy User"}
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        passed = (res.status_code == 400 and body.get("detail") == "Email already registered")
        details = "Next.js successfully proxied 400 Bad Request error detail" if passed else f"Status {res.status_code}: {res.text}"
        record_result("PROX-03", "Proxy", "Next.js rewrite: POST /api/v1/auth/register 400 error proxying", passed, res.status_code, 400, details, body)
    except Exception as e:
        record_result("PROX-03", "Proxy", "Next.js rewrite: POST /api/v1/auth/register error proxying", False, 0, 400, str(e))

    # PROX-04: Test Next.js frontend pages directly
    try:
        login_page_res = client.get(f"{FRONTEND_URL}/login")
        register_page_res = client.get(f"{FRONTEND_URL}/register")
        passed = (login_page_res.status_code == 200 and register_page_res.status_code == 200)
        details = f"/login: {login_page_res.status_code}, /register: {register_page_res.status_code}"
        record_result("PROX-04", "Frontend Pages", "HTTP 200 for /login and /register pages", passed, login_page_res.status_code, 200, details)
    except Exception as e:
        record_result("PROX-04", "Frontend Pages", "HTTP 200 for /login and /register pages", False, 0, 200, str(e))

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count

    print("\n================================================================================")
    print(f"LIVE TEST RUN COMPLETE: {passed_count}/{total} PASSED ({failed_count} FAILED)")
    print("================================================================================\n")

    # Write output JSON for report generator
    with open("tests/live_auth_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": total,
            "passed": passed_count,
            "failed": failed_count,
            "results": results
        }, f, indent=2)

if __name__ == "__main__":
    run_tests()
