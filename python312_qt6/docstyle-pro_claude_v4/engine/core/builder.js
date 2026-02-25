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
  TableOfContents, PageNumber, SectionType, Table, TableRow, TableCell, WidthType,
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

const _SENTENCE_SPLIT_RE = /(?<=[.!?。！？])\s+/;

const _AUTO_POLISH_PROFILES = {
  weak: {
    minElements: 8,
    textRatioMin: 0.80,
    heavyRatioMax: 0.12,
    splitMinChars: 680,
    leadMinChars: 110,
    firstChunkChars: 280,
    insertDividerFromNthH1: 2,
  },
  normal: {
    minElements: 6,
    textRatioMin: 0.72,
    heavyRatioMax: 0.18,
    splitMinChars: 520,
    leadMinChars: 70,
    firstChunkChars: 220,
    insertDividerFromNthH1: 1,
  },
  strong: {
    minElements: 5,
    textRatioMin: 0.65,
    heavyRatioMax: 0.24,
    splitMinChars: 380,
    leadMinChars: 45,
    firstChunkChars: 170,
    insertDividerFromNthH1: 1,
  },
};

const _STYLE_PRESETS = {
  template: {},
  classic: {
    SIZE_BODY: 21, SIZE_H1: 34, SIZE_H2: 28, SIZE_H3: 24,
    LINE_SPACING: 420, JUSTIFY: true,
    BODY_BEFORE: 140, BODY_AFTER: 180,
    H1_BEFORE: 520, H1_AFTER: 140,
    H2_BEFORE: 380, H2_AFTER: 120,
    H3_BEFORE: 260, H3_AFTER: 90,
    LEAD_BEFORE: 210, LEAD_AFTER: 210,
  },
  modern: {
    SIZE_BODY: 20, SIZE_H1: 32, SIZE_H2: 26, SIZE_H3: 22,
    LINE_SPACING: 384, JUSTIFY: false,
    BODY_BEFORE: 100, BODY_AFTER: 150,
    H1_BEFORE: 420, H1_AFTER: 110,
    H2_BEFORE: 300, H2_AFTER: 90,
    H3_BEFORE: 220, H3_AFTER: 70,
    LEAD_BEFORE: 170, LEAD_AFTER: 170,
  },
  report: {
    SIZE_BODY: 19, SIZE_H1: 30, SIZE_H2: 24, SIZE_H3: 21,
    LINE_SPACING: 360, JUSTIFY: false,
    BODY_BEFORE: 90, BODY_AFTER: 130,
    H1_BEFORE: 360, H1_AFTER: 100,
    H2_BEFORE: 260, H2_AFTER: 80,
    H3_BEFORE: 200, H3_AFTER: 60,
    LEAD_BEFORE: 150, LEAD_AFTER: 150,
  },
  magazine: {
    SIZE_BODY: 21, SIZE_H1: 36, SIZE_H2: 30, SIZE_H3: 24,
    LINE_SPACING: 408, JUSTIFY: true,
    BODY_BEFORE: 150, BODY_AFTER: 200,
    H1_BEFORE: 560, H1_AFTER: 150,
    H2_BEFORE: 420, H2_AFTER: 130,
    H3_BEFORE: 280, H3_AFTER: 100,
    LEAD_BEFORE: 240, LEAD_AFTER: 220,
  },
};

const applyStylePreset = (C, presetKey) => {
  const key = String(presetKey || "template").toLowerCase();
  const preset = _STYLE_PRESETS[key] || _STYLE_PRESETS.template;
  Object.assign(C, preset);
};

const resolveAutoPolishLevel = (settings) => {
  const raw = String(settings.auto_polish_level || "normal").toLowerCase();
  if (raw === "off") return "off";
  if (raw === "weak") return "weak";
  if (raw === "strong") return "strong";
  return "normal";
};

const isAutoPolishEnabled = (settings) => {
  if (settings.auto_polish === false || settings.auto_polish === "false") return false;
  return resolveAutoPolishLevel(settings) !== "off";
};

const splitLongBodyText = (text, profile) => {
  const src = (text || "").trim();
  if (!src) return ["", ""];
  if (src.length < profile.splitMinChars) return [src, ""];

  const sentences = src.split(_SENTENCE_SPLIT_RE).filter(Boolean);
  if (sentences.length < 2) {
    const mid = Math.floor(src.length / 2);
    return [src.slice(0, mid).trim(), src.slice(mid).trim()];
  }

  let first = "";
  let idx = 0;
  while (idx < sentences.length && first.length < profile.firstChunkChars) {
    first = `${first}${first ? " " : ""}${sentences[idx]}`;
    idx += 1;
  }
  const second = sentences.slice(idx).join(" ").trim();
  return [first.trim(), second];
};

const isTextHeavyDocument = (elements, profile) => {
  if (!Array.isArray(elements) || elements.length < profile.minElements) return false;

  const textTypes = new Set(["h1", "h2", "h3", "body", "quote", "bullets", "hr", "empty"]);
  const heavyTypes = new Set(["image", "table2", "table3", "qa", "prompt", "conclusion"]);

  let textCount = 0;
  let heavyCount = 0;

  for (const el of elements) {
    if (!el || typeof el !== "object") continue;
    if (textTypes.has(el.type)) textCount += 1;
    if (heavyTypes.has(el.type)) heavyCount += 1;
  }

  return (textCount / elements.length) >= profile.textRatioMin
    && heavyCount <= Math.max(2, Math.floor(elements.length * profile.heavyRatioMax));
};

const autoPolishElements = (elements, profile) => {
  const polished = [];
  let h1Count = 0;
  let justSawHeading = false;

  for (const el of elements) {
    if (!el || typeof el !== "object") continue;

    if (el.type === "h1") {
      if (h1Count >= profile.insertDividerFromNthH1) {
        polished.push({ type: "section_divider", text: el.text || "" });
      }
      polished.push(el);
      h1Count += 1;
      justSawHeading = true;
      continue;
    }

    if (el.type === "h2" || el.type === "h3") {
      polished.push(el);
      justSawHeading = true;
      continue;
    }

    if (el.type === "body") {
      const text = (el.text || "").trim();
      if (!text) {
        justSawHeading = false;
        continue;
      }

      if (justSawHeading && text.length >= profile.leadMinChars) {
        const [leadText, remainder] = splitLongBodyText(text, profile);
        polished.push({ ...el, type: "lead", text: leadText || text });
        if (remainder) polished.push({ ...el, type: "body", text: remainder });
      } else if (text.length >= profile.splitMinChars) {
        const [firstHalf, secondHalf] = splitLongBodyText(text, profile);
        polished.push({ ...el, text: firstHalf || text });
        if (secondHalf) polished.push({ ...el, text: secondHalf });
      } else {
        polished.push(el);
      }

      justSawHeading = false;
      continue;
    }

    polished.push(el);
    justSawHeading = false;
  }

  return polished;
};

// ─────────────────────────────────────────────
// Header / Footer 공통 생성
// ─────────────────────────────────────────────
const makeHeader = (meta, C) => {
  const leftText = meta.header_text ? meta.header_text : `${meta.title || ""}    `;
  const rightText = meta.header_text ? "" : (meta.chapter || "");
  const barTextColor = C.WHITE || "FFFFFF";

  // 데코레이션: 상단 컬러 바 (템플릿 BG_HEAD 색상)
  const topBar = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE }, insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE } },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            shading: { fill: C.BG_HEAD, type: ShadingType.CLEAR },
            margins: { left: 260, right: 260, top: 120, bottom: 120 },
            children: [
              new Paragraph({
                spacing: { before: 0, after: 40 },
                children: [E.run("__________", { size: 16, color: barTextColor, bold: true }, C)],
              }),
              new Paragraph({
                spacing: { before: 0, after: 0 },
                children: [E.run("____", { size: 16, color: barTextColor, bold: true }, C)],
              }),
            ],
          }),
        ],
      }),
    ],
  });

  return new Header({
    children: [
      topBar,
      new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.RULE, space: 2 } },
        spacing: { before: 40, after: 100 },
        children: [
          E.run(leftText, { size: 18, color: C.GRAY3 }, C),
          E.run(rightText, { size: 18, color: C.BLUE, bold: true }, C),
        ],
      }),
    ],
  });
};

const makeFooter = (meta, C) => {
  const footerChildren = [];
  const copyrightText = E.run(`© ${meta.author || ""}  |  본 원고는 저작권법에 의해 보호됩니다`, { size: 18, color: C.GRAY3 }, C);
  const showPageNum = meta.page_numbers !== false;

  // 데코레이션: 하단 컬러 바 (ACCENT 색상)
  const bottomBar = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE }, insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE } },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            shading: { fill: C.ACCENT, type: ShadingType.CLEAR },
            margins: { left: 0, right: 0, top: 80, bottom: 80 },
            children: [new Paragraph({ children: [E.run(" ", { size: 2, color: C.ACCENT }, C)] })],
          }),
        ],
      }),
    ],
  });

  if (showPageNum) {
    footerChildren.push(
      new Paragraph({
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: C.RULE, space: 2 } },
        alignment: AlignmentType.CENTER,
        spacing: { before: 100, after: 0 },
        children: [
          new TextRun({
            children: ["-  ", PageNumber.CURRENT, "  -"],
            color: C.DARK,
            size: 18,
            font: C.FONT || "Arial"
          })
        ]
      })
    );
  }

  footerChildren.push(
    new Paragraph({
      border: showPageNum ? undefined : { top: { style: BorderStyle.SINGLE, size: 4, color: C.RULE, space: 2 } },
      alignment: AlignmentType.RIGHT,
      spacing: { before: showPageNum ? 40 : 100, after: 0 },
      children: [copyrightText],
    })
  );

  // 하단 데코레이션 바 추가
  footerChildren.push(bottomBar);

  return new Footer({ children: footerChildren });
};

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

    case "lead":
      return [E.leadParagraph(el.text || "", C), E.empty(20)];

    case "quote":
      return [E.quoteBox(el.text || "", C), E.empty(20)];

    case "insight":
      if (C.TYPE === "TECH") return [...E.terminalBox(el.text || "", C), E.empty(20)];
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

    case "section_divider":
      return [E.sectionDivider(el.text || "", C), E.empty(60)];

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

  applyStylePreset(C, settings.style_preset || "template");

  // 1. 사용자 설정 객체 C 에 병합 (기본 속성 덮어쓰기)
  if (settings.h_font) C.H_FONT = settings.h_font;
  if (settings.b_font) C.FONT = settings.b_font;
  if (settings.base_size) {
    const s = parseInt(settings.base_size, 10);
    C.SIZE_BODY = s;
    C.SIZE_H1 = s + 8;
    C.SIZE_H2 = s + 4;
    C.SIZE_H3 = s + 2;
    C.BASE_SIZE = s;
  }
  if (settings.line_spacing) {
    C.LINE_SPACING = Math.round(parseFloat(settings.line_spacing) * 240);
  } else if (!C.LINE_SPACING) {
    C.LINE_SPACING = 384;
  }
  if (settings.justify !== undefined) C.JUSTIFY = settings.justify;

  const isMinimal = C.TYPE === "MINIMAL";
  const isEditorial = C.TYPE === "EDITORIAL";
  const autoPolishEnabled = isAutoPolishEnabled(settings);
  const autoPolishLevel = resolveAutoPolishLevel(settings);
  const autoPolishProfile = _AUTO_POLISH_PROFILES[autoPolishLevel] || _AUTO_POLISH_PROFILES.normal;
  const sourceElements = (autoPolishEnabled && isTextHeavyDocument(data.elements || [], autoPolishProfile))
    ? autoPolishElements(data.elements || [], autoPolishProfile)
    : (data.elements || []);

  // 2. Cover / Header Elements (Full Width)
  const coverElements = [];
  if (meta.title || meta.subtitle || meta.author) {
    coverElements.push(...E.coverPage(meta.title, meta.subtitle, meta.author, C));
  }

  // 3. Table of Contents
  const tocElements = [];
  if (meta.auto_toc) {
    tocElements.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 240, after: 240 },
        children: [E.run("차례", { size: 36, bold: true, color: C.DARK }, C)],
      }),
      new TableOfContents(" ", {
        hyperlink: true,
        headingStyleRange: "1-3",
        stylesWithLevels: [
          new String("Heading 1"), 1,
          new String("Heading 2"), 2,
          new String("Heading 3"), 3,
        ],
      }),
      E.empty(200),
      new Paragraph({ children: [E.run("", { break: 1 }, C)] })
    );
  }

  // 4. 전체 요소 → docx 객체 배열 (Header vs Body)
  const mainHeaderItems = [E.empty(100)];
  const mainBodyItems = [];
  let reachedChapterBody = false;

  for (const el of sourceElements) {
    const converted = convertElement(el, C, imgBaseDir);

    if (isEditorial && !reachedChapterBody) {
      mainHeaderItems.push(...converted);
      if (el.type === "chapter_title") reachedChapterBody = true;
    } else {
      (isEditorial ? mainBodyItems : mainHeaderItems).push(...converted);
    }
  }
  mainBodyItems.push(E.empty(200));

  const commonPageProps = {
    size: { width: 11906, height: 16838 }, // A4
    margin: (() => {
      if (settings.margins === "wide") return { top: 2160, right: 2160, bottom: 2160, left: 2160 };
      if (settings.margins === "narrow") return { top: 1080, right: 1080, bottom: 1080, left: 1080 };
      if (isMinimal) return { top: 1800, right: 2000, bottom: 1800, left: 2000 };
      if (isEditorial) return { top: 1080, right: 1080, bottom: 1440, left: 1080 };
      return { top: 1260, right: 1260, bottom: 1260, left: 1440 };
    })(),
  };

  const sections = [];
  if (isEditorial) {
    // 1단 섹션 (Cover + TOC + Chapter Header)
    sections.push({
      properties: { page: commonPageProps, type: SectionType.CONTINUOUS },
      headers: { default: makeHeader(meta, C) },
      footers: { default: makeFooter(meta, C) },
      children: [...coverElements, ...tocElements, ...mainHeaderItems],
    });
    // 2단 섹션 (본문)
    sections.push({
      properties: {
        page: { ...commonPageProps, cols: { count: 2, space: 720 } },
      },
      headers: { default: makeHeader(meta, C) },
      footers: { default: makeFooter(meta, C) },
      children: mainBodyItems,
    });
  } else {
    sections.push({
      properties: { page: commonPageProps },
      headers: { default: makeHeader(meta, C) },
      footers: { default: makeFooter(meta, C) },
      children: [...coverElements, ...tocElements, ...mainHeaderItems, ...mainBodyItems],
    });
  }

  return new Document({
    numbering: makeNumbering(C),
    styles: {
      default: {
        document: {
          run: { font: C.FONT || "Arial", size: C.SIZE_BODY || 20, color: C.TEXT },
          paragraph: { alignment: isMinimal ? AlignmentType.CENTER : (C.JUSTIFY ? AlignmentType.JUSTIFY : AlignmentType.LEFT) }
        }
      },
    },
    sections: sections,
  });
};

module.exports = { build };
