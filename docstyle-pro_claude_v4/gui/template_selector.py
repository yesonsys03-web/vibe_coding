"""
template_selector.py — DocStyle Pro 템플릿 선택 위젯

기능
    - 10가지 템플릿을 2열 썸네일 카드로 표시
    - 카드 클릭 시 선택 · 선택된 카드는 액센트 테두리 강조
    - 각 카드는 미니 문서 미리보기(QPainter로 직접 렌더) 포함
    - 이름 · 태그 · 설명 표시

시그널
    template_selected(str)  : 선택된 템플릿 ID ("01" ~ "10")
"""

from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QLinearGradient,
)
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget, QGraphicsDropShadowEffect,
)


# ─────────────────────────────────────────────
# 템플릿 메타데이터
# ─────────────────────────────────────────────

TEMPLATES = [
    {
        "id": "01", "category": "Editorial", "name": "Classic Editorial", "tag": "출판사 원고",
        "desc": "다크 헤더 · 빨간 액센트 · 박스형 구획",
        "header": "#1E293B", "header_text": "#FFFFFF",
        "accent": "#DC2626", "box_bg": "#EFF6FF", "box_border": "#3B82F6",
    },
    {
        "id": "02", "category": "Life & Culture", "name": "Minimal Zen", "tag": "에세이 / 철학",
        "desc": "극도의 여백 · 흑백 타이포그래피",
        "header": "#FAFAFA", "header_text": "#18181B",
        "accent": "#18181B", "box_bg": "#F4F4F5", "box_border": "#A1A1AA",
    },
    {
        "id": "03", "category": "Business", "name": "Nordic Blue", "tag": "비즈니스",
        "desc": "차분한 청색 · 스칸디나비아 감성",
        "header": "#0C4A6E", "header_text": "#FFFFFF",
        "accent": "#0EA5E9", "box_bg": "#E0F2FE", "box_border": "#7DD3FC",
    },
    {
        "id": "04", "category": "Life & Culture", "name": "Luxury Gold", "tag": "럭셔리 / 프리미엄",
        "desc": "블랙 & 골드 · 세리프 타이포",
        "header": "#1C1917", "header_text": "#FCD34D",
        "accent": "#D97706", "box_bg": "#FEF3C7", "box_border": "#FDE68A",
    },
    {
        "id": "05", "category": "Education", "name": "Academic", "tag": "학술 / 전문서",
        "desc": "학술지 스타일 · 주석·인용 강조",
        "header": "#1E3A5F", "header_text": "#FFFFFF",
        "accent": "#2563EB", "box_bg": "#EFF6FF", "box_border": "#93C5FD",
    },
    {
        "id": "06", "category": "Tech", "name": "Tech Modern", "tag": "IT / 기술서",
        "desc": "보라 그라데이션 · 코드 블록 감성",
        "header": "#1E1B4B", "header_text": "#A5B4FC",
        "accent": "#8B5CF6", "box_bg": "#EDE9FE", "box_border": "#C4B5FD",
    },
    {
        "id": "07", "category": "Life & Culture", "name": "Warm Editorial", "tag": "라이프스타일",
        "desc": "테라코타 · 베이지 · 따뜻한 색감",
        "header": "#431407", "header_text": "#FED7AA",
        "accent": "#EA580C", "box_bg": "#FFF7ED", "box_border": "#FED7AA",
    },
    {
        "id": "08", "category": "Life & Culture", "name": "Bold Magazine", "tag": "매거진 / 트렌드",
        "desc": "강렬한 컬러 블록 · 굵은 타이포",
        "header": "#881337", "header_text": "#FFFFFF",
        "accent": "#F43F5E", "box_bg": "#FFF1F2", "box_border": "#FCA5A5",
    },
    {
        "id": "09", "category": "Life & Culture", "name": "Forest Green", "tag": "건강 / 자연",
        "desc": "자연 · 에코 · 차분한 초록",
        "header": "#064E3B", "header_text": "#6EE7B7",
        "accent": "#10B981", "box_bg": "#D1FAE5", "box_border": "#6EE7B7",
    },
    {
        "id": "10", "category": "Editorial", "name": "Royal Purple", "tag": "인문 / 예술",
        "desc": "보라 · 문화·예술 고급 감성",
        "header": "#2E1065", "header_text": "#C4B5FD",
        "accent": "#7C3AED", "box_bg": "#F5F3FF", "box_border": "#C4B5FD",
    },

    # ── 직종별 템플릿
    {
        "id": "11", "category": "Medical", "name": "Clinical White", "tag": "의료·헬스케어",
        "desc": "틸 헤더 · 민트 박스 · 청결·신뢰감",
        "header": "#0F766E", "header_text": "#FFFFFF",
        "accent": "#0F766E", "box_bg": "#F0FDFA", "box_border": "#99F6E4",
    },
    {
        "id": "12", "category": "Legal", "name": "Legal Authority", "tag": "법률·법무",
        "desc": "딥 네이비 · 골드 액센트 · 권위·포멀",
        "header": "#1E3A5F", "header_text": "#FFFFFF",
        "accent": "#B7973A", "box_bg": "#F8F9FC", "box_border": "#D4AF5A",
    },
    {
        "id": "13", "category": "Education", "name": "Education Plus", "tag": "교육·강의",
        "desc": "오렌지 헤더 · 블루 박스 · 친근·체계적",
        "header": "#EA580C", "header_text": "#FFFFFF",
        "accent": "#EA580C", "box_bg": "#EFF6FF", "box_border": "#93C5FD",
    },
    {
        "id": "14", "category": "Life & Culture", "name": "Creative Studio", "tag": "마케팅·브랜딩",
        "desc": "퍼플 · 핑크 액센트 · 창의·역동·감각적",
        "header": "#4F1D96", "header_text": "#FFFFFF",
        "accent": "#EC4899", "box_bg": "#FDF4FF", "box_border": "#F9A8D4",
    },
    {
        "id": "15", "category": "Business", "name": "Finance Pro", "tag": "금융·회계",
        "desc": "다크 그린 · 안정적·보수적·정밀",
        "header": "#14532D", "header_text": "#FFFFFF",
        "accent": "#16A34A", "box_bg": "#F0FDF4", "box_border": "#86EFAC",
    },
    {
        "id": "16", "category": "Life & Culture", "name": "Real Estate", "tag": "부동산·건설",
        "desc": "브라운 헤더 · 골드 액센트 · 고급·어스톤",
        "header": "#44403C", "header_text": "#FFFFFF",
        "accent": "#CA8A04", "box_bg": "#FAFAF9", "box_border": "#FDE68A",
    },
    {
        "id": "17", "category": "Life & Culture", "name": "HR Connect", "tag": "인사·채용",
        "desc": "시안 헤더 · 코랄 액센트 · 따뜻·사람중심",
        "header": "#0E7490", "header_text": "#FFFFFF",
        "accent": "#F97316", "box_bg": "#ECFEFF", "box_border": "#A5F3FC",
    },
    {
        "id": "18", "category": "Life & Culture", "name": "Culinary", "tag": "식음료·요식업",
        "desc": "버건디 헤더 · 로즈 액센트 · 따뜻·감성적",
        "header": "#881337", "header_text": "#FFFFFF",
        "accent": "#F43F5E", "box_bg": "#FFF1F2", "box_border": "#FECDD3",
    },
    {
        "id": "19", "category": "Life & Culture", "name": "Energy Black", "tag": "스포츠·피트니스",
        "desc": "블랙 헤더 · 옐로우 액센트 · 강렬·역동",
        "header": "#18181B", "header_text": "#EAB308",
        "accent": "#EAB308", "box_bg": "#FEFCE8", "box_border": "#FDE047",
    },
    {
        "id": "20", "category": "Business", "name": "Civic Blue", "tag": "비영리·공공기관",
        "desc": "코발트 블루 · 공익·신뢰·투명",
        "header": "#1D4ED8", "header_text": "#FFFFFF",
        "accent": "#3B82F6", "box_bg": "#EFF6FF", "box_border": "#93C5FD",
    },
    {
        "id": "21", "category": "Tech", "name": "Startup Pitch", "tag": "스타트업·벤처",
        "desc": "블랙 헤더 · 네온 그린 · 혁신·임팩트",
        "header": "#09090B", "header_text": "#22C55E",
        "accent": "#22C55E", "box_bg": "#F0FDF4", "box_border": "#86EFAC",
    },
    {
        "id": "22", "category": "Tech", "name": "Game Neon", "tag": "게임·엔터테인먼트",
        "desc": "다크 퍼플 헤더 · 시안 · 역동·몰입",
        "header": "#1E1B4B", "header_text": "#22D3EE",
        "accent": "#06B6D4", "box_bg": "#ECFEFF", "box_border": "#A5F3FC",
    },
    {
        "id": "23", "category": "Life & Culture", "name": "Travel Sky", "tag": "여행·관광·호텔",
        "desc": "스카이블루 헤더 · 오렌지 · 설레임·프리미엄",
        "header": "#0369A1", "header_text": "#FFFFFF",
        "accent": "#F97316", "box_bg": "#F0F9FF", "box_border": "#BAE6FD",
    },
    {
        "id": "24", "category": "Life & Culture", "name": "Eco Earth", "tag": "환경·에너지·ESG",
        "desc": "딥 그린 헤더 · 라임 · 지속가능·신뢰",
        "header": "#166534", "header_text": "#FFFFFF",
        "accent": "#65A30D", "box_bg": "#F7FEE7", "box_border": "#BEF264",
    },
    {
        "id": "25", "category": "Tech", "name": "Tech Slate", "tag": "반도체·제조·R&D",
        "desc": "슬레이트 헤더 · 블루 · 정밀·혁신",
        "header": "#1E293B", "header_text": "#FFFFFF",
        "accent": "#2563EB", "box_bg": "#F1F5F9", "box_border": "#93C5FD",
    },
    {
        "id": "26", "category": "Life & Culture", "name": "Media Dark", "tag": "미디어·방송·콘텐츠",
        "desc": "블랙 헤더 · 오렌지 · 임팩트·트렌드",
        "header": "#18181B", "header_text": "#F97316",
        "accent": "#F97316", "box_bg": "#FFF7ED", "box_border": "#FED7AA",
    },
    {
        "id": "27", "category": "Life & Culture", "name": "Calm Lavender", "tag": "심리상담·코칭",
        "desc": "라벤더 헤더 · 소프트 핑크 · 안정·공감",
        "header": "#6D28D9", "header_text": "#FFFFFF",
        "accent": "#EC4899", "box_bg": "#F5F3FF", "box_border": "#DDD6FE",
    },
    {
        "id": "28", "category": "Life & Culture", "name": "Bio Green", "tag": "농업·바이오·식품과학",
        "desc": "올리브 헤더 · 라임 · 자연·생명·신뢰",
        "header": "#365314", "header_text": "#FFFFFF",
        "accent": "#84CC16", "box_bg": "#FEFCE8", "box_border": "#D9F99D",
    },
    {
        "id": "29", "category": "Business", "name": "Logistics Navy", "tag": "물류·유통·SCM",
        "desc": "네이비 헤더 · 옐로우 · 신뢰·정확·속도",
        "header": "#1E3A5F", "header_text": "#FACC15",
        "accent": "#CA8A04", "box_bg": "#FEFCE8", "box_border": "#FDE68A",
    },
    {
        "id": "30", "category": "Life & Culture", "name": "Design Mono", "tag": "패션·인테리어 디자인",
        "desc": "다크 헤더 · 샌드 베이지 · 감각·미니멀",
        "header": "#292524", "header_text": "#D6C5A0",
        "accent": "#D6C5A0", "box_bg": "#FAFAF9", "box_border": "#E7E5E4",
    },
    {
        "id": "31", "category": "Medical", "name": "Medical Newsletter", "tag": "의료·헬스케어 뉴스레터",
        "desc": "클린 틸 · 화이트 · 신뢰감 있는 의료 뉴스레터",
        "header": "#0F766E", "header_text": "#FFFFFF",
        "accent": "#0F766E", "box_bg": "#F0FDFA", "box_border": "#99F6E4",
    },
    {
        "id": "32", "category": "Medical", "name": "Clinical Report", "tag": "의료·헬스케어 분석서",
        "desc": "딥 틸 · 그레이 · 정밀한 의료 분석서",
        "header": "#134E4A", "header_text": "#FFFFFF",
        "accent": "#0D9488", "box_bg": "#F0FDFA", "box_border": "#99F6E4",
    },
    {
        "id": "33", "category": "Legal", "name": "Legal Report", "tag": "법률·법무 보고서",
        "desc": "딥 네이비 · 골드 라인 · 권위 있는 법률 보고서",
        "header": "#1E3A5F", "header_text": "#FFFFFF",
        "accent": "#B7973A", "box_bg": "#F8F9FC", "box_border": "#D4AF5A",
    },
    {
        "id": "34", "category": "Legal", "name": "Legal Proposal", "tag": "법률·법무 제안서",
        "desc": "다크 슬레이트 · 아이보리 · 포멀한 법률 제안서",
        "header": "#0F172A", "header_text": "#FFFFFF",
        "accent": "#C9A84C", "box_bg": "#FAFAF9", "box_border": "#FDE68A",
    },
    {
        "id": "35", "category": "Education", "name": "Lecture Note", "tag": "교육·강의 강의안",
        "desc": "블루 헤더 · 옐로우 하이라이트 · 명확한 강의안",
        "header": "#1D4ED8", "header_text": "#FFFFFF",
        "accent": "#EAB308", "box_bg": "#FEFCE8", "box_border": "#FDE047",
    },
    {
        "id": "36", "category": "Education", "name": "Edu Proposal", "tag": "교육·강의 제안서",
        "desc": "오렌지 헤더 · 화이트 · 열정적인 교육 제안서",
        "header": "#C2410C", "header_text": "#FFFFFF",
        "accent": "#EA580C", "box_bg": "#FFF7ED", "box_border": "#FED7AA",
    },
    {
        "id": "37", "category": "Life & Culture", "name": "Brand Proposal", "tag": "마케팅·브랜딩 제안서",
        "desc": "핫핑크 헤더 · 블랙 · 강렬한 브랜딩 제안서",
        "header": "#BE185D", "header_text": "#FFFFFF",
        "accent": "#EC4899", "box_bg": "#FFF0F6", "box_border": "#FBCFE8",
    },
    {
        "id": "38", "category": "Life & Culture", "name": "Brand Newsletter", "tag": "마케팅·브랜딩 뉴스레터",
        "desc": "코랄 헤더 · 크림 · 트렌디한 마케팅 뉴스레터",
        "header": "#E55B3C", "header_text": "#FFFFFF",
        "accent": "#E55B3C", "box_bg": "#FFF7ED", "box_border": "#FED7AA",
    },
    {
        "id": "39", "category": "Business", "name": "Finance Report", "tag": "금융·회계 보고서",
        "desc": "다크 그린 헤더 · 실버 · 정밀한 금융 보고서",
        "header": "#14532D", "header_text": "#FFFFFF",
        "accent": "#16A34A", "box_bg": "#F0FDF4", "box_border": "#86EFAC",
    },
    {
        "id": "40", "category": "Business", "name": "Investment Deck", "tag": "금융·회계 제안서",
        "desc": "차콜 헤더 · 골드 · 전문적인 투자 제안서",
        "header": "#1C1917", "header_text": "#FACC15",
        "accent": "#CA8A04", "box_bg": "#FEF9C3", "box_border": "#FDE047",
    },
    {
        "id": "41", "category": "Tech", "name": "Dev Proposal", "tag": "IT·개발 제안서",
        "desc": "퍼플 헤더 · 그린 코드 감성 · IT 제안서",
        "header": "#1E1B4B", "header_text": "#FFFFFF",
        "accent": "#22C55E", "box_bg": "#F5F3FF", "box_border": "#86EFAC",
    },
    {
        "id": "42", "category": "Tech", "name": "Dev Tutorial", "tag": "IT·개발 강의안",
        "desc": "다크 헤더 · 시안 · 명확한 기술 강의안",
        "header": "#0F172A", "header_text": "#22D3EE",
        "accent": "#22D3EE", "box_bg": "#ECFEFF", "box_border": "#A5F3FC",
    },
    {
        "id": "43", "category": "Life & Culture", "name": "Property Brief", "tag": "부동산·건설 기획서",
        "desc": "브라운 헤더 · 골드 · 고급스러운 부동산 기획서",
        "header": "#3D2B1F", "header_text": "#FFFFFF",
        "accent": "#B7973A", "box_bg": "#FEF3C7", "box_border": "#FDE68A",
    },
    {
        "id": "44", "category": "Life & Culture", "name": "Property Letter", "tag": "부동산·건설 뉴스레터",
        "desc": "베이지 헤더 · 어스그린 · 신뢰감 있는 부동산 뉴스레터",
        "header": "#44403C", "header_text": "#FFFFFF",
        "accent": "#4D7C0F", "box_bg": "#FAFAF9", "box_border": "#D9F99D",
    },
    {
        "id": "45", "category": "Life & Culture", "name": "HR Newsletter", "tag": "인사·채용 뉴스레터",
        "desc": "시안 헤더 · 코랄 · 따뜻한 HR 뉴스레터",
        "header": "#0E7490", "header_text": "#FFFFFF",
        "accent": "#F97316", "box_bg": "#ECFEFF", "box_border": "#A5F3FC",
    },
    {
        "id": "46", "category": "Life & Culture", "name": "Food Magazine", "tag": "식음료·요식업 매거진",
        "desc": "버건디 헤더 · 크림 · 식욕을 자극하는 매거진",
        "header": "#9F1239", "header_text": "#FFFFFF",
        "accent": "#F43F5E", "box_bg": "#FFF1F2", "box_border": "#FECDD3",
    },
    {
        "id": "47", "category": "Life & Culture", "name": "Beauty Magazine", "tag": "패션·뷰티 매거진",
        "desc": "블랙 헤더 · 로즈골드 · 고급스러운 뷰티 매거진",
        "header": "#1C1917", "header_text": "#E8B4A0",
        "accent": "#E8B4A0", "box_bg": "#FFF1F2", "box_border": "#F5CDB8",
    },
    {
        "id": "48", "category": "Life & Culture", "name": "Fashion Proposal", "tag": "패션·뷰티 제안서",
        "desc": "모카 헤더 · 샴페인 · 세련된 패션 제안서",
        "header": "#3B1C0A", "header_text": "#D6C5A0",
        "accent": "#C9A882", "box_bg": "#FAFAF9", "box_border": "#E7D8C2",
    },
    {
        "id": "49", "category": "Life & Culture", "name": "Sports Guide", "tag": "스포츠·피트니스 강의안",
        "desc": "블랙 헤더 · 레드 · 강렬한 스포츠 강의안",
        "header": "#18181B", "header_text": "#F87171",
        "accent": "#DC2626", "box_bg": "#FEF2F2", "box_border": "#FCA5A5",
    },
    {
        "id": "50", "category": "Education", "name": "NGO Report", "tag": "비영리·공공기관 보고서",
        "desc": "코발트 헤더 · 화이트 · 투명한 공공 보고서",
        "header": "#1E40AF", "header_text": "#FFFFFF",
        "accent": "#3B82F6", "box_bg": "#EFF6FF", "box_border": "#93C5FD",
    },
]


def _hex(color: str) -> QColor:
    return QColor(f"#{color.lstrip('#')}")


# ─────────────────────────────────────────────
# 미니 문서 썸네일 (QPainter)
# ─────────────────────────────────────────────

class ThumbnailWidget(QWidget):
    """QPainter로 직접 그리는 미니 문서 미리보기"""

    def __init__(self, tpl: dict, parent=None):
        super().__init__(parent)
        self._tpl = tpl
        self.setFixedHeight(140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self._tpl
        W = self.width()
        H = self.height()

        # ── 1. 배경 (그라데이션)
        grad = QLinearGradient(0, 0, 0, H)
        grad.setColorAt(0, QColor("#FFFFFF"))
        grad.setColorAt(1, QColor("#F8FAFC"))
        p.fillRect(self.rect(), grad)

        # ── 2. 스타일 결정
        cat = t.get("category", "")
        name = t.get("name", "").lower()
        
        is_minimal = "minimal" in name or "zen" in name or "mono" in name
        is_tech = cat == "Tech" or "dev" in name
        is_formal = cat in ["Medical", "Legal", "Business", "Education"]
        is_editorial = cat == "Editorial" or "magazine" in name or "editorial" in name

        # ── 3. 헤더 렌더링
        hdr_h = 36
        if is_minimal: hdr_h = 24
        elif is_editorial: hdr_h = 42

        hdr_rect = QRect(0, 0, W, hdr_h)
        p.fillRect(hdr_rect, _hex(t["header"]))

        # 헤더 텍스트 라인
        p.setPen(Qt.PenStyle.NoPen)
        txt_color = _hex(t["header_text"])
        if is_minimal:
            p.fillRect(QRect(W//2 - 25, 10, 50, 4), txt_color.darker(110))
        else:
            p.fillRect(QRect(12, hdr_h // 2 - 4, 60, 6), txt_color.lighter(110))
            p.fillRect(QRect(12, hdr_h // 2 + 6, 30, 3), txt_color.darker(120))
            # 액센트 포인트
            p.fillRect(QRect(0, 0, 4, hdr_h), _hex(t["accent"]))

        # 번호 배지
        p.setBrush(_hex(t["accent"]))
        p.drawEllipse(W - 22, 6, 14, 14)
        p.setPen(QColor("#FFFFFF"))
        p.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        p.drawText(QRect(W - 22, 6, 14, 14), Qt.AlignmentFlag.AlignCenter, t["id"])

        # ── 4. 본문 내용 렌더링
        y = hdr_h + 12
        p.setPen(Qt.PenStyle.NoPen)

        if is_tech:
            # 테크: 모노스페이스/코드 느낌 (들여쓰기 섞인 짧은 선들)
            for i in range(4):
                indent = 12 + (10 if i % 2 == 1 else 0)
                p.fillRect(QRect(indent, y, 40 + (i*10), 3), QColor("#CBD5E1"))
                y += 8
            # 터미널 느낌의 박스
            p.fillRect(QRect(12, y + 4, W - 24, 28), QColor("#1E293B")) # 다크 박스
            p.fillRect(QRect(16, y + 10, 40, 2), _hex(t["accent"]))
            p.fillRect(QRect(16, y + 16, 60, 2), QColor("#4ade80")) # 네온 그린 라인
        
        elif is_minimal:
            # 미니멀: 중앙 정렬된 가느다란 선들
            y += 8
            for w in [60, 80, 50, 70]:
                p.fillRect(QRect(W//2 - w//2, y, w, 2), QColor("#E2E8F0"))
                y += 10
        
        elif is_editorial:
            # 에디토리얼: 굵은 제목 + 다단 느낌
            p.fillRect(QRect(12, y, 90, 10), _hex(t["accent"]))
            y += 18
            # 2단 가상 렌더링
            mid = W // 2
            for i in range(3):
                p.fillRect(QRect(12, y, mid - 18, 3), QColor("#E2E8F0"))
                p.fillRect(QRect(mid + 6, y, mid - 18, 3), QColor("#E2E8F0"))
                y += 8
        
        else:
            # 포멀/기본: 깔끔한 리스트/박스형
            p.fillRect(QRect(12, y, 4, 12), _hex(t["accent"]))
            p.fillRect(QRect(20, y + 2, 80, 8), QColor("#94A3B8"))
            y += 20
            # 강조 박스
            box_r = QRect(12, y, W - 24, 30)
            p.fillRect(box_r, _hex(t["box_bg"]))
            p.setPen(QPen(_hex(t["box_border"]), 1, Qt.PenStyle.DashLine))
            p.drawRect(box_r)
            p.setPen(Qt.PenStyle.NoPen)
            p.fillRect(QRect(20, y+10, 60, 3), _hex(t["box_border"]).darker(110))

        # ── 5. 하단 장식 (페이지 번호 느낌)
        p.setBrush(QColor("#E2E8F0"))
        p.drawRect(W//2 - 10, H - 10, 20, 2)

        # ── 6. 외곽선
        p.setPen(QPen(QColor("#E2E8F0"), 1))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        p.end()


# ─────────────────────────────────────────────
# 개별 템플릿 카드
# ─────────────────────────────────────────────

class TemplateCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, tpl: dict, parent=None):
        super().__init__(parent)
        self._tpl      = tpl
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(200)
        self._build_ui()
        self._apply_style(selected=False)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 썸네일
        self._thumb = ThumbnailWidget(self._tpl, self)
        layout.addWidget(self._thumb)

        # 하단 정보 패널
        info = QWidget(self)
        info.setObjectName("card_info")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(10, 8, 10, 10)
        info_layout.setSpacing(3)

        # 이름 + 태그 행
        name_row = QWidget()
        from PyQt6.QtWidgets import QHBoxLayout
        nr_lay = QHBoxLayout(name_row)
        nr_lay.setContentsMargins(0, 0, 0, 0)
        nr_lay.setSpacing(4)

        name_lbl = QLabel(self._tpl["name"])
        name_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: #111827;")

        tag_lbl = QLabel(self._tpl["tag"])
        tag_lbl.setFont(QFont("Arial", 8))
        tag_lbl.setStyleSheet(
            f"color: {self._tpl['accent']};"
            f"background: {self._tpl['box_bg']};"
            "padding: 1px 6px; border-radius: 8px;"
        )
        tag_lbl.setMaximumWidth(90)

        nr_lay.addWidget(name_lbl)
        nr_lay.addStretch()
        nr_lay.addWidget(tag_lbl)

        desc_lbl = QLabel(self._tpl["desc"])
        desc_lbl.setFont(QFont("Arial", 8))
        desc_lbl.setStyleSheet("color: #6B7280;")
        desc_lbl.setWordWrap(True)

        info_layout.addWidget(name_row)
        info_layout.addWidget(desc_lbl)
        layout.addWidget(info)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style(selected)
        self._thumb.update()

    def _apply_style(self, selected: bool):
        accent = self._tpl["accent"]
        if selected:
            self.setStyleSheet(
                f"TemplateCard {{ border: 2.5px solid {accent}; border-radius: 12px; background: #FFFFFF; }}"
                f"QWidget#card_info {{ background: #FAFAFA; border-top: 1px solid {accent}20; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; }}"
            )
            # 그림자 소멸
            self.setGraphicsEffect(None)
        else:
            self.setStyleSheet(
                "TemplateCard { border: 1.5px solid #E2E8F0; border-radius: 12px; background: #FFFFFF; }"
                "TemplateCard:hover { border-color: #94A3B8; }"
                "QWidget#card_info { background: #FFFFFF; border-top: 1px solid #F1F5F9; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; }"
            )
            # 미묘한 그림자 추가
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(15)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QColor(0, 0, 0, 20))
            self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._tpl["id"])


# ─────────────────────────────────────────────
# 템플릿 선택기 (스크롤 가능한 그리드)
# ─────────────────────────────────────────────

class TemplateSelector(QWidget):
    """
    2열 그리드로 10개 템플릿 카드를 표시한다.

    Signals
    -------
    template_selected(str)  선택된 템플릿 ID
    """

    template_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id = "01"
        self._cards: dict[str, TemplateCard] = {}
        self._build_ui()
        self._select("01")

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 섹션 헤더
        header = QLabel("템플릿 라이브러리")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header.setStyleSheet(
            "color: #1E293B; padding: 16px 20px 12px;"
            "background: #FFFFFF; border-bottom: 1px solid #F1F5F9;"
        )
        outer.addWidget(header)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: #F8FAFC; }")

        container = QWidget()
        container.setStyleSheet("background: #F8FAFC;")
        self._content_layout = QVBoxLayout(container)
        self._content_layout.setContentsMargins(16, 16, 16, 32)
        self._content_layout.setSpacing(24)

        # 카테고리별로 그룹화하여 렌더링
        categories = [
            ("원고 / 출판", "Editorial"),
            ("의료 / 헬스케어", "Medical"),
            ("법률 / 전문직", "Legal"),
            ("비즈니스 / 금융", "Business"),
            ("IT / 테크", "Tech"),
            ("교육 / 학술", "Education"),
            ("라이프스타일 / 기타", "Life & Culture"),
        ]

        for label, cat_key in categories:
            items = [t for t in TEMPLATES if t["category"] == cat_key]
            if not items:
                continue

            # 카테고리 제목
            cat_title = QLabel(label)
            cat_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            cat_title.setStyleSheet("color: #64748B; padding-top: 8px; border-top: 1px solid #E2E8F0;")
            self._content_layout.addWidget(cat_title)

            # 그리드 (2열)
            grid = QGridLayout()
            grid.setSpacing(16)
            for i, tpl in enumerate(items):
                card = TemplateCard(tpl)
                card.clicked.connect(self._select)
                self._cards[tpl["id"]] = card
                grid.addWidget(card, i // 2, i % 2)
            
            self._content_layout.addLayout(grid)

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _select(self, tpl_id: str):
        # 이전 선택 해제
        if self._selected_id in self._cards:
            self._cards[self._selected_id].set_selected(False)
        # 새 선택 적용
        self._selected_id = tpl_id
        if tpl_id in self._cards:
            self._cards[tpl_id].set_selected(True)
        self.template_selected.emit(tpl_id)

    @property
    def selected_id(self) -> str:
        return self._selected_id

    def get_template_info(self, tpl_id: str) -> dict:
        for t in TEMPLATES:
            if t["id"] == tpl_id:
                return t
        return TEMPLATES[0]
