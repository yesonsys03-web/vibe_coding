/**
 * elements.js — DocStyle Pro 공통 요소 생성 함수 라이브러리
 *
 * 모든 템플릿은 이 파일의 함수만 사용한다.
 * 템플릿별 중복 코드를 금지하고 색상(C)만 교체하여 스타일을 변환한다.
 */

"use strict";

const {
  Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, BorderStyle, WidthType, ShadingType, VerticalAlign,
  LevelFormat,
} = require("docx");
const fs = require("fs");
const path = require("path");

// ─────────────────────────────────────────────
// 상수
// ─────────────────────────────────────────────
const PAGE_CONTENT_WIDTH = 9026;
const MAX_IMG_EMU_W = 6096000;

// ─────────────────────────────────────────────
// 유틸리티
// ─────────────────────────────────────────────
const noBdr = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const solidBdr = (color, size = 2) => ({ style: BorderStyle.SINGLE, size, color });
const thickBdr = (color, size = 20) => ({ style: BorderStyle.THICK, size, color });

// ─────────────────────────────────────────────
// 기본 빌딩 블록
// ─────────────────────────────────────────────
const run = (text, opts = {}, C) => new TextRun({
  text,
  font: C && C.FONT ? C.FONT : "Arial",
  ...opts
});
const para = (children, opts = {}) =>
  new Paragraph({ children: Array.isArray(children) ? children : [children], ...opts });
const empty = (h = 120) => new Paragraph({ spacing: { before: 0, after: h }, children: [] });
const hrPara = (color, sz = 4) =>
  new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: sz, color, space: 1 } },
    spacing: { before: 80, after: 80 },
    children: [],
  });

// ─────────────────────────────────────────────
// 텍스트 요소
// ─────────────────────────────────────────────
const bodyText = (text, indent = 0, C) => {
  const isMinimal = C.TYPE === "MINIMAL";
  const align = C.JUSTIFY ? AlignmentType.JUSTIFY : AlignmentType.LEFT;
  return new Paragraph({
    spacing: { before: isMinimal ? 60 : 120, after: isMinimal ? 80 : 160, line: C.LINE_SPACING || 360 },
    indent: { left: indent },
    alignment: align,
    children: [run(text, { size: C.SIZE_BODY || 20, color: C.TEXT }, C)],
  });
};

const caption = (text, C) =>
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 30, after: 100 },
    children: [run(text, { size: 18, color: C.GRAY2, italics: true }, C)],
  });

// ─────────────────────────────────────────────
// 헤딩 요소
// ─────────────────────────────────────────────
const chapterTitle = (phase, title, sub, C) => {
  const isMinimal = C.TYPE === "MINIMAL";
  const isNordic = C.NAME === "Nordic Blue";

  if (isMinimal) {
    return [
      empty(400),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [run(title, { bold: true, size: 48, color: C.DARK }, C)],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [run(sub, { size: 24, color: C.GRAY, italics: true }, C)],
      }),
      empty(600),
    ];
  }

  // Nordic Blue: Add a small accent circle/point logic effectively via a leading bullet or special run
  // Note: True circles are hard in docx-js without VML/Drawing, so we use a large bullet character
  const mainChildren = [run(title, { bold: true, size: 34, color: C.WHITE }, C)];
  if (isNordic) {
    mainChildren.unshift(run("●  ", { size: 24, color: C.ACCENT }, C));
  }

  return [
    new Paragraph({
      shading: { fill: C.BG_HEAD, type: ShadingType.CLEAR },
      spacing: { before: isNordic ? 400 : 0, after: 0 },
      indent: { left: 240, right: 240 },
      border: { bottom: thickBdr(C.ACCENT, 12), top: noBdr, left: noBdr, right: noBdr },
      children: [run(phase || "", { size: 20, color: C.BLUE2, bold: true }, C)],
    }),
    new Paragraph({
      shading: { fill: C.BG_HEAD, type: ShadingType.CLEAR },
      spacing: { before: 0, after: 40 },
      indent: { left: 240, right: 240 },
      children: mainChildren,
    }),
    new Paragraph({
      shading: { fill: C.BG_HEAD, type: ShadingType.CLEAR },
      spacing: { before: 0, after: 160 },
      indent: { left: 240, right: 240 },
      children: [run(sub || "", { size: 20, color: C.GRAY3, italics: true }, C)],
    }),
    empty(100),
  ];
};

const h1 = (num, title, C) => {
  const isNordic = C.NAME === "Nordic Blue";
  const accentColor = isNordic ? C.ACCENT : C.ACCENT; // Could vary if needed

  return new Paragraph({
    spacing: { before: 480, after: 120 },
    border: {
      bottom: { style: BorderStyle.SINGLE, size: 2, color: C.RULE, space: 12 },
      left: isNordic ? { style: BorderStyle.SINGLE, size: 24, color: C.ACCENT, space: 12 } : noBdr,
      top: noBdr,
      right: noBdr,
    },
    indent: { left: isNordic ? 400 : 0 },
    children: [
      run(`${num}.  `, { font: C.H_FONT || C.FONT || "Arial", bold: true, size: C.SIZE_H1 || 32, color: C.ACCENT }, C),
      run(title, { font: C.H_FONT || C.FONT || "Arial", bold: true, size: C.SIZE_H1 || 32, color: C.DARK }, C),
    ],
  });
};

const h2 = (text, C) => {
  const isNordic = C.NAME === "Nordic Blue";
  return new Paragraph({
    spacing: { before: 360, after: 100 },
    border: { bottom: noBdr },
    children: [
      isNordic ? run("•  ", { color: C.ACCENT, bold: true }, C) : run(""),
      run(text, { font: C.H_FONT || C.FONT || "Arial", bold: true, size: C.SIZE_H2 || 26, color: C.BLUE2 }, C)
    ],
  });
};

const h3 = (text, C) =>
  new Paragraph({
    spacing: { before: 240, after: 80 },
    children: [run(text, { font: C.H_FONT || C.FONT || "Arial", bold: true, size: C.SIZE_H3 || 22, color: C.DARK }, C)],
  });

const coverPage = (title, subtitle, author, C) => {
  const elements = [empty(1200)]; // Push down to middle of page

  if (title) {
    elements.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 240 },
        children: [run(title, { font: C.H_FONT || C.FONT || "Arial", bold: true, size: 56, color: C.DARK }, C)],
      })
    );
  }

  if (subtitle) {
    elements.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 800 },
        children: [run(subtitle, { font: C.FONT || "Arial", size: 28, color: C.GRAY, italics: true }, C)],
      })
    );
  }

  if (author) {
    elements.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 800, after: 0 },
        children: [run(author, { font: C.FONT || "Arial", size: 24, color: C.GRAY3 }, C)],
      })
    );
  }

  // Page break after cover
  if (elements.length > 1) { // If it's not just the empty spacer
    elements[elements.length - 1].addChildElement(run("", { break: 1 }, C));
  }

  return elements;
};

// ─────────────────────────────────────────────
// 박스 요소
// ─────────────────────────────────────────────
const quoteBox = (text, C) =>
  new Paragraph({
    shading: { fill: C.BG_LIGHT || "F8FAFC", type: ShadingType.CLEAR },
    border: { left: { style: BorderStyle.SINGLE, size: 8, color: C.BOX_BORDER, space: 12 }, top: noBdr, bottom: noBdr, right: noBdr },
    spacing: { before: 160, after: 160 },
    indent: { left: 280, right: 240 },
    children: [run(text, { size: 20, color: C.GRAY, italics: true }, C)],
  });

const insightBox = (text, C) =>
  new Paragraph({
    shading: { fill: C.BG_RED || "FEF2F2", type: ShadingType.CLEAR },
    border: { left: { style: BorderStyle.SINGLE, size: 8, color: C.ACCENT, space: 12 }, top: noBdr, bottom: noBdr, right: noBdr },
    spacing: { before: 160, after: 160 },
    indent: { left: 280, right: 240 },
    children: [run(text, { size: 20, color: C.DARK, bold: true }, C)],
  });

const tipBox = (text, C) =>
  new Paragraph({
    shading: { fill: C.BG_GREEN || "F0FDF4", type: ShadingType.CLEAR },
    border: { left: { style: BorderStyle.SINGLE, size: 8, color: C.GREEN, space: 12 }, top: noBdr, bottom: noBdr, right: noBdr },
    spacing: { before: 120, after: 120 },
    indent: { left: 280, right: 240 },
    children: [
      run("Tip  ", { bold: true, size: 20, color: C.GREEN }, C),
      run(text, { size: 20, color: C.DARK }, C),
    ],
  });

const warningBox = (text, C) =>
  new Paragraph({
    shading: { fill: C.BG_AMBER || "FFFBEB", type: ShadingType.CLEAR },
    border: { left: { style: BorderStyle.SINGLE, size: 8, color: C.AMBER, space: 12 }, top: noBdr, bottom: noBdr, right: noBdr },
    spacing: { before: 120, after: 120 },
    indent: { left: 280, right: 240 },
    children: [
      run("주의  ", { bold: true, size: 20, color: C.AMBER }, C),
      run(text, { size: 20, color: C.DARK }, C),
    ],
  });

const qaBlock = (q, answers, C) => [
  new Paragraph({
    shading: { fill: C.BG_HEAD, type: ShadingType.CLEAR },
    border: { top: solidBdr(C.BLUE2), bottom: noBdr, left: noBdr, right: noBdr },
    spacing: { before: 160, after: 0 },
    indent: { left: 240, right: 240 },
    children: [
      run("Q  ", { bold: true, size: 20, color: C.BLUE2 }, C),
      run(q, { size: 20, color: C.WHITE, italics: true }, C),
    ],
  }),
  ...answers.map((t) =>
    new Paragraph({
      shading: { fill: C.BG_BOX, type: ShadingType.CLEAR },
      border: { top: noBdr, bottom: noBdr, left: solidBdr(C.BOX_BORDER), right: solidBdr(C.BOX_BORDER) },
      spacing: { before: 50, after: 40 },
      indent: { left: 360, right: 240 },
      children: [run(t, { size: 20, color: C.GRAY }, C)],
    })
  ),
  new Paragraph({
    shading: { fill: C.BG_BOX, type: ShadingType.CLEAR },
    border: { top: noBdr, bottom: solidBdr(C.BOX_BORDER), left: solidBdr(C.BOX_BORDER), right: solidBdr(C.BOX_BORDER) },
    spacing: { before: 0, after: 120 },
    children: [],
  }),
  empty(40),
];

const promptBox = (label, prompt, C) => [
  new Paragraph({
    shading: { fill: C.BG_HEAD, type: ShadingType.CLEAR },
    border: { top: solidBdr(C.BLUE2), bottom: noBdr, left: noBdr, right: noBdr },
    spacing: { before: 160, after: 0 },
    indent: { left: 240, right: 240 },
    children: [
      run("🔑  ", { size: 20 }, C),
      run("골든 프롬프트  ", { bold: true, size: 20, color: C.BLUE2 }, C),
      run(label, { size: 18, color: C.GRAY3 }, C),
    ],
  }),
  new Paragraph({
    shading: { fill: C.BG_HEAD, type: ShadingType.CLEAR },
    border: { top: noBdr, bottom: solidBdr(C.BLUE2), left: noBdr, right: noBdr },
    spacing: { before: 60, after: 0 },
    indent: { left: 280, right: 240 },
    children: [run(prompt, { size: 20, color: C.GRAY3, italics: true }, C)],
  }),
  empty(60),
];

const conclusionBox = (lines, C) => [
  new Paragraph({
    shading: { fill: C.BG_HEAD, type: ShadingType.CLEAR },
    border: { top: thickBdr(C.ACCENT, 12), bottom: noBdr, left: noBdr, right: noBdr },
    spacing: { before: 120, after: 0 },
    indent: { left: 240, right: 240 },
    children: [],
  }),
  ...lines.map((t) =>
    new Paragraph({
      shading: { fill: C.BG_HEAD, type: ShadingType.CLEAR },
      spacing: { before: 60, after: 60 },
      indent: { left: 280, right: 280 },
      children: [run(t, { size: 22, color: C.WHITE }, C)],
    })
  ),
  new Paragraph({
    shading: { fill: C.BG_HEAD, type: ShadingType.CLEAR },
    border: { top: noBdr, bottom: thickBdr(C.ACCENT, 8), left: noBdr, right: noBdr },
    spacing: { before: 0, after: 0 },
    children: [],
  }),
  empty(80),
];

// ─────────────────────────────────────────────
// 목록
// ─────────────────────────────────────────────
const bulletList = (items, C) =>
  items.map(
    (t) =>
      new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        spacing: { before: 40, after: 80, line: C.LINE_SPACING || 360 },
        alignment: C.JUSTIFY ? AlignmentType.JUSTIFY : AlignmentType.LEFT,
        children: [run(t, { size: C.SIZE_BODY || 20, color: C.TEXT }, C)],
      })
  );

// ─────────────────────────────────────────────
// 이미지
// ─────────────────────────────────────────────
const imgPlaceholder = (captionText) => [
  new Paragraph({
    shading: { fill: "F1F5F9", type: ShadingType.CLEAR },
    border: { top: solidBdr("CBD5E1"), bottom: solidBdr("CBD5E1"), left: solidBdr("CBD5E1"), right: solidBdr("CBD5E1") },
    alignment: AlignmentType.CENTER,
    spacing: { before: 100, after: 0 },
    indent: { left: 200, right: 200 },
    children: [run("[ 이미지 ]", { size: 20, color: "9CA3AF" }, { FONT: "Arial" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 30, after: 100 },
    children: [run(captionText, { size: 18, color: "6B7280", italics: true })],
  }),
];

const imgReal = (imgPath, widthEmu, heightEmu, captionText) => {
  if (!fs.existsSync(imgPath)) return imgPlaceholder(captionText);

  let w = widthEmu || MAX_IMG_EMU_W;
  let h = heightEmu || Math.round(MAX_IMG_EMU_W * 0.5);
  if (w > MAX_IMG_EMU_W) {
    const ratio = MAX_IMG_EMU_W / w;
    w = MAX_IMG_EMU_W;
    h = Math.round(h * ratio);
  }

  const ext = path.extname(imgPath).slice(1).toLowerCase();
  const typeMap = { png: "png", jpg: "jpg", jpeg: "jpg", gif: "gif", bmp: "bmp" };
  const imgType = typeMap[ext] || "png";
  const imgData = fs.readFileSync(imgPath);

  // EMU → pixel (96dpi 기준: 1px = 9144 EMU)
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 100, after: 0 },
      children: [
        new ImageRun({
          data: imgData,
          transformation: { width: Math.round(w / 9144), height: Math.round(h / 9144) },
          type: imgType,
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 30, after: 100 },
      children: [run(captionText, { size: 18, color: "6B7280", italics: true })],
    }),
  ];
};

// ─────────────────────────────────────────────
// 표
// ─────────────────────────────────────────────
const makeCell = (text, width, fill, textColor, bold = false, borders) =>
  new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders,
    shading: { fill, type: ShadingType.CLEAR },
    margins: { top: 100, bottom: 100, left: 160, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ children: [run(text, { size: 19, color: textColor, bold })] })],
  });

const table2col = (col1Header, col2Header, rows, C) => {
  const colW = [3200, 5826];
  const total = colW.reduce((a, b) => a + b, 0);
  const bdr = { top: solidBdr("D1D5DB"), bottom: solidBdr("D1D5DB"), left: solidBdr("D1D5DB"), right: solidBdr("D1D5DB") };

  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colW,
    rows: [
      new TableRow({ children: [makeCell(col1Header || "", colW[0], C.BG_HEAD, C.WHITE, true, bdr), makeCell(col2Header || "", colW[1], C.BG_HEAD, C.WHITE, true, bdr)] }),
      ...rows.map(([left, right], i) =>
        new TableRow({
          children: [
            makeCell(left || "", colW[0], i % 2 === 0 ? C.BG_BOX : "F8FAFC", C.ACCENT, true, bdr),
            makeCell(right || "", colW[1], i % 2 === 0 ? "FFFFFF" : "F8FAFC", C.DARK, false, bdr),
          ],
        })
      ),
    ],
  });
};

const table3col = (headers, rows, C) => {
  const colW = [2000, 3200, 3826];
  const total = colW.reduce((a, b) => a + b, 0);
  const bdr = { top: solidBdr("D1D5DB"), bottom: solidBdr("D1D5DB"), left: solidBdr("D1D5DB"), right: solidBdr("D1D5DB") };

  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colW,
    rows: [
      new TableRow({ children: headers.slice(0, colW.length).map((h, i) => makeCell(h, colW[i], C.BG_HEAD, C.WHITE, true, bdr)) }),
      ...rows.map((cells, ri) =>
        new TableRow({
          children: cells.slice(0, colW.length).map((cell, ci) =>
            makeCell(cell, colW[ci], ci === 0 ? C.BG_RED : ri % 2 === 0 ? "FFFFFF" : "F8FAFC", ci === 0 ? C.ACCENT : C.DARK, ci === 0, bdr)
          ),
        })
      ),
    ],
  });
};

// ─────────────────────────────────────────────
// exports
// ─────────────────────────────────────────────
module.exports = {
  PAGE_CONTENT_WIDTH, MAX_IMG_EMU_W,
  noBdr, solidBdr, thickBdr,
  run, para, empty, hrPara,
  bodyText, caption,
  chapterTitle, h1, h2, h3, coverPage,
  quoteBox, insightBox, tipBox, warningBox, qaBlock, promptBox, conclusionBox,
  bulletList,
  imgPlaceholder, imgReal,
  makeCell, table2col, table3col,
};
