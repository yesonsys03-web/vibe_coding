/**
 * builder.js — DocStyle Pro 문서 빌드 파이프라인
 *
 * 역할
 *  1. input JSON을 읽어 요소 배열로 파싱
 *  2. 선택된 템플릿의 색상(C)과 스타일 함수 로드
 *  3. elements.js 함수로 각 요소를 docx 객체로 변환
 *  4. Header / Footer / numbering 공통 설정 적용
 *  5. 완성된 Document 객체 반환
 */

"use strict";

const {
  Document, Header, Footer, Paragraph, TextRun,
  AlignmentType, BorderStyle, ShadingType, LevelFormat,
} = require("docx");

const E = require("./elements");

// ─────────────────────────────────────────────
// numbering 설정 (bullets — 모든 템플릿 공통)
// ─────────────────────────────────────────────
const makeNumbering = (C) => ({
  config: [
    {
      reference: "bullets",
      levels: [
        {
          level: 0,
          format: LevelFormat.BULLET,
          text: "▸",
          alignment: AlignmentType.LEFT,
          style: {
            paragraph: { indent: { left: 480, hanging: 240 } },
            run: { font: C.FONT || "Arial", color: C.BLUE2 },
          },
        },
      ],
    },
  ],
});

// ─────────────────────────────────────────────
// Header / Footer 공통 생성
// ─────────────────────────────────────────────
const makeHeader = (meta, C) =>
  new Header({
    children: [
      new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.RULE, space: 2 } },
        spacing: { before: 0, after: 100 },
        children: [
          E.run(`${meta.title || ""}    `, { size: 18, color: C.GRAY3 }, C),
          E.run(meta.chapter || "", { size: 18, color: C.BLUE, bold: true }, C),
        ],
      }),
    ],
  });

const makeFooter = (meta, C) =>
  new Footer({
    children: [
      new Paragraph({
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: C.RULE, space: 2 } },
        alignment: AlignmentType.RIGHT,
        spacing: { before: 100, after: 0 },
        children: [E.run(`© ${meta.author || ""}  |  본 원고는 저작권법에 의해 보호됩니다`, { size: 18, color: C.GRAY3 }, C)],
      }),
    ],
  });

// ─────────────────────────────────────────────
// 요소 타입 → docx 객체 변환
// ─────────────────────────────────────────────

/**
 * 단일 요소 객체를 받아 docx Paragraph/Table 배열 반환
 * @param {Object} el    JSON 요소
 * @param {Object} C     템플릿 색상
 * @param {string} imgBaseDir 이미지 기본 경로
 * @returns {Array}
 */
const convertElement = (el, C, imgBaseDir) => {
  const path = require("path");

  switch (el.type) {

    case "chapter_title":
      return E.chapterTitle(el.phase || "", el.text || "", el.sub || "", C);

    case "h1":
      return [E.h1(el.num || "", el.text || "", C), E.empty(40)];

    case "h2":
      return [E.h2(el.text || "", C), E.empty(20)];

    case "h3":
      return [E.h3(el.text || "", C), E.empty(10)];

    case "body":
      return [E.bodyText(el.text || "", el.indent || 0, C), E.empty(20)];

    case "quote":
      return [E.quoteBox(el.text || "", C), E.empty(20)];

    case "insight":
      return [E.insightBox(el.text || "", C), E.empty(20)];

    case "tip":
      return [E.tipBox(el.text || "", C), E.empty(20)];

    case "warning":
      return [E.warningBox(el.text || "", C), E.empty(20)];

    case "qa":
      return E.qaBlock(el.question || "", el.answers || [], C);

    case "prompt":
      return E.promptBox(el.label || "", el.text || "", C);

    case "conclusion":
      return E.conclusionBox(el.lines || [], C);

    case "bullets":
      return [...E.bulletList(el.items || [], C), E.empty(40)];

    case "image": {
      const imgPath = path.join(imgBaseDir, el.filename || "");
      return [
        ...E.imgReal(imgPath, el.width_emu || 0, el.height_emu || 0, el.caption || ""),
        E.empty(20),
      ];
    }

    case "image_placeholder":
      return [...E.imgPlaceholder(el.caption || ""), E.empty(20)];

    case "table2":
      return [
        E.table2col(el.col1 || "", el.col2 || "", el.rows || [], C),
        E.empty(60),
      ];

    case "table3":
      return [
        E.table3col(el.headers || [], el.rows || [], C),
        E.empty(60),
      ];

    case "hr":
      return [E.hrPara(C.RULE, el.size || 4), E.empty(40)];

    case "empty":
      return [E.empty(el.height || 120)];

    default:
      // 알 수 없는 타입은 본문으로 처리
      if (el.text) return [E.bodyText(el.text, 0, C)];
      return [];
  }
};

// ─────────────────────────────────────────────
// 메인 빌더
// ─────────────────────────────────────────────

/**
 * JSON 데이터로 Document 객체 생성
 *
 * @param {Object} data        파싱된 JSON 객체
 * @param {Object} C           템플릿 색상 객체
 * @returns {Document}
 */
const build = (data, C) => {
  const imgBaseDir = data.image_base_dir || "./temp/images/";
  const meta = data.meta || {};
  const settings = data.custom_settings || {};

  // 1. 사용자 설정 객체 C 에 병합 (기본 속성 덮어쓰기)
  if (settings.h_font) C.H_FONT = settings.h_font;
  if (settings.b_font) C.FONT = settings.b_font;
  if (settings.base_size) {
    const s = parseInt(settings.base_size, 10);
    C.SIZE_BODY = s;
    C.SIZE_H1 = s + 8;
    C.SIZE_H2 = s + 4;
    C.SIZE_H3 = s + 2;
    // 다른 요소들이 size를 명시적으로 쓰지 않는 경우 fallback
    C.BASE_SIZE = s;
  }
  if (settings.line_spacing) {
    const spc = parseFloat(settings.line_spacing);
    // line: 240이 single spacing 이므로, 1.5면 360
    C.LINE_SPACING = Math.round(spc * 240);
  } else {
    C.LINE_SPACING = 276; // 기본 1.15
  }
  if (settings.justify !== undefined) {
    C.JUSTIFY = settings.justify;
  }

  // 2. 전체 요소 → docx 객체 배열 (flat)
  const children = [];
  children.push(E.empty(200));

  for (const el of (data.elements || [])) {
    const converted = convertElement(el, C, imgBaseDir);
    children.push(...converted);
  }

  children.push(E.empty(200));

  return new Document({
    numbering: makeNumbering(C),
    styles: {
      default: {
        document: { run: { font: C.FONT || "Arial", size: 22, color: C.TEXT } },
      },
    },
    sections: [
      {
        properties: {
          page: {
            size: { width: 11906, height: 16838 },       // A4
            margin: (() => {
              if (settings.margins === "wide") return { top: 2160, right: 2160, bottom: 2160, left: 2160 };
              if (settings.margins === "narrow") return { top: 1080, right: 1080, bottom: 1080, left: 1080 };
              // default 여백 처리 (템플릿 타입 기반 혹은 1440 등)
              return {
                top: C.TYPE === "MINIMAL" ? 1800 : 1260,
                right: C.TYPE === "MINIMAL" ? 1800 : 1260,
                bottom: C.TYPE === "MINIMAL" ? 1800 : 1260,
                left: C.TYPE === "MINIMAL" ? 1800 : 1440
              };
            })(),
          },
        },
        headers: { default: makeHeader(meta, C) },
        footers: { default: makeFooter(meta, C) },
        children,
      },
    ],
  });
};

module.exports = { build };
