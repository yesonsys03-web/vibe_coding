# UV Workflow Guide

## 원칙
- 이 프로젝트의 Python 환경/의존성 관리는 `uv`만 사용한다.
- 패키지 설치는 항상 `uv add <package>`로 진행한다.
- `pip install`은 사용하지 않는다.

## 초기 세팅
```bash
uv sync
```

## 자주 쓰는 명령
```bash
# 개발 서버 실행 예시
uv run uvicorn app.main:app --reload

# 패키지 추가
uv add fastapi
uv add "uvicorn[standard]"

# 개발 전용 패키지 추가
uv add --dev pytest ruff

# 잠금 파일 기준으로 재현 설치
uv sync --frozen
```

## 협업 규칙
- 의존성 변경 시 `pyproject.toml`과 `uv.lock`을 함께 커밋한다.
- CI에서는 `uv sync --frozen`을 사용해 잠금 파일과 불일치 설치를 방지한다.
- 로컬 인터프리터는 `${workspaceFolder}/.venv/bin/python`을 사용한다.
