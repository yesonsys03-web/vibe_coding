/**
 * layout.js — 페이지 레이아웃 · 헤더 · 푸터 공통 설정
 * buildDocument() 가 Document 객체를 반환한다.
 */

const {
  Document, Header, Footer, Paragraph, TextRun,
  BorderStyle, AlignmentType, LevelFormat,
} = require('docx');

const thin = (c) => ({ style: BorderStyle.SINGLE, size: 4, color: c });

function buildDocument(T, meta, children) {
  const chapterName = meta.title || "";
  const author      = meta.author || "";

  return new Document({
    numbering: {
      config: [{
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "▸",
          alignment: AlignmentType.LEFT,
          style: {
            paragraph: { indent: { left: 480, hanging: 240 } },
            run: { font: "Arial", color: T.BLUE2 },
          },
        }],
      }],
    },
    styles: {
      default: {
        document: { run: { font: T.FONT || "Arial", size: 22, color: T.DARK } },
      },
    },
    sections: [{
      properties: {
        page: {
          size: { width: 11906, height: 16838 },  // A4
          margin: { top: 1260, right: 1260, bottom: 1260, left: 1440 },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              border: { bottom: thin(T.RULE), top: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
              spacing: { before: 0, after: 100 },
              children: [
                new TextRun({ text: `${author}    `, font: T.FONT || "Arial", size: 18, color: T.GRAY3 }),
                new TextRun({ text: chapterName,    font: T.FONT || "Arial", size: 18, color: T.H2_COLOR, bold: true }),
              ],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              border: { top: thin(T.RULE), bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
              alignment: AlignmentType.RIGHT,
              spacing: { before: 100, after: 0 },
              children: [
                new TextRun({
                  text: author ? `© ${author}  |  본 원고는 저작권법에 의해 보호됩니다` : "© All rights reserved",
                  font: T.FONT || "Arial", size: 18, color: T.GRAY3,
                }),
              ],
            }),
          ],
        }),
      },
      children,
    }],
  });
}

module.exports = { buildDocument };
