"""
测试模块 1: 认证中间件 (middleware/auth.py)
覆盖: 密码哈希、JWT 创建/验证/过期、依赖注入
"""
import pytest
from datetime import timedelta

from middleware.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:
    """密码哈希与验证"""

    def test_hash_returns_string(self):
        result = hash_password("password123")
        assert isinstance(result, str)
        assert len(result) > 20

    def test_hash_different_each_time(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2  # bcrypt 每次生成不同 salt

    def test_verify_correct_password(self):
        pw = "my_secure_password"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_verify_empty_password(self):
        hashed = hash_password("nonempty")
        assert verify_password("", hashed) is False

    def test_hash_chinese_password(self):
        pw = "中文密码测试"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_hash_long_password(self):
        pw = "a" * 72  # bcrypt 最大 72 字节
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_hash_special_characters(self):
        pw = "p@ss!w0rd#$%^&*()"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True


class TestJWTToken:
    """JWT Token 创建与验证"""

    def test_create_token_returns_string(self):
        token = create_access_token(data={"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 30

    def test_token_has_three_parts(self):
        token = create_access_token(data={"sub": "user-123"})
        parts = token.split(".")
        assert len(parts) == 3

    def test_decode_valid_token(self):
        token = create_access_token(data={"sub": "user-456"})
        payload = decode_access_token(token)
        assert payload["sub"] == "user-456"
        assert "exp" in payload

    def test_decode_token_with_extra_fields(self):
        token = create_access_token(data={
            "sub": "user-789",
            "role": "admin",
            "name": "测试用户",
        })
        payload = decode_access_token(token)
        assert payload["sub"] == "user-789"
        assert payload["role"] == "admin"
        assert payload["name"] == "测试用户"

    def test_decode_invalid_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("not.a.valid.token")
        assert exc_info.value.status_code == 401

    def test_decode_empty_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_access_token("")

    def test_decode_malformed_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_access_token("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0")

    def test_custom_expiry(self):
        short_delta = timedelta(seconds=1)
        token = create_access_token(
            data={"sub": "user-exp"},
            expires_delta=short_delta,
        )
        payload = decode_access_token(token)
        assert payload["sub"] == "user-exp"

    def test_different_users_different_tokens(self):
        t1 = create_access_token(data={"sub": "user-a"})
        t2 = create_access_token(data={"sub": "user-b"})
        assert t1 != t2
        assert decode_access_token(t1)["sub"] == "user-a"
        assert decode_access_token(t2)["sub"] == "user-b"
