# 개발 환경 설정 가이드 (uv + Qt)

이 가이드는 회사와 집, 그리고 동료들의 개발 환경을 동일하게 맞추기 위한 가이드입니다.

## 1. uv 설치
`uv`는 매우 빠른 파이썬 패키지 및 프로젝트 매니저입니다. 기존의 `pip` 대신 사용합니다.

### macOS / Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 2. 프로젝트 구조
이 저장소는 4가지 주요 파이썬 + Qt 조합을 포함하고 있습니다:
- `python310_qt5`: Python 3.10 + PyQt5
- `python310_qt6`: Python 3.10 + PyQt6
- `python312_qt5`: Python 3.12 + PyQt5
- `python312_qt6`: Python 3.12 + PyQt6

## 3. 환경 동기화 (Add)
새로운 라이브러리를 설치할 때는 **반드시** `uv add`를 사용하세요.

```bash
# 예시: requests 라이브러리 추가
cd python312_qt6
uv add requests
```

## 4. 스크립트 실행
가상환경을 수동으로 활성화할 필요 없이 `uv run`을 사용하면 편리합니다.

```bash
uv run main.py
```

```bash
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```

## 6. VS Code 워크스페이스 설정
여러 환경을 효율적으로 관리하기 위해 미리 설정된 멀티 루트 워크스페이스를 사용하세요.

1. VS Code에서 **File > Open Workspace from File...** 을 선택합니다.
2. 루트 디렉토리의 `python-environments.code-workspace` 파일을 엽니다.
3. 왼쪽 탐색기에서 각 환경(3.10+Qt5, 3.12+Qt6 등)이 개별 폴더로 분리되어 나타납니다.

---
**주의:** 절대 `pip install`을 사용하지 마세요. 모든 설정은 `pyproject.toml`과 `uv.lock`을 통해 관리됩니다.

## 7. 이 구조의 장점 (Advantages)
이 프로젝트 구조는 다음과 같은 강력한 이점을 제공합니다:

- **🚀 압도적인 속도**: `uv`는 Rust로 작성되어 기존 `pip`나 `poetry`보다 훨씬 빠른 패키지 설치 및 동기화 속도를 자랑합니다.
- **🎯 일관된 개발 환경**: `uv.lock` 파일을 통해 모든 팀원이 소수점 자리까지 동일한 라이브러리 버전을 사용함을 보장합니다 (Deterministic builds).
- **🛡️ 완벽한 환경 격리**: Python 및 Qt 버전별로 독립된 환경을 관리하여, 버전 충돌 걱정 없이 다양한 조합을 테스트할 수 있습니다.
- **🪄 간편한 실행**: 가상환경을 수동으로 `activate`할 필요 없이, `uv run` 명령어로 즉시 프로젝트 환경에서 스크립트를 실행할 수 있습니다.
- **📦 단일화된 관리**: `pyproject.toml` 파일 하나로 프로젝트 설정, 파이썬 버전, 의존성을 모두 중앙 집중식으로 관리합니다.

