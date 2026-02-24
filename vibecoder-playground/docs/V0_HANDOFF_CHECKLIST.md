# v0 Handoff Checklist - VibeCoder Playground

## 목적
- Stitch에서 확정한 디자인을 v0로 안정적으로 이식하기 위한 체크리스트.

## 1) 이식 전 준비
- [ ] Stitch 최종 시안(모바일/데스크톱) 캡처 확보
- [ ] 색상/타입/간격 토큰 확정
- [ ] 화면별 필수 컴포넌트 목록 확정
- [ ] 인터랙션 노트(애니메이션 시간/상태 전환) 정리

## 2) v0 생성 프롬프트 템플릿
```text
Build a responsive React page based on this design spec.

Requirements:
- Preserve layout hierarchy and visual language from provided references.
- Use reusable components for nav, cards, comments, and modal.
- Mobile-first responsive behavior.
- Include loading, empty, and error states.
- Keep text in Korean.

Do not:
- Replace brand colors with generic defaults.
- Remove report/comment interaction points.
```

## 3) 컴포넌트 이식 순서
1. 레이아웃 골격 (Nav, container, section spacing)
2. 피드 핵심 (`HeroBanner`, `ProjectCard`, `FilterChips`)
3. 상세/댓글 (`CommentList`, `CommentComposer`, `ReportModal`)
4. 등록/프로필
5. 상태 UI(로딩/빈값/에러)

## 4) 품질 체크
- [ ] 모바일 360px에서 콘텐츠 잘림 없음
- [ ] 태블릿/데스크톱 그리드 전환 자연스러움
- [ ] 포커스 링 표시
- [ ] 색 대비 충분
- [ ] CTA가 명확하고 일관됨

## 5) FastAPI 연동 준비
- [ ] 프로젝트 목록/상세 API 응답 필드 매핑 확인
- [ ] 댓글 작성/조회/신고 API 인터페이스 고정
- [ ] 실패 응답(`code`, `message`, `field_errors`) 표시 UI 준비

## 6) GitHub 반영 전 최종 점검
- [ ] 기능 단위 파일 분리
- [ ] 죽은 코드 제거
- [ ] 하드코딩 임시 문자열 제거
- [ ] 스크린샷(모바일/데스크톱) 캡처 완료
- [ ] PR 템플릿 항목 채울 자료 준비 완료
