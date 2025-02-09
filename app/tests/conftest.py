import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..database import Base
from ..main import app, get_db, get_cache_service, get_rate_limiter, get_stats_tracker
from ..auth.auth import create_access_token
from ..cache import CacheService
from unittest.mock import Mock, patch
import os
import tempfile
import asyncio

# Use SQLite in-memory database for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def mock_redis():
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.hincrby.return_value = 1
    mock_redis.hgetall.return_value = {"downloads": "1"}
    return mock_redis

@pytest.fixture
def mock_cache_service(mock_redis):
    return CacheService(redis_client=mock_redis)

@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db, mock_cache_service):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    def override_get_cache_service():
        return mock_cache_service

    def override_get_rate_limiter():
        return Mock()

    def override_get_stats_tracker():
        return Mock()
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache_service] = override_get_cache_service
    app.dependency_overrides[get_rate_limiter] = override_get_rate_limiter
    app.dependency_overrides[get_stats_tracker] = override_get_stats_tracker
    return TestClient(app)

@pytest.fixture
def test_module_zip():
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp.write(b"test content")
        return tmp.name

@pytest.fixture
def auth_headers():
    # Create a valid test token with all required permissions
    token_data = {
        "sub": "test-user",
        "permissions": [
            "read:module",
            "write:module",
            "upload:module",
            "generate:module"
        ]
    }
    token = asyncio.run(create_access_token(token_data))
    return {"Authorization": f"Bearer {token}"}
