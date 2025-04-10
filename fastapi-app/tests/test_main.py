import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from main import app, save_todos, load_todos, TodoItem

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # 테스트 전 초기화
    save_todos([])
    yield
    # 테스트 후 정리
    save_todos([])

def test_get_todos_empty():
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []

def test_get_todos_with_items():
    todo = TodoItem(id=1, title="Test", description="Test description", deadline="2025-04-10", category="공부", completed=False)
    save_todos([todo.dict()])
    response = client.get("/todos")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Test"

def test_create_todo():
    todo = {"id": 1, "title": "Test", "description": "Test description", "deadline" : "2025-04-10", "category" : "공부", "completed": False}
    response = client.post("/todos", json=todo)
    assert response.status_code == 200
    assert response.json()["title"] == "Test"

def test_create_todo_invalid():
    todo = {"id": 1, "title": "Test"}
    response = client.post("/todos", json=todo)
    assert response.status_code == 422

def test_update_todo():
    todo = TodoItem(id=1, title="Test", description="Test description", deadline="2025-04-10", category="공부", completed=False)
    save_todos([todo.dict()])
    updated_todo = {"id": 1, "title": "Updated", "description": "Test description", "deadline" : "2025-04-10", "category" : "공부", "completed": False}
    response = client.put("/todos/1", json=updated_todo)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"

def test_update_todo_not_found():
    updated_todo = {"id": 1, "title": "Updated", "description": "Updated description", "deadline" : "2025-04-10", "category" : "공부", "completed": True}
    response = client.put("/todos/1", json=updated_todo)
    assert response.status_code == 404

def test_delete_todo():
    todo = TodoItem(id=1, title="Test", description="Test description", deadline="2025-04-10", category="공부", completed=False)
    save_todos([todo.dict()])
    response = client.delete("/todos/1")
    assert response.status_code == 200
    assert response.json()["message"] == "To-Do item deleted"
    
def test_delete_todo_not_found():
    response = client.delete("/todos/1")
    assert response.status_code == 200
    assert response.json()["message"] == "To-Do item deleted"

def test_create_todo_missing_fields():
    # 필수 필드가 빠진 상태에서 todo를 생성하려는 테스트
    todo = {"id": 1, "title": "Test"}  # deadline, category, completed 빠짐
    response = client.post("/todos", json=todo)
    assert response.status_code == 422  # 유효하지 않은 데이터가 들어가면 422 상태 코드

def test_get_todo_not_found():
    # 존재하지 않는 todo의 id로 요청할 경우 404 에러 확인
    response = client.get("/todos/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "To-Do item not found"

def test_update_todo_invalid_data():
    # 잘못된 데이터 타입 또는 필드 누락시 업데이트 요청 테스트
    updated_todo = {"id": 1, "title": 12345, "description": "Updated description", "deadline": "2025-04-10", "category": "공부", "completed": "yes"}
    response = client.put("/todos/1", json=updated_todo)
    assert response.status_code == 422  # 필드 타입이 잘못되었을 때 422 상태 코드

def test_delete_todo_invalid_id():
    # 존재하지 않는 ID로 삭제 요청 시 404 에러
    response = client.delete("/todos/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "To-Do item not found"

def test_get_todos_with_invalid_filter():
    # 잘못된 쿼리 파라미터로 todos를 필터링하는 테스트
    response = client.get("/todos?category=nonexistent")
    assert response.status_code == 200
    assert response.json() == []  # 해당 카테고리가 없는 경우 빈 리스트를 반환

def test_create_todo_invalid_deadline():
    # 잘못된 형식의 deadline을 제공할 경우
    todo = {"id": 2, "title": "Test", "description": "Test description", "deadline": "invalid-date", "category": "공부", "completed": False}
    response = client.post("/todos", json=todo)
    assert response.status_code == 422  # 유효하지 않은 날짜 형식

def test_create_todo_missing_id():
    # ID를 누락한 채 todo를 생성하려고 할 경우
    todo = {"title": "Test", "description": "Test description", "deadline": "2025-04-10", "category": "공부", "completed": False}
    response = client.post("/todos", json=todo)
    assert response.status_code == 422  # ID가 없으면 422 상태 코드
