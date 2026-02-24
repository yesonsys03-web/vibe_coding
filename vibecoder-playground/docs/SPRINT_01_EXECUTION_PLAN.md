# VibeCoder Playground - Sprint 01 Execution Plan

## 목표
- 1주 안에 "디자인 확정 -> UI 이식 -> FastAPI 연결 -> GitHub PR"까지 한 사이클을 완료한다.

## Sprint 기간
- 권장: 5 working days

## Day-by-Day
### Day 1 - Stitch 디자인 확정
- Home, Project Detail, Submit, Profile 4개 화면 시안 확정
- 상태별 컴포넌트(default/hover/loading/error) 캡처 확보
- 디자인 토큰(색상, 타이포, 간격, 라운드) 확정

### Day 2 - v0 이식
- 공통 레이아웃(`TopNav`, main container, footer) 생성
- `ProjectCard`, `FilterChips`, `HeroBanner` 생성
- 모바일 우선 반응형 맞춤

### Day 3 - 상호작용/댓글
- `CommentList`, `CommentComposer`, `ReportModal` 생성
- 빈 상태/에러 상태/로딩 상태 구현
- 접근성 기본점검(포커스, 레이블, 대비)

### Day 4 - FastAPI 연동
- `GET /projects`, `GET /projects/{id}`, `GET/POST /projects/{id}/comments` 연결
- `POST /comments/{id}/report` 연결
- API 에러 메시지 표준 포맷 UI 반영

### Day 5 - GitHub PR & QA
- 기능 단위 브랜치 정리
- PR 생성(스크린샷/테스트/리스크 포함)
- 리뷰 반영 후 main 머지
- 학습 로그 업데이트

## DoD (Definition of Done)
- 데스크톱/모바일에서 레이아웃 깨짐 없음
- 작품 목록/상세/댓글 작성/신고가 실제 동작
- 에러/빈 상태가 사용자에게 명확히 노출
- PR 템플릿 기준 항목 모두 작성 완료
- `docs/IMPLEMENTATION_LEARNING_LOG.md` Session 업데이트 완료

## 리스크 & 대응
- 디자인 편차 발생: Stitch 원본 대비 QA 체크리스트 강제
- 댓글 스팸 증가: 레이트리밋 + 신고 임계치 즉시 적용
- 개발 지연: Day 4에서 실시간 기능 제외하고 폴링 유지

## 산출물 체크리스트
- Stitch 시안 캡처 (4화면 x 모바일/데스크톱)
- v0 코드 반영 브랜치
- FastAPI 연동 PR
- 학습 로그 Session 기록
