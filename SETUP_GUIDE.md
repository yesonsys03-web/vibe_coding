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

## 5. 원격 저장소 연결 (GitHub)
이 환경을 GitHub에 연결하려면 다음 명령어를 실행하세요:

```bash
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```

---
**주의:** 절대 `pip install`을 사용하지 마세요. 모든 설정은 `pyproject.toml`과 `uv.lock`을 통해 관리됩니다.
