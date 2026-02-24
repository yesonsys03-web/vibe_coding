# Google Stitch Prompt Pack - VibeCoder Playground

## 사용법
- 아래 프롬프트를 Stitch에 그대로 넣고, 화면별 시안을 생성한다.
- 결과물은 모바일 먼저 확인 후 데스크톱 버전을 만든다.
- 생성된 시안은 `docs/VIBECODER_PLAYGROUND_DESIGN_SYSTEM.md` 원칙과 비교해 선택한다.

## Global Prompt (공통)
```text
Design a Korean community showcase website called "VibeCoder Playground".

Brand direction:
- playful, experimental, electric, handmade
- avoid generic corporate SaaS style
- message: "완성도보다 바이브. 실험도 작품이다."

Visual rules:
- deep navy layered background
- poster-stack style cards with subtle angle overlap
- sticker labels: New, Hot, Weird, WIP
- fonts: Space Grotesk for display, Pretendard for body, JetBrains Mono for code/tag

Accessibility:
- high contrast text
- visible focus ring
- keyboard friendly interactions

Deliver mobile-first layout and desktop adaptation.
```

## Screen 1 - Home/Feed
```text
Create the Home/Feed screen for VibeCoder Playground.

Must include:
- hero section with strong statement and CTA button "작품 올리기"
- trending strip with 6 project thumbnails
- main feed grid with project cards
- filter chips (platform, stack, tags)
- each card: thumbnail, title, one-line summary, tags, author nickname, like/comment counts

Interaction cues:
- hover tilt on cards
- clear active state for filter chips
- empty state copy for no results

Tone:
- feels like a creator playground, not a formal portfolio site
```

## Screen 2 - Project Detail
```text
Create the Project Detail screen for VibeCoder Playground.

Must include:
- title, author, date, tags
- media area (carousel or embed)
- sections: 제작 의도, 사용 기술, 느낀 점
- actions: like, share, external link
- comment section with sorting (최신, 공감순)
- report entry point for comments

Microcopy requirement:
- first-comment helper text: "좋았던 포인트 한 가지를 남겨보세요"
- behavior guideline: "존중 기반 피드백만 허용"
```

## Screen 3 - Submit Project
```text
Create the Submit Project screen for VibeCoder Playground.

Must include form fields:
- title (required)
- one-line summary (required)
- description (optional)
- thumbnail upload or URL
- demo URL and GitHub URL
- tags (max 5)
- platform selector (web/app/ai/etc)

Must include UX states:
- live preview card while editing
- inline error states
- success confirmation with "내 작품 보기" button
```

## Screen 4 - Profile
```text
Create the Profile screen for VibeCoder Playground.

Must include:
- profile header with nickname and bio
- tabs: 작품, 댓글, 좋아요
- activity highlights (light gamification)
- list cards consistent with Home feed style
```

## Selection Criteria (시안 선택 기준)
- 컨셉 적합도: "놀이터" 감성이 드러나는가
- 가독성: 정보 밀도가 높아도 읽기 쉬운가
- 확장성: 댓글/신고/관리 흐름을 붙이기 쉬운가
- 구현성: v0로 무리 없이 이식 가능한 구조인가
