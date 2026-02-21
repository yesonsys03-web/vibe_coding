/**
 * base_builder.js — 10개 템플릿이 공유하는 문서 빌드 로직
 * 각 템플릿은 THEME 객체만 바꿔서 build() 를 호출한다.
 */

const EL     = require('../core/elements');
const LAYOUT = require('../core/layout');

function build(THEME, parsed) {
  const children = [];

  // 시작 여백
  children.push(EL.empty(200));

  for (const block of parsed.content) {
    switch (block.type) {

      case 'chapter_header':
        children.push(...EL.chapterTitle(
          THEME,
          block.phase    || '',
          block.title    || '',
          block.subtitle || ''
        ));
        break;

      case 'h1':
        children.push(EL.h1(THEME, block.number || '', block.text));
        children.push(EL.empty(60));
        break;

      case 'h2':
        children.push(EL.h2(THEME, block.text));
        children.push(EL.empty(40));
        break;

      case 'h3':
        children.push(EL.h3(THEME, block.text));
        break;

      case 'body':
        children.push(EL.body(THEME, block.text));
        break;

      case 'quote_box':
        children.push(EL.quoteBox(THEME, block.text));
        break;

      case 'insight_box':
        children.push(EL.insightBox(THEME, block.text));
        break;

      case 'tip_box':
        children.push(EL.tipBox(THEME, block.text));
        break;

      case 'caution_box':
        children.push(EL.cautionBox(THEME, block.text));
        break;

      case 'warning_box':
        children.push(EL.warningBox(THEME, block.text));
        break;

      case 'conclusion_box':
        children.push(EL.conclusionBox(THEME, block.text));
        break;

      case 'qa_block':
        children.push(...EL.qaBlock(THEME, block.question, block.answers || []));
        break;

      case 'bullet':
        children.push(EL.bulletItem(THEME, block.text));
        break;

      case 'image_ref':
        // 실제 이미지는 Python image_injector.py 가 사후 삽입
        // 마커 텍스트를 플레이스홀더로 남겨둔다
        children.push(...EL.imagePlaceholder(THEME, block.image_id || 'img', block.caption || ''));
        break;

      case 'table':
        children.push(EL.buildTable(
          THEME,
          block.headers || [],
          block.rows    || [],
          block.colWidths || null
        ));
        children.push(EL.empty(80));
        break;

      case 'hr':
        children.push(EL.hrLine(THEME.RULE, 4));
        break;

      case 'empty':
        children.push(EL.empty(block.height || 120));
        break;

      default:
        // 알 수 없는 블록 타입 → 본문으로 처리
        if (block.text) {
          children.push(EL.body(THEME, block.text));
        }
        break;
    }
  }

  return LAYOUT.buildDocument(THEME, parsed.meta || {}, children);
}

module.exports = { build };
