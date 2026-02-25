# 🚀 안티그래비티 × OpenCode 완벽 세팅 가이드

안티그래비티(Antigravity)의 강력한 Gemini 3.1 모델을 터미널의 OpenCode 에이전트와 연동하여 사용하는 **"국룰" 세팅법**입니다. (macOS, Homebrew 기준)

---

## 🛠 1단계: 기초 환경 구축 (Runtime)

OpenCode가 실행될 수 있는 가장 빠르고 안정적인 환경을 만듭니다.

### 1. Bun & Node.js 설치
Homebrew를 사용하여 설치합니다. (`brew tab` 아님 주의!)

```bash
# 1. Bun 공식 저장소 연결 (Tap)
brew tap oven-sh/bun

# 2. Bun 런타임 설치
brew install bun

# 3. Node.js 설치 (OpenCode 실행 필수 의존성)
brew install node
```

### 2. 설치 확인
```bash
bun --version
node --version
```

---

## 📦 2단계: 도구 설치 (OpenCode & OMO)

### 1. OpenCode 엔진 설치 (Global)
프로젝트 생성 및 어디서든 실행하기 위해 전역(-g)으로 설치합니다.
(오타 주의: opencode-al ❌ -> opencode-ai ⭕)

```bash
bun add -g opencode-ai
```

### 2. Oh My OpenCode (OMO) 설치
설정을 도와주는 프레임워크입니다.

설치 중 질문: AI Provider는 Google 선택. API Key 입력란은 **Enter(Skip)**로 넘기세요.

```bash
bunx oh-my-opencode install
```

### 3. 환경 변수(PATH) 설정 (필수 ⭐)
설치 후 "command not found" 에러 방지를 위해 경로를 등록합니다.

```bash
echo 'export PATH="/Users/$(whoami)/.bun/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## ⚙️ 3단계: 두뇌 연결 (Configuration)

이 과정이 핵심입니다. 유료 API 키 대신 안티그래비티의 권한을 사용하도록 설정합니다.

### 1. 설정 파일 열기
```bash
code ~/.config/opencode/opencode.json
# 또는 nano ~/.config/opencode/opencode.json
```

### 2. 플러그인 및 모델 버전 수정
파일 내용을 아래와 같이 수정합니다. (Gemini 3 Pro -> 3.1 Pro 업데이트 필수)

**변경 포인트 1:** plugins 배열에 인증 모듈 추가

```json
"plugins": [
  "oh-my-opencode@latest",
  "opencode-antigravity-auth"  // <-- 콤마(,) 찍고 이 줄 추가!
],
```

**변경 포인트 2:** 모델 버전을 최신(3.1)으로 변경
antigravity-gemini-3-pro 부분을 찾아 **3-1-pro**로 고쳐야 에러가 안 납니다.

```json
"antigravity-gemini-3-1-pro": {  // <-- 3-pro를 3-1-pro로 변경
  "name": "Gemini 3.1 Pro (Antigravity)", // <-- 이름도 3.1로 변경
  ...
},
"antigravity-gemini-3-1-flash": { // <-- Flash 모델도 3.1로 변경
  "name": "Gemini 3.1 Flash (Antigravity)",
  ...
}
```

### 3. 최종 인증 로그인
```bash
opencode auth login
```

- Select provider: **Google**
- Login method: **OAuth with Antigravity**
- Project ID: (그대로 Enter)

결과: 브라우저 창이 뜨면 구글 로그인 후 '허용' 클릭.

---

## 🏃‍♂️ 4단계: 실전 사용법

### 기본 명령어
- **대화형 모드:** `opencode` (터미널에서 AI와 채팅하며 코딩)
- **즉시 명령:** `opencode "README.md 파일 만들어줘"`
- **파일 인식:** 대화 중 `/add main.py` 입력 (해당 파일을 읽고 수정해줌)

### 협업 시 주의사항 (Global vs Local)
- 나 혼자: 그냥 opencode (Global) 사용.
- 팀 프로젝트: 프로젝트 폴더 내에서 버전을 고정해야 함.

```bash
cd my-project
bun add -d opencode-ai  # package.json에 버전 박제
```

---

## 🚨 트러블슈팅 (Troubleshooting)

### Q1. 화면에 "明明明明..." 같은 이상한 글자가 무한 반복돼요!
**원인:** 바탕화면(Desktop) 접근 권한이 없거나, 파일이 너무 많아 AI가 고장 난 상태.

**해결:**
1. 즉시 `Ctrl + C`로 강제 종료.
2. 시스템 설정 > 개인정보 보호 및 보안 > 파일 및 폴더 > 터미널(또는 Bun)의 접근 권한 허용.
3. 바탕화면 대신 별도 폴더를 만들어 작업할 것.

### Q2. Claude나 ChatGPT 구독 중인데 써도 되나요?
**답변:** 비추천합니다.

OpenCode는 웹 채팅 구독(Plus/Pro)이 아니라 **API Key(종량제)**가 필요합니다.

안티그래비티 환경에서는 Google(Gemini) 설정이 무료이고 성능도 최적화되어 있습니다.

### Q3. "Gemini 3 Pro is no longer available" 에러가 떠요.
**해결:** 3단계 설정을 참고하여 opencode.json 파일 내 모델 이름을 3-1-pro로 수정하세요.
