/**
 * generate.js — DocStyle Pro CLI 진입점
 *
 * 사용법
 *   node generate.js <input.json> <output.docx> --template <id>
 *
 * 예시
 *   node generate.js ../temp/input.json ../temp/output.docx --template 01
 *
 * 종료 코드
 *   0 — 성공
 *   1 — 인자 오류 또는 실행 오류
 */

"use strict";

const fs = require("fs");
const path = require("path");
const { Packer } = require("docx");

const { build } = require("./core/builder");

// ─────────────────────────────────────────────
// 템플릿 레지스트리
// ─────────────────────────────────────────────
const TEMPLATE_REGISTRY = {
  // ── 기본 10종 (스타일 중심)
  "01": "./templates/template_01_classic",
  "02": "./templates/template_02_minimal",
  "03": "./templates/template_03_nordic",
  "04": "./templates/template_04_luxury",
  "05": "./templates/template_05_academic",
  "06": "./templates/template_06_tech",
  "07": "./templates/template_07_warm",
  "08": "./templates/template_08_bold",
  "09": "./templates/template_09_forest",
  "10": "./templates/template_10_royal",
  // ── 직종별 10종 (11~20)
  "11": "./templates/template_11_clinical",
  "12": "./templates/template_12_legal",
  "13": "./templates/template_13_education",
  "14": "./templates/template_14_creative",
  "15": "./templates/template_15_finance",
  "16": "./templates/template_16_realestate",
  "17": "./templates/template_17_hr",
  "18": "./templates/template_18_culinary",
  "19": "./templates/template_19_sports",
  "20": "./templates/template_20_civic",
  // ── 직종별 추가 10종 (21~30)
  "21": "./templates/template_21_startup",
  "22": "./templates/template_22_game",
  "23": "./templates/template_23_travel",
  "24": "./templates/template_24_eco",
  "25": "./templates/template_25_tech_rd",
  "26": "./templates/template_26_media",
  "27": "./templates/template_27_calm",
  "28": "./templates/template_28_bio",
  "29": "./templates/template_29_logistics",
  "30": "./templates/template_30_design",
  // ── 직종 × 문서유형 조합 20종 (31~50)
  "31": "./templates/template_31_medical_news",
  "32": "./templates/template_32_clinical_report",
  "33": "./templates/template_33_legal_report",
  "34": "./templates/template_34_legal_proposal",
  "35": "./templates/template_35_lecture_note",
  "36": "./templates/template_36_edu_proposal",
  "37": "./templates/template_37_brand_proposal",
  "38": "./templates/template_38_brand_newsletter",
  "39": "./templates/template_39_finance_report",
  "40": "./templates/template_40_investment_deck",
  "41": "./templates/template_41_dev_proposal",
  "42": "./templates/template_42_dev_tutorial",
  "43": "./templates/template_43_property_brief",
  "44": "./templates/template_44_property_letter",
  "45": "./templates/template_45_hr_newsletter",
  "46": "./templates/template_46_food_magazine",
  "47": "./templates/template_47_beauty_magazine",
  "48": "./templates/template_48_fashion_proposal",
  "49": "./templates/template_49_sports_guide",
  "50": "./templates/template_50_ngo_report",
};

// ─────────────────────────────────────────────
// CLI 인자 파싱
// ─────────────────────────────────────────────
function parseArgs(argv) {
  const args = argv.slice(2);
  const result = { inputPath: null, outputPath: null, templateId: "01" };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--template" && args[i + 1]) {
      result.templateId = args[++i].replace(/^0*/, "").padStart(2, "0");
    } else if (!result.inputPath) {
      result.inputPath = args[i];
    } else if (!result.outputPath) {
      result.outputPath = args[i];
    }
  }

  return result;
}

// ─────────────────────────────────────────────
// 메인
// ─────────────────────────────────────────────
async function main() {
  const { inputPath, outputPath, templateId } = parseArgs(process.argv);

  // 인자 검증
  if (!inputPath || !outputPath) {
    console.error("사용법: node generate.js <input.json> <output.docx> --template <01~10>");
    process.exit(1);
  }

  if (!fs.existsSync(inputPath)) {
    console.error(`오류: 입력 파일을 찾을 수 없습니다 → ${inputPath}`);
    process.exit(1);
  }

  if (!TEMPLATE_REGISTRY[templateId]) {
    console.error(`오류: 존재하지 않는 템플릿 ID → ${templateId}`);
    console.error(`사용 가능한 템플릿: ${Object.keys(TEMPLATE_REGISTRY).join(", ")} (01~20)`);
    process.exit(1);
  }

  // 입력 JSON 파싱
  let data;
  try {
    const raw = fs.readFileSync(inputPath, "utf-8");
    data = JSON.parse(raw);
  } catch (err) {
    console.error(`오류: JSON 파싱 실패 → ${err.message}`);
    process.exit(1);
  }

  // 템플릿 로드
  const templatePath = path.resolve(__dirname, TEMPLATE_REGISTRY[templateId]);
  const { C } = require(templatePath);

  console.log(`[DocStyle Pro] 템플릿: ${C.NAME} (${templateId})`);
  console.log(`[DocStyle Pro] 입력:   ${inputPath}`);
  console.log(`[DocStyle Pro] 출력:   ${outputPath}`);
  console.log(`[DocStyle Pro] 요소 수: ${(data.elements || []).length}개`);

  // 문서 빌드
  let doc;
  try {
    doc = build(data, C);
  } catch (err) {
    console.error(`오류: 문서 빌드 실패 → ${err.stack}`);
    process.exit(1);
  }

  // 출력 디렉터리 생성
  const outDir = path.dirname(outputPath);
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  // 파일 저장
  try {
    const buffer = await Packer.toBuffer(doc);
    fs.writeFileSync(outputPath, buffer);
    console.log(`[DocStyle Pro] ✅ 완료 → ${outputPath}`);
  } catch (err) {
    console.error(`오류: 파일 저장 실패 → ${err.message}`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`예기치 않은 오류: ${err.message}`);
  process.exit(1);
});
