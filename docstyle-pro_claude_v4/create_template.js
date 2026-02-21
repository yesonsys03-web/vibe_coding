/**
 * create_template.js
 * DocStyle Pro 사용자 작성 템플릿 (.dotx) 생성
 *
 * DS-* 커스텀 스타일 10종을 포함한 Word 템플릿을 만든다.
 * 사용자는 이 파일을 열고 평소처럼 글을 쓰면서
 * 스타일 패널에서 DS-* 스타일만 지정하면 된다.
 */

"use strict";

const {
  Document, Packer, Paragraph, TextRun,
  AlignmentType, BorderStyle, ShadingType,
  HeadingLevel, LevelFormat,
} = require("docx");
const fs = require("fs");

// ─────────────────────────────────────────────
// 커스텀 스타일 정의
// ─────────────────────────────────────────────

const paragraphStyles = [

  // ── DS-ChapterTitle ─────────────────────────
  {
    id: "DSChapterTitle",
    name: "DS-ChapterTitle",
    basedOn: "Normal",
    next: "Normal",
    quickFormat: true,
    run: { bold: true, size: 32, font: "Arial", color: "FFFFFF" },
    paragraph: {
      spacing: { before: 0, after: 160 },
      shading: { fill: "1E293B", type: ShadingType.CLEAR },
    },
  },

  // ── DS-Insight (빨간 강조 박스) ──────────────
  {
    id: "DSInsight",
    name: "DS-Insight",
    basedOn: "Normal",
    next: "Normal",
    quickFormat: true,
    run: { bold: true, size: 22, font: "Arial", color: "1E293B" },
    paragraph: {
      spacing: { before: 120, after: 120 },
      indent: { left: 280, right: 240 },
      shading: { fill: "FEF2F2", type: ShadingType.CLEAR },
      border: {
        left: { style: BorderStyle.THICK, size: 18, color: "DC2626", space: 6 },
        top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      },
    },
  },

  // ── DS-Tip (초록 Tip 박스) ───────────────────
  {
    id: "DSTip",
    name: "DS-Tip",
    basedOn: "Normal",
    next: "Normal",
    quickFormat: true,
    run: { size: 22, font: "Arial", color: "1E293B" },
    paragraph: {
      spacing: { before: 100, after: 100 },
      indent: { left: 280, right: 240 },
      shading: { fill: "F0FDF4", type: ShadingType.CLEAR },
      border: {
        left: { style: BorderStyle.THICK, size: 18, color: "047857", space: 6 },
        top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      },
    },
  },

  // ── DS-Warning (황색 주의 박스) ──────────────
  {
    id: "DSWarning",
    name: "DS-Warning",
    basedOn: "Normal",
    next: "Normal",
    quickFormat: true,
    run: { size: 22, font: "Arial", color: "1E293B" },
    paragraph: {
      spacing: { before: 100, after: 100 },
      indent: { left: 280, right: 240 },
      shading: { fill: "FFFBEB", type: ShadingType.CLEAR },
      border: {
        left: { style: BorderStyle.THICK, size: 18, color: "B45309", space: 6 },
        top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      },
    },
  },

  // ── DS-Quote (파란 인용 박스) ─────────────────
  {
    id: "DSQuote",
    name: "DS-Quote",
    basedOn: "Normal",
    next: "Normal",
    quickFormat: true,
    run: { italics: true, size: 22, font: "Arial", color: "374151" },
    paragraph: {
      spacing: { before: 120, after: 120 },
      indent: { left: 280, right: 240 },
      shading: { fill: "EFF6FF", type: ShadingType.CLEAR },
      border: {
        left: { style: BorderStyle.THICK, size: 18, color: "3B82F6", space: 6 },
        top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      },
    },
  },

  // ── DS-QA-Question ───────────────────────────
  {
    id: "DSQAQuestion",
    name: "DS-QA-Question",
    basedOn: "Normal",
    next: "DSQAAnswer",
    quickFormat: true,
    run: { bold: true, size: 20, font: "Arial", color: "FFFFFF" },
    paragraph: {
      spacing: { before: 160, after: 0 },
      indent: { left: 240, right: 240 },
      shading: { fill: "1E293B", type: ShadingType.CLEAR },
      border: {
        top: { style: BorderStyle.SINGLE, size: 2, color: "3B82F6", space: 1 },
        bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      },
    },
  },

  // ── DS-QA-Answer ─────────────────────────────
  {
    id: "DSQAAnswer",
    name: "DS-QA-Answer",
    basedOn: "Normal",
    next: "DSQAAnswer",
    quickFormat: true,
    run: { size: 20, font: "Arial", color: "374151" },
    paragraph: {
      spacing: { before: 50, after: 40 },
      indent: { left: 360, right: 240 },
      shading: { fill: "EFF6FF", type: ShadingType.CLEAR },
      border: {
        top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        left: { style: BorderStyle.SINGLE, size: 2, color: "93C5FD", space: 1 },
        right: { style: BorderStyle.SINGLE, size: 2, color: "93C5FD", space: 1 },
      },
    },
  },

  // ── DS-Prompt ────────────────────────────────
  {
    id: "DSPrompt",
    name: "DS-Prompt",
    basedOn: "Normal",
    next: "Normal",
    quickFormat: true,
    run: { italics: true, size: 20, font: "Arial", color: "9CA3AF" },
    paragraph: {
      spacing: { before: 60, after: 0 },
      indent: { left: 280, right: 240 },
      shading: { fill: "1E293B", type: ShadingType.CLEAR },
      border: {
        top: { style: BorderStyle.SINGLE, size: 2, color: "3B82F6", space: 1 },
        bottom: { style: BorderStyle.SINGLE, size: 2, color: "3B82F6", space: 1 },
        left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      },
    },
  },

  // ── DS-Conclusion ────────────────────────────
  {
    id: "DSConclusion",
    name: "DS-Conclusion",
    basedOn: "Normal",
    next: "Normal",
    quickFormat: true,
    run: { size: 22, font: "Arial", color: "FFFFFF" },
    paragraph: {
      spacing: { before: 60, after: 60 },
      indent: { left: 280, right: 280 },
      shading: { fill: "1E293B", type: ShadingType.CLEAR },
      border: {
        top: { style: BorderStyle.THICK, size: 12, color: "DC2626", space: 1 },
        bottom: { style: BorderStyle.THICK, size: 8, color: "DC2626", space: 1 },
        left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      },
    },
  },

  // ── DS-Caption ───────────────────────────────
  {
    id: "DSCaption",
    name: "DS-Caption",
    basedOn: "Normal",
    next: "Normal",
    quickFormat: true,
    run: { italics: true, size: 18, font: "Arial", color: "6B7280" },
    paragraph: {
      alignment: AlignmentType.CENTER,
      spacing: { before: 30, after: 100 },
    },
  },

];

// ─────────────────────────────────────────────
// 가이드 본문 작성
// ─────────────────────────────────────────────

const makeGuideBody = () => [

  // 제목
  new Paragraph({
    children: [new TextRun({ text: "DocStyle Pro — 사용 가이드", bold: true, size: 36, font: "Arial", color: "1E293B" })],
    spacing: { before: 0, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "DC2626", space: 4 } },
  }),

  new Paragraph({
    children: [new TextRun({ text: "이 파일을 복사해서 원고를 작성하세요. 아래 사용법을 읽은 후 내용을 지우고 시작합니다.", size: 22, font: "Arial", color: "374151" })],
    spacing: { before: 0, after: 240 },
  }),

  // ── 섹션: 기본 구조 ──
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text: "1.  파일 맨 위 메타데이터 작성", font: "Arial" })],
  }),
  new Paragraph({
    children: [new TextRun({ text: "아래 형식으로 파일 맨 위에 문서 정보를 작성합니다. DS-ChapterTitle 스타일이 자동으로 읽어갑니다.", size: 22, font: "Arial", color: "374151" })],
    spacing: { before: 60, after: 80 },
  }),
  new Paragraph({
    style: "DSQuote",
    children: [new TextRun({ text: "제목: 나의 데이터는 배신하지 않는다 | 작성자: 홍길동 | 챕터: [Phase 9] | 부제: 법률 문서 분석 · 나홀로 소송", italics: true, size: 20, font: "Arial" })],
  }),
  new Paragraph({ children: [], spacing: { before: 0, after: 120 } }),

  // ── 섹션: 스타일 목록 ──
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text: "2.  사용 가능한 스타일 목록", font: "Arial" })],
  }),
  new Paragraph({
    children: [new TextRun({ text: "스타일 패널(홈 탭 → 스타일)에서 DS-로 시작하는 스타일을 선택합니다.", size: 22, font: "Arial", color: "374151" })],
    spacing: { before: 60, after: 160 },
  }),

  // DS-ChapterTitle 예시
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text: "DS-ChapterTitle — 챕터 시작 페이지", font: "Arial" })],
  }),
  new Paragraph({
    style: "DSChapterTitle",
    children: [new TextRun({ text: "챕터 제목이 여기에 표시됩니다", bold: true, size: 32, font: "Arial", color: "FFFFFF" })],
  }),
  new Paragraph({ children: [], spacing: { before: 0, after: 80 } }),

  // DS-Insight 예시
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text: "DS-Insight — 빨간 강조 박스", font: "Arial" })],
  }),
  new Paragraph({
    style: "DSInsight",
    children: [new TextRun({ text: "핵심 메시지나 중요한 통찰을 강조할 때 사용합니다. 독자의 시선을 집중시킵니다.", font: "Arial" })],
  }),
  new Paragraph({ children: [], spacing: { before: 0, after: 80 } }),

  // DS-Tip 예시
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text: "DS-Tip — 초록 Tip 박스", font: "Arial" })],
  }),
  new Paragraph({
    style: "DSTip",
    children: [new TextRun({ text: "실용적인 팁이나 보충 설명을 제공할 때 사용합니다.", font: "Arial" })],
  }),
  new Paragraph({ children: [], spacing: { before: 0, after: 80 } }),

  // DS-Warning 예시
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text: "DS-Warning — 황색 주의 박스", font: "Arial" })],
  }),
  new Paragraph({
    style: "DSWarning",
    children: [new TextRun({ text: "주의사항이나 오류 방지 안내를 작성할 때 사용합니다.", font: "Arial" })],
  }),
  new Paragraph({ children: [], spacing: { before: 0, after: 80 } }),

  // DS-Quote 예시
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text: "DS-Quote — 인용 박스", font: "Arial" })],
  }),
  new Paragraph({
    style: "DSQuote",
    children: [new TextRun({ text: "전문가 발언, 책 인용, 또는 참고할 만한 문장을 블록 인용으로 표시합니다.", italics: true, font: "Arial" })],
  }),
  new Paragraph({ children: [], spacing: { before: 0, after: 80 } }),

  // DS-QA-Question / DS-QA-Answer 예시
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text: "DS-QA-Question / DS-QA-Answer — Q&A 블록", font: "Arial" })],
  }),
  new Paragraph({
    style: "DSQAQuestion",
    children: [new TextRun({ text: "Q  이 도구를 사용하면 어떤 점이 달라지나요?", bold: true, font: "Arial" })],
  }),
  new Paragraph({
    style: "DSQAAnswer",
    children: [new TextRun({ text: "A  복잡한 레이아웃을 자동으로 적용해 주므로 내용 작성에만 집중할 수 있습니다.", font: "Arial" })],
  }),
  new Paragraph({ children: [], spacing: { before: 0, after: 80 } }),

  // DS-Prompt 예시
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text: "DS-Prompt — 골든 프롬프트 박스", font: "Arial" })],
  }),
  new Paragraph({
    children: [new TextRun({ text: "라벨(프롬프트 이름): DS-Prompt 바로 위에 일반 텍스트로 '프롬프트 라벨:' 형식으로 작성", size: 20, font: "Arial", color: "64748B" })],
    spacing: { before: 40, after: 40 },
  }),
  new Paragraph({
    style: "DSPrompt",
    children: [new TextRun({ text: "\"업로드된 문서를 분석해서 핵심 쟁점을 3가지로 요약해 줘.\"", italics: true, font: "Arial" })],
  }),
  new Paragraph({ children: [], spacing: { before: 0, after: 80 } }),

  // DS-Conclusion 예시
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text: "DS-Conclusion — 결론 박스", font: "Arial" })],
  }),
  new Paragraph({
    children: [new TextRun({ text: "결론 박스는 여러 줄을 연속으로 작성합니다. 각 줄을 DS-Conclusion 스타일로 지정하세요.", size: 20, font: "Arial", color: "64748B" })],
    spacing: { before: 40, after: 40 },
  }),
  new Paragraph({
    style: "DSConclusion",
    children: [new TextRun({ text: "도구는 수단입니다.", font: "Arial" })],
  }),
  new Paragraph({
    style: "DSConclusion",
    children: [new TextRun({ text: "어떤 질문을 던지느냐에 따라 결과가 달라집니다.", font: "Arial" })],
  }),
  new Paragraph({ children: [], spacing: { before: 0, after: 80 } }),

  // DS-Caption 예시
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text: "DS-Caption — 이미지 캡션", font: "Arial" })],
  }),
  new Paragraph({
    children: [new TextRun({ text: "[ 이미지 ]", size: 20, font: "Arial", color: "9CA3AF" })],
    alignment: AlignmentType.CENTER,
    shading: { fill: "F1F5F9", type: ShadingType.CLEAR },
    border: {
      top: { style: BorderStyle.SINGLE, size: 2, color: "CBD5E1" },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: "CBD5E1" },
      left: { style: BorderStyle.SINGLE, size: 2, color: "CBD5E1" },
      right: { style: BorderStyle.SINGLE, size: 2, color: "CBD5E1" },
    },
    spacing: { before: 60, after: 0 },
  }),
  new Paragraph({
    style: "DSCaption",
    children: [new TextRun({ text: "그림 1. 이미지 아래에 DS-Caption 스타일로 설명을 작성합니다", italics: true, font: "Arial" })],
  }),
  new Paragraph({ children: [], spacing: { before: 0, after: 160 } }),

  // ── 섹션: 주의사항 ──
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text: "3.  주의사항", font: "Arial" })],
  }),
  ...[
    "이 파일을 복사해서 사용하세요. 원본 템플릿은 보관합니다.",
    "이미지는 워드 파일과 같은 폴더에 저장하면 자동으로 인식됩니다.",
    "표는 Word 기본 표 기능으로 작성합니다. 2열 또는 3열 표가 자동 변환됩니다.",
    "목록(불릿)은 Word 기본 목록 기능을 사용합니다.",
    "DS-QA-Question 다음 줄은 자동으로 DS-QA-Answer 스타일이 적용됩니다.",
    "DS-Prompt 바로 앞 줄에 '라벨:' 형식으로 프롬프트 이름을 작성합니다.",
  ].map(t => new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text: t, size: 21, font: "Arial", color: "374151" })],
  })),

];

// ─────────────────────────────────────────────
// 문서 생성
// ─────────────────────────────────────────────

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: "▸",
        alignment: AlignmentType.LEFT,
        style: {
          paragraph: { indent: { left: 480, hanging: 240 } },
          run: { font: "Arial", color: "3B82F6" },
        },
      }],
    }],
  },
  styles: {
    default: {
      document: { run: { font: "Arial", size: 22, color: "1E293B" } },
    },
    paragraphStyles,
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1260, right: 1260, bottom: 1260, left: 1440 },
      },
    },
    children: makeGuideBody(),
  }],
});

// ─────────────────────────────────────────────
// 저장
// ─────────────────────────────────────────────

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("DocStylePro_Template.dotx", buffer);
  console.log("✅ DocStylePro_Template.dotx 생성 완료");
});
