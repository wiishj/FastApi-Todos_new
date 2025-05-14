# Python 3.9 베이스 이미지
FROM python:3.9

# 비루트(non-root) 사용자 및 그룹 생성
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# 작업 디렉토리 설정
WORKDIR /app

# 파일 복사
COPY main.py /app/main.py
COPY requirements.txt /app/requirements.txt
COPY templates /app/templates
COPY tests/ ./app/tests/

# 애플리케이션 파일의 소유권을 비루트 사용자에게 변경
RUN chown -R appuser:appgroup /app && \
pip install --no-cache-dir -r requirements.txt

# 비루트 사용자로 전환한
USER appuser

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
