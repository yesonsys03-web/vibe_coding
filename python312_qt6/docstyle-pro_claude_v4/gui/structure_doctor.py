import re
from collections import Counter


_HEADING_RE = re.compile(r"^\s*(#{1,6})\s*(.*?)\s*$")


def _scan_headings(text: str) -> list[tuple[int, int, str]]:
    headings: list[tuple[int, int, str]] = []
    in_code = False

    for idx, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue

        m = _HEADING_RE.match(line)
        if not m:
            continue

        level = min(max(len(m.group(1)), 1), 5)
        title = (m.group(2) or "").strip()
        headings.append((idx, level, title))

    return headings


def inspect_markdown_structure(text: str) -> dict:
    headings = _scan_headings(text)
    issues: list[str] = []
    issue_items: list[dict] = []
    suggestions: list[str] = []

    if not headings:
        issues.append("제목 구조(H1~H5)가 없습니다.")
        issue_items.append({"line": 1, "message": "제목 구조(H1~H5)가 없습니다."})
        suggestions.append("문서 제목을 H1(`# 제목`)로 먼저 추가하세요.")
    else:
        first_level = headings[0][1]
        if first_level != 1:
            issues.append("첫 제목이 H1이 아닙니다.")
            issue_items.append(
                {
                    "line": headings[0][0],
                    "message": "첫 제목이 H1이 아닙니다.",
                }
            )
            suggestions.append(
                "첫 제목을 H1으로 맞추면 목차/스타일 적용이 안정적입니다."
            )

        prev_level = headings[0][1]
        for ln, level, _ in headings[1:]:
            if level - prev_level > 1:
                msg = f"라인 {ln}: 제목 레벨이 한 번에 {prev_level} -> {level}로 점프합니다."
                issues.append(msg)
                issue_items.append({"line": ln, "message": msg})
            prev_level = level

        dup_counter = Counter([h[2].strip().lower() for h in headings if h[2].strip()])
        dups = [name for name, cnt in dup_counter.items() if cnt > 1]
        if dups:
            issues.append(f"중복 제목 {len(dups)}개가 있습니다.")
            for name in dups[:6]:
                for ln, _, title in headings:
                    if title.strip().lower() == name:
                        issue_items.append(
                            {
                                "line": ln,
                                "message": f"라인 {ln}: 중복 제목 '{title}'",
                            }
                        )
                        break
            suggestions.append("동일한 제목은 번호나 맥락 단어를 추가해 구분하세요.")

        long_heads = [ln for ln, _, title in headings if len(title) > 65]
        if long_heads:
            issues.append(f"너무 긴 제목이 {len(long_heads)}개 있습니다.")
            for ln in long_heads[:6]:
                issue_items.append(
                    {"line": ln, "message": f"라인 {ln}: 제목 길이가 너무 깁니다."}
                )
            suggestions.append(
                "긴 제목은 본문으로 내리고 제목은 핵심어 위주로 줄이세요."
            )

    level_counts = Counter([level for _, level, _ in headings])
    issue_count = len(issues)
    score = max(0, 100 - issue_count * 12)

    return {
        "score": score,
        "issue_count": issue_count,
        "issues": issues,
        "issue_items": issue_items,
        "suggestions": suggestions,
        "heading_count": len(headings),
        "heading_levels": {
            "h1": level_counts.get(1, 0),
            "h2": level_counts.get(2, 0),
            "h3": level_counts.get(3, 0),
            "h4": level_counts.get(4, 0),
            "h5": level_counts.get(5, 0),
        },
    }


def normalize_markdown_structure(text: str) -> tuple[str, dict]:
    lines = text.splitlines()
    out: list[str] = []
    in_code = False
    changes = {
        "heading_normalized": 0,
        "empty_heading_filled": 0,
        "blankline_compacted": 0,
        "title_promoted": 0,
    }

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code = not in_code
            out.append(line)
            continue

        if in_code:
            out.append(line)
            continue

        m = _HEADING_RE.match(line)
        if m:
            level = min(max(len(m.group(1)), 1), 5)
            title = (m.group(2) or "").strip()
            if not title:
                title = "제목 없음"
                changes["empty_heading_filled"] += 1
            normalized = f"{'#' * level} {title}"
            if normalized != line:
                changes["heading_normalized"] += 1
            out.append(normalized)
        else:
            out.append(line)

    compacted: list[str] = []
    blank_run = 0
    for line in out:
        if line.strip() == "":
            blank_run += 1
            if blank_run > 1:
                changes["blankline_compacted"] += 1
                continue
        else:
            blank_run = 0
        compacted.append(line)

    if not _scan_headings("\n".join(compacted)):
        first_idx = -1
        for idx, line in enumerate(compacted):
            s = line.strip()
            if not s:
                continue
            if s.startswith(("- ", "* ", "> ", "```", "1. ", "2. ", "3. ")):
                break
            if len(s) <= 80:
                first_idx = idx
            break

        if first_idx >= 0:
            compacted[first_idx] = f"# {compacted[first_idx].strip()}"
            changes["title_promoted"] += 1

    normalized_text = "\n".join(compacted)
    report = inspect_markdown_structure(normalized_text)
    report["changes"] = changes
    report["changed"] = normalized_text != text
    return normalized_text, report
