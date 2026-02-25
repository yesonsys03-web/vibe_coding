"use client";

import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

const CATEGORY_ORDER = [
  ["Editorial", "원고 / 출판"],
  ["Medical", "의료 / 헬스케어"],
  ["Legal", "법률 / 전문직"],
  ["Business", "비즈니스 / 금융"],
  ["Tech", "IT / 테크"],
  ["Education", "교육 / 학술"],
  ["Life & Culture", "라이프스타일 / 기타"],
];

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function HomePage() {
  const [templates, setTemplates] = useState([]);
  const [templateId, setTemplateId] = useState("01");
  const [file, setFile] = useState(null);
  const [markdown, setMarkdown] = useState("# Sample Title\n\nWrite your manuscript here...");
  const [structureReport, setStructureReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [inputMode, setInputMode] = useState("file");
  const [templateCategory, setTemplateCategory] = useState("Editorial");
  const [lastConvertMeta, setLastConvertMeta] = useState(null);
  const [insightQuery, setInsightQuery] = useState("");
  const [insightAnswer, setInsightAnswer] = useState("");
  const [insightContexts, setInsightContexts] = useState([]);
  const [insightGuide, setInsightGuide] = useState([]);
  const [insightFilters, setInsightFilters] = useState("");
  const [aiProvider, setAiProvider] = useState("OpenAI (ChatGPT)");
  const [aiOpenAIKey, setAiOpenAIKey] = useState("");
  const [aiClaudeKey, setAiClaudeKey] = useState("");
  const [aiGeminiKey, setAiGeminiKey] = useState("");
  const [aiGroqKey, setAiGroqKey] = useState("");
  const [aiKeyFlags, setAiKeyFlags] = useState({
    has_openai_key: false,
    has_claude_key: false,
    has_gemini_key: false,
    has_groq_key: false,
    has_gemini_oauth: false,
  });
  const [aiTitle, setAiTitle] = useState("");
  const [aiSubtitle, setAiSubtitle] = useState("");
  const [aiHeader, setAiHeader] = useState("");
  const [aiTocPlan, setAiTocPlan] = useState("");
  const textareaRef = useRef(null);

  const groupedTemplates = useMemo(() => {
    return CATEGORY_ORDER.map(([key, label]) => ({
      key,
      label,
      items: templates.filter((t) => t.category === key),
    })).filter((g) => g.items.length > 0);
  }, [templates]);

  const visibleTemplateGroups = useMemo(() => {
    if (templateCategory === "ALL") return groupedTemplates;
    return groupedTemplates.filter((g) => g.key === templateCategory);
  }, [groupedTemplates, templateCategory]);

  useEffect(() => {
    fetch(`${API_BASE}/templates`)
      .then((r) => r.json())
      .then((data) => {
        const list = Array.isArray(data.templates) ? data.templates : [];
        setTemplates(list);
        if (list.length > 0) setTemplateId(list[0].id);
      })
      .catch((err) => setMessage(`Template load failed: ${err}`));

    fetch(`${API_BASE}/settings/ai`)
      .then((r) => r.json())
      .then((data) => {
        setAiProvider(data.provider || "OpenAI (ChatGPT)");
        setAiKeyFlags({
          has_openai_key: Boolean(data.has_openai_key),
          has_claude_key: Boolean(data.has_claude_key),
          has_gemini_key: Boolean(data.has_gemini_key),
          has_groq_key: Boolean(data.has_groq_key),
          has_gemini_oauth: Boolean(data.has_gemini_oauth),
        });
      })
      .catch(() => {});
  }, []);

  async function saveAiSettings() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/settings/ai`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: aiProvider,
          openai_key: aiOpenAIKey,
          claude_key: aiClaudeKey,
          gemini_key: aiGeminiKey,
          groq_key: aiGroqKey,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "settings save failed");

      const refresh = await fetch(`${API_BASE}/settings/ai`);
      const fresh = await refresh.json();
      setAiKeyFlags({
        has_openai_key: Boolean(fresh.has_openai_key),
        has_claude_key: Boolean(fresh.has_claude_key),
        has_gemini_key: Boolean(fresh.has_gemini_key),
        has_groq_key: Boolean(fresh.has_groq_key),
        has_gemini_oauth: Boolean(fresh.has_gemini_oauth),
      });

      setAiOpenAIKey("");
      setAiClaudeKey("");
      setAiGeminiKey("");
      setAiGroqKey("");
      setMessage("AI 설정이 저장되었습니다.");
    } catch (err) {
      setMessage(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function runStructureCheck() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/structure/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: markdown }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "structure/check failed");
      setStructureReport(data);
      setMessage(`Structure score: ${data.score}`);
    } catch (err) {
      setMessage(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function runNormalize() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/structure/normalize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: markdown }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "structure/normalize failed");
      setMarkdown(data.text || markdown);
      setStructureReport(data.report || null);
      setMessage("Normalized successfully.");
    } catch (err) {
      setMessage(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function runConvert() {
    setBusy(true);
    setMessage("");
    try {
      const form = new FormData();
      const customSettings = {
        style_preset: "template",
        auto_polish: true,
        auto_polish_level: "normal",
      };

      if (file) {
        form.append("file", file);
      } else {
        const mdBlob = new Blob([markdown], { type: "text/markdown" });
        form.append("file", mdBlob, "draft.md");
      }

      form.append("template_id", templateId);
      form.append("custom_settings", JSON.stringify(customSettings));

      const res = await fetch(`${API_BASE}/convert`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "convert failed");
      }

      const blob = await res.blob();
      const elements = res.headers.get("X-DocStyle-Elements");
      const images = res.headers.get("X-DocStyle-Images");
      setLastConvertMeta({
        fileName: `docstyle_${templateId}.docx`,
        sizeKb: Math.max(1, Math.round(blob.size / 1024)),
        elements: elements ? Number(elements) : null,
        images: images ? Number(images) : null,
      });
      downloadBlob(blob, `docstyle_${templateId}.docx`);
      setMessage("Converted and downloaded.");
    } catch (err) {
      setMessage(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function runAiToc() {
    if (!aiTitle.trim()) {
      setMessage("AI 목차 생성을 위해 제목을 입력하세요.");
      return;
    }

    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/ai/toc`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: aiTitle.trim(),
          subtitle: aiSubtitle.trim(),
          header: aiHeader.trim(),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "ai/toc failed");
      const text = String(data.text || "");
      setAiTocPlan(text);
      setMessage("AI 목차 기획이 생성되었습니다.");
    } catch (err) {
      setMessage(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function runAiDraft() {
    if (!aiTitle.trim()) {
      setMessage("AI 본문 초안 생성을 위해 제목을 입력하세요.");
      return;
    }

    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/ai/draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: aiTitle.trim(),
          subtitle: aiSubtitle.trim(),
          header: aiHeader.trim(),
          toc: aiTocPlan,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "ai/draft failed");
      setMarkdown(String(data.text || ""));
      setInputMode("editor");
      setMessage("AI 본문 초안이 생성되어 편집기에 반영되었습니다.");
    } catch (err) {
      setMessage(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function runAiOrganize() {
    const source = markdown.trim();
    if (!source) {
      setMessage("AI 원고 정리를 위해 본문을 입력하세요.");
      return;
    }

    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/ai/organize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: source }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "ai/organize failed");
      setMarkdown(String(data.text || source));
      setInputMode("editor");
      setMessage("AI 원고 정리가 완료되었습니다.");
    } catch (err) {
      setMessage(String(err));
    } finally {
      setBusy(false);
    }
  }

  function parseFilters() {
    return insightFilters
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  async function runInsightGuide() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/insight/guide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filter_files: parseFilters() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "insight/guide failed");
      setInsightGuide(Array.isArray(data.questions) ? data.questions : []);
      setMessage("인사이트 추천 질문을 불러왔습니다.");
    } catch (err) {
      setMessage(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function runInsightAsk() {
    if (!insightQuery.trim()) {
      setMessage("인사이트 질문을 입력하세요.");
      return;
    }

    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/insight/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: insightQuery.trim(),
          filter_files: parseFilters(),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "insight/chat failed");
      setInsightAnswer(String(data.answer || ""));
      setInsightContexts(Array.isArray(data.contexts) ? data.contexts : []);
      setMessage("인사이트 답변이 생성되었습니다.");
    } catch (err) {
      setMessage(String(err));
    } finally {
      setBusy(false);
    }
  }

  function jumpToIssue(issue) {
    const line = Number(issue?.line || 1);
    const textarea = textareaRef.current;
    if (!textarea) return;

    const rows = markdown.split("\n");
    let pos = 0;
    for (let i = 0; i < Math.max(0, line - 1) && i < rows.length; i += 1) {
      pos += rows[i].length + 1;
    }

    textarea.focus();
    textarea.setSelectionRange(pos, pos + (rows[Math.max(0, line - 1)] || "").length);
  }

  return (
    <main className="shell">
      <header className="appHeader">
        <div className="brand">DocStyle Web</div>
        <div className="sub">Desktop-like workflow for manuscript to DOCX</div>
      </header>

      <div className="workspace">
        <aside className="leftPanel">
          <section className="sectionCard">
            <h3>🤖 AI 작성 도우미</h3>
            <label className="field">
              <span>책 제목</span>
              <input
                value={aiTitle}
                onChange={(e) => setAiTitle(e.target.value)}
                placeholder="예: 성공적인 책 출간과 웹사이트 구축"
              />
            </label>
            <label className="field">
              <span>부제 (선택)</span>
              <input
                value={aiSubtitle}
                onChange={(e) => setAiSubtitle(e.target.value)}
                placeholder="예: 실무 실행 로드맵"
              />
            </label>
            <label className="field">
              <span>핵심 키워드 (선택)</span>
              <input
                value={aiHeader}
                onChange={(e) => setAiHeader(e.target.value)}
                placeholder="예: 퍼스널브랜딩, 출판기획"
              />
            </label>

            <div className="actions vertical">
              <button disabled={busy} onClick={runAiToc}>🧭 AI 목차 기획</button>
              <button disabled={busy} onClick={runAiDraft}>✍️ AI 본문 초안 자동 생성</button>
              <button disabled={busy} onClick={runAiOrganize}>🗂️ AI 원고 정리</button>
            </div>

            <label className="field">
              <span>AI 목차 결과</span>
              <textarea
                rows={6}
                value={aiTocPlan}
                onChange={(e) => setAiTocPlan(e.target.value)}
                placeholder="AI 목차 결과가 여기에 표시됩니다."
              />
            </label>
          </section>

          <section className="sectionCard">
            <h3>① 원고 준비</h3>
            <div className="tabs">
              <button
                className={inputMode === "file" ? "tab active" : "tab"}
                onClick={() => setInputMode("file")}
                disabled={busy}
              >
                파일 로드
              </button>
              <button
                className={inputMode === "editor" ? "tab active" : "tab"}
                onClick={() => setInputMode("editor")}
                disabled={busy}
              >
                직접 작성
              </button>
            </div>

            {inputMode === "file" ? (
              <label className="field">
                <span>.md 또는 .docx 파일 선택</span>
                <input
                  type="file"
                  accept=".md,.docx"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
              </label>
            ) : null}

            <label className="field">
              <span>원고 편집</span>
              <textarea
                ref={textareaRef}
                value={markdown}
                onChange={(e) => setMarkdown(e.target.value)}
                rows={14}
              />
            </label>
          </section>

          <section className="sectionCard">
            <h3>② 원고 정리</h3>
            <div className="actions vertical">
              <button disabled={busy} onClick={runStructureCheck}>🔍 구조 점검</button>
              <button disabled={busy} onClick={runNormalize}>🧹 구조 자동 정리</button>
            </div>
          </section>

          <section className="sectionCard">
            <h3>③ 변환 실행</h3>
            <button className="convertBtn" disabled={busy} onClick={runConvert}>
              🚀 변환 시작
            </button>
          </section>
        </aside>

        <section className="centerPanel">
          <div className="sectionCard">
            <h3>템플릿 라이브러리</h3>
            <div className="tplToolbar">
              <span className="tplToolbarLabel">카테고리</span>
              <div className="tplCategoryTabs">
                <button
                  className={templateCategory === "ALL" ? "tplCatBtn active" : "tplCatBtn"}
                  onClick={() => setTemplateCategory("ALL")}
                >
                  전체
                </button>
                {groupedTemplates.map((g) => (
                  <button
                    key={g.key}
                    className={templateCategory === g.key ? "tplCatBtn active" : "tplCatBtn"}
                    onClick={() => setTemplateCategory(g.key)}
                  >
                    {g.label}
                  </button>
                ))}
              </div>
            </div>

            {visibleTemplateGroups.map((group) => (
              <div key={group.key} className="tplGroup">
                <div className="tplGroupTitle">{group.label}</div>
                <div className="templateGrid">
                  {group.items.map((t) => {
                    const isSelected = t.id === templateId;
                    const accent = t.accent || "#DC2626";
                    return (
                      <button
                        key={t.id}
                        className={isSelected ? "tplCard selected" : "tplCard"}
                        onClick={() => setTemplateId(t.id)}
                        style={
                          isSelected
                            ? {
                                borderColor: accent,
                              }
                            : undefined
                        }
                      >
                        <div className="tplThumb">
                          <div
                            className="tplThumbHeader"
                            style={{ background: t.header || "#1E293B", color: t.header_text || "#FFFFFF" }}
                          >
                            <div
                              className="tplAccentRail"
                              style={{ background: accent }}
                            />
                            <div className="tplHeadLines">
                              <span />
                              <span />
                            </div>
                            <div
                              className="tplBadge"
                              style={{ background: accent }}
                            >
                              {t.id}
                            </div>
                          </div>
                          <div className="tplThumbBody">
                            <div className="tplMockTitle" style={{ background: accent }} />
                            <div className="tplMockCols">
                              <div className="tplCol">
                                <span />
                                <span />
                                <span />
                              </div>
                              <div className="tplCol">
                                <span />
                                <span />
                                <span />
                              </div>
                            </div>
                            <div
                              className="tplBox"
                              style={{
                                background: t.box_bg || "#EFF6FF",
                                borderColor: t.box_border || "#93C5FD",
                              }}
                            />
                          </div>
                        </div>
                        <div
                          className="tplInfo"
                          style={
                            isSelected
                              ? {
                                  background: "#FAFAFA",
                                  borderTopColor: `${accent}33`,
                                }
                              : undefined
                          }
                        >
                          <div className="tplMetaRow">
                            <div className="tplName">{t.name}</div>
                            <span
                              className="tplIdPill"
                              style={{ color: accent, background: t.box_bg || "#EEF2FF" }}
                            >
                              #{t.id}
                            </span>
                          </div>
                          <div className="tplMeta">
                            <span
                              className="tplTag"
                              style={{ color: accent, background: t.box_bg || "#F8FAFC" }}
                            >
                              {t.tag || "문서 템플릿"}
                            </span>
                          </div>
                          <div className="tplDesc">{t.desc || ""}</div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          <div className="sectionCard">
            <h3>미리보기 요약</h3>
            <p className="previewText">
              원고 길이: {markdown.length.toLocaleString()} chars<br />
              파일 모드: {file ? `업로드됨 (${file.name})` : "에디터 내용 사용"}<br />
              API: {API_BASE}
            </p>
          </div>

        </section>

        <aside className="rightPanel">
          <section className="sectionCard resultCard">
            <h3>결과 미리보기</h3>
            {lastConvertMeta ? (
              <div className="stats">
                <div><strong>파일</strong> {lastConvertMeta.fileName}</div>
                <div><strong>크기</strong> {lastConvertMeta.sizeKb} KB</div>
                <div><strong>요소</strong> {lastConvertMeta.elements ?? "-"}</div>
                <div><strong>이미지</strong> {lastConvertMeta.images ?? "-"}</div>
              </div>
            ) : (
              <p className="hint">아직 변환 결과가 없습니다.</p>
            )}
          </section>

          <section className="sectionCard">
            <h3>문단 구조 점검 결과</h3>
            {structureReport ? (
              <>
                <p className="hint">점수: <strong>{structureReport.score}</strong></p>
                <div className="issueList">
                  {(structureReport.issue_items || []).length > 0 ? (
                    (structureReport.issue_items || []).map((issue, idx) => (
                      <button
                        key={`${issue.message}-${idx}`}
                        className="issueItem"
                        onClick={() => jumpToIssue(issue)}
                      >
                        {issue.message}
                      </button>
                    ))
                  ) : (
                    <div className="hint">문제 없음</div>
                  )}
                </div>
              </>
            ) : (
              <p className="hint">아직 점검하지 않았습니다.</p>
            )}
          </section>

          <section className="sectionCard">
            <h3>🔐 인사이트랩 AI 설정</h3>
            <label className="field">
              <span>사용할 모델 Provider</span>
              <select value={aiProvider} onChange={(e) => setAiProvider(e.target.value)}>
                <option>OpenAI (ChatGPT)</option>
                <option>Anthropic (Claude)</option>
                <option>Google (Gemini)</option>
                <option>Groq (Llama 3.3)</option>
                <option>Groq (Qwen 2.5 32B)</option>
              </select>
            </label>

            <div className="keyStatus">
              <span className={aiKeyFlags.has_openai_key ? "keyOk" : "keyMissing"}>OpenAI Key {aiKeyFlags.has_openai_key ? "설정됨" : "미설정"}</span>
              <span className={aiKeyFlags.has_claude_key ? "keyOk" : "keyMissing"}>Claude Key {aiKeyFlags.has_claude_key ? "설정됨" : "미설정"}</span>
              <span className={aiKeyFlags.has_gemini_key ? "keyOk" : "keyMissing"}>Gemini Key {aiKeyFlags.has_gemini_key ? "설정됨" : "미설정"}</span>
              <span className={aiKeyFlags.has_gemini_oauth ? "keyOk" : "keyMissing"}>Gemini OAuth {aiKeyFlags.has_gemini_oauth ? "연결됨" : "미연결"}</span>
              <span className={aiKeyFlags.has_groq_key ? "keyOk" : "keyMissing"}>Groq Key {aiKeyFlags.has_groq_key ? "설정됨" : "미설정"}</span>
            </div>

            {(aiProvider.includes("OpenAI")) ? (
              <label className="field">
                <span>OpenAI API Key (입력 시 갱신)</span>
                <input
                  type="password"
                  value={aiOpenAIKey}
                  onChange={(e) => setAiOpenAIKey(e.target.value)}
                  placeholder="sk-..."
                />
              </label>
            ) : null}

            {(aiProvider.includes("Anthropic")) ? (
              <label className="field">
                <span>Anthropic API Key (입력 시 갱신)</span>
                <input
                  type="password"
                  value={aiClaudeKey}
                  onChange={(e) => setAiClaudeKey(e.target.value)}
                  placeholder="sk-ant-..."
                />
              </label>
            ) : null}

            {(aiProvider.includes("Gemini")) ? (
              <label className="field">
                <span>Gemini API Key (입력 시 갱신)</span>
                <input
                  type="password"
                  value={aiGeminiKey}
                  onChange={(e) => setAiGeminiKey(e.target.value)}
                  placeholder="AIza..."
                />
              </label>
            ) : null}

            {(aiProvider.includes("Groq")) ? (
              <label className="field">
                <span>Groq API Key (입력 시 갱신)</span>
                <input
                  type="password"
                  value={aiGroqKey}
                  onChange={(e) => setAiGroqKey(e.target.value)}
                  placeholder="gsk_..."
                />
              </label>
            ) : null}

            <div className="actions">
              <button disabled={busy} onClick={saveAiSettings}>설정 저장</button>
            </div>
            <p className="hint">빈 값은 기존 키를 유지합니다.</p>
          </section>

          <section className="sectionCard">
            <h3>💡 인사이트 랩 사용법</h3>
            <ol className="usageList">
              <li>Vault에 있는 문서 기준으로 질문을 생성하려면 <strong>추천 질문 불러오기</strong>를 누르세요.</li>
              <li>필요하면 파일 경로를 줄바꿈으로 입력해 검색 범위를 좁히세요.</li>
              <li>질문을 입력하고 <strong>질문하기</strong>를 누르면 문맥 기반 답변이 생성됩니다.</li>
            </ol>

            <label className="field">
              <span>필터 파일 경로 (옵션, 줄바꿈으로 여러 개)</span>
              <textarea
                rows={4}
                value={insightFilters}
                onChange={(e) => setInsightFilters(e.target.value)}
                placeholder={"/abs/path/one.md\n/abs/path/two.md"}
              />
            </label>

            <div className="actions">
              <button disabled={busy} onClick={runInsightGuide}>추천 질문 불러오기</button>
            </div>

            {insightGuide.length > 0 ? (
              <div className="guideButtons">
                {insightGuide.map((q, idx) => (
                  <button key={`${q}-${idx}`} className="guideBtn" onClick={() => setInsightQuery(q)}>
                    {q}
                  </button>
                ))}
              </div>
            ) : null}

            <label className="field">
              <span>인사이트 질문</span>
              <textarea
                rows={3}
                value={insightQuery}
                onChange={(e) => setInsightQuery(e.target.value)}
                placeholder="예: 내 원고들 기반으로 다음 책 목차를 제안해줘"
              />
            </label>

            <div className="actions">
              <button disabled={busy} onClick={runInsightAsk}>질문하기</button>
            </div>

            {insightAnswer ? (
              <div className="insightAnswer">
                <h4>AI 답변</h4>
                <pre>{insightAnswer}</pre>
              </div>
            ) : null}

            {insightContexts.length > 0 ? (
              <div className="insightContext">
                <h4>참고 문맥</h4>
                <ul>
                  {insightContexts.slice(0, 6).map((c, idx) => (
                    <li key={`${c.filename || "ctx"}-${idx}`}>
                      <strong>{c.filename || "unknown"}</strong>
                      <div className="hint">{(c.content || "").slice(0, 130)}...</div>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>
        </aside>
      </div>

      <div className="statusBar">
        {busy ? "작업 중..." : "준비됨"}
        <span> · </span>
        {message || "파일을 로드하고 템플릿을 선택하세요"}
      </div>
    </main>
  );
}
