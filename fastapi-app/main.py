from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum
import json
import os
import logging
import time
from multiprocessing import Queue
from os import getenv
from fastapi import Request
from prometheus_fastapi_instrumentator import Instrumentator
from logging_loki import LokiQueueHandler

app = FastAPI()

# Prometheus 메트릭스 엔드포인트 (/metrics)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

loki_logs_handler = LokiQueueHandler(
    Queue(-1),
    url=getenv("LOKI_ENDPOINT"),
    tags={"application": "fastapi"},
    version="1",
)

# Custom access logger (ignore Uvicorn's default logging)
custom_logger = logging.getLogger("custom.access")
custom_logger.setLevel(logging.INFO)

# Add Loki handler (assuming `loki_logs_handler` is correctly configured)
custom_logger.addHandler(loki_logs_handler)

async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time  # Compute response time

    log_message = (
        f'{request.client.host} - "{request.method} {request.url.path} HTTP/1.1" {response.status_code} {duration:.3f}s'
    )

    # **Only log if duration exists**
    if duration:
        custom_logger.info(log_message)

    return response

class Category(str, Enum):
    workout = "운동"
    appointment = "약속"
    study = "공부"
    schedule = "일정"

# To-Do 항목 모델
class TodoItem(BaseModel):
    id: int
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None  # str로 변경
    completed: bool
    category: Optional[str]=None


# JSON 파일 경로
TODO_FILE = "todo.json"


# JSON 파일에서 To-Do 항목 로드
def load_todos():
    if not os.path.exists(TODO_FILE):
        return []

    try:
        with open(TODO_FILE, "r", encoding="utf-8") as file:
            data = file.read().strip()
            if not data:
                return []

            todos = json.loads(data)
            return todos  # JSON 데이터를 그대로 반환 (dict 형태)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 디코딩 오류: {e}")
        return []


def save_todos(todos):
    with open(TODO_FILE, "w", encoding="utf-8") as file:
        json.dump(todos, file, indent=5, ensure_ascii=False)


# To-Do 목록 조회
@app.get("/todos", response_model=list[TodoItem])
def get_todos():
    return load_todos()


@app.get("/todos/{todo_id}")
def get_todo(todo_id: int):
    todos = load_todos()
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")


# 신규 To-Do 항목 추가
@app.post("/todos", response_model=TodoItem)
def create_todo(todo: TodoItem):
    todos = load_todos()
    todos.append(todo.dict())
    save_todos(todos)
    return todo


# To-Do 항목 수정 (완료 여부 수정 포함)
@app.put("/todos/{todo_id}", response_model=TodoItem)
def update_todo(todo_id: int, updated_todo: TodoItem):
    todos = load_todos()

    for todo in todos:
        if todo["id"] == todo_id:
            if updated_todo.title is not None:
                todo["title"] = updated_todo.title
            if updated_todo.description is not None:
                todo["description"] = updated_todo.description
            if updated_todo.deadline is not None:
                todo["deadline"] = updated_todo.deadline
            todo["completed"] = updated_todo.completed

            save_todos(todos)
            return todo

    raise HTTPException(status_code=404, detail="To-Do item not found")


# To-Do 항목 삭제
@app.delete("/todos/{todo_id}", response_model=dict)
def delete_todo(todo_id: int):
    todos = load_todos()
    todos = [todo for todo in todos if todo["id"] != todo_id]
    save_todos(todos)
    return {"message": "To-Do item deleted"}


@app.patch("/todos/{todo_id}/toggle")
def toggle_todo_completion(todo_id: int):
    todos = load_todos()
    for todo in todos:
        if todo["id"] == todo_id:
            todo["completed"] = not todo["completed"]
            break
    save_todos(todos)
    raise HTTPException(status_code=404, detail="Todo not found")


# HTML 파일 서빙
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content)
