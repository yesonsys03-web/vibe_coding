/**
 * template_01_classic.js — Classic Editorial
 *
 * 출판사 원고 스타일
 * 다크 헤더 · 빨간 액센트 · 박스형 구획
 * 이 책(NotebookLM 활용서) 시리즈의 기본 스타일
 */

"use strict";

/** 색상 시스템 — 이 객체만 교체하면 완전히 다른 템플릿이 된다 */
const C = {
  // ── 배경
  BG_HEAD: "1E293B",   // 챕터 헤더 · Q&A 헤더 · 프롬프트 박스
  BG_BOX: "EFF6FF",   // 인용·Q&A 답변 박스 배경
  BG_RED: "FEF2F2",   // 강조(insight) 박스 배경
  BG_GREEN: "F0FDF4",   // Tip 박스 배경
  BG_AMBER: "FFFBEB",   // 주의 박스 배경

  // ── 주요 텍스트
  WHITE: "FFFFFF",
  TEXT: "1E293B",   // 기본 본문
  DARK: "1E293B",   // 제목
  GRAY: "374151",   // 보조 텍스트
  GRAY2: "6B7280",   // 캡션
  GRAY3: "9CA3AF",   // 부제·헤더 설명

  // ── 브랜드 컬러
  ACCENT: "DC2626",   // 빨간 액센트 (챕터 헤더 선, 번호)
  BLUE: "1D4ED8",   // h2 제목
  BLUE2: "3B82F6",   // h1 구분선 · 박스 상단 선
  BOX_BORDER: "93C5FD",   // 인용 박스 테두리
  GREEN: "047857",   // Tip 텍스트
  AMBER: "B45309",   // 주의 텍스트

  // ── 구분선
  RULE: "E5E7EB",

  // ── 메타 정보 (썸네일 생성용)
  // ── 스타일 특성
  FONT: "Georgia",
  TYPE: "EDITORIAL",
  NAME: "Classic Editorial",
  TAG: "출판사 원고",
  DESC: "다크 헤더 · 빨간 액센트 · 박스형 구획 — 이 책 시리즈 기본 스타일",
};

module.exports = { C };
