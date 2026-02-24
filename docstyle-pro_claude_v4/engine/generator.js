/**
 * generator.js — Node.js 엔진 CLI 진입점
 *
 * 사용법:
 *   node generator.js <parsed_json_path> <template_id> <output_docx_path>
 *
 * 예시:
 *   node generator.js ../temp/parsed.json 1 ../temp/output_raw.docx
 */

'use strict';

const fs   = require('fs');
const path = require('path');
const { Packer } = require('docx');

// ── 인수 파싱 ────────────────────────────────────────────
const [,, jsonPath, templateId, outputPath] = process.argv;

if (!jsonPath || !templateId || !outputPath) {
  console.error('[ERROR] Usage: node generator.js <parsed.json> <template_id> <output.docx>');
  process.exit(1);
}

if (!fs.existsSync(jsonPath)) {
  console.error(`[ERROR] parsed.json not found: ${jsonPath}`);
  process.exit(1);
}

// ── 템플릿 맵 ────────────────────────────────────────────
const TEMPLATE_MAP = {
  '1':  './templates/t01_template',
  '2':  './templates/t02_template',
  '3':  './templates/t03_template',
  '4':  './templates/t04_template',
  '5':  './templates/t05_template',
  '6':  './templates/t06_template',
  '7':  './templates/t07_template',
  '8':  './templates/t08_template',
  '9':  './templates/t09_template',
  '10': './templates/t10_template',
};

const templateModule = TEMPLATE_MAP[String(templateId)];
if (!templateModule) {
  console.error(`[ERROR] Unknown template ID: ${templateId}. Valid: 1-10`);
  process.exit(1);
}

// ── 실행 ─────────────────────────────────────────────────
try {
  const parsed   = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
  const template = require(templateModule);
  const doc      = template.build(parsed);

  Packer.toBuffer(doc).then(buffer => {
    const outDir = path.dirname(outputPath);
    if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
    fs.writeFileSync(outputPath, buffer);
    console.log(`[OK] Template ${templateId} → ${outputPath}`);
  }).catch(err => {
    console.error('[ERROR] Packer failed:', err.message);
    process.exit(1);
  });

} catch (err) {
  console.error('[ERROR]', err.message);
  process.exit(1);
}
