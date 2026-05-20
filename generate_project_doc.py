"""
generate_project_doc.py
Generates a detailed project documentation PDF using ReportLab.
No system dependencies required (no GTK, no Chrome).

Run:    python generate_project_doc.py
Output: output/Lead_Automation_System_Documentation.pdf
"""

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether,
)
from reportlab.platypus.flowables import Flowable

# ── Output ────────────────────────────────────────────────────────────────
OUTPUT = Path("output/Lead_Automation_System_Documentation.pdf")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
GENERATED_AT = datetime.now().strftime("%B %d, %Y")

# ── Colours ───────────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#1a2744")
GOLD   = colors.HexColor("#f59e0b")
LIGHT  = colors.HexColor("#f8fafc")
BORDER = colors.HexColor("#e2e8f0")
MUTED  = colors.HexColor("#6b7280")
SLATE  = colors.HexColor("#475569")
GREEN  = colors.HexColor("#065f46")
GREEN_BG = colors.HexColor("#d1fae5")
AMBER  = colors.HexColor("#92400e")
AMBER_BG = colors.HexColor("#fef3c7")
RED    = colors.HexColor("#991b1b")
RED_BG = colors.HexColor("#fee2e2")
BLUE   = colors.HexColor("#1e40af")
BLUE_BG = colors.HexColor("#dbeafe")
CODE_BG = colors.HexColor("#0f172a")
CODE_FG = colors.HexColor("#e2e8f0")
CALLOUT_BG = colors.HexColor("#eff6ff")

W, H = A4  # 595.27 x 841.89 pts

# ── Styles ────────────────────────────────────────────────────────────────
SS = getSampleStyleSheet()

def style(name, **kw):
    base = kw.pop("parent", "Normal")
    s = ParagraphStyle(name, parent=SS[base], **kw)
    return s

S_BODY     = style("Body",     fontSize=10, leading=16, textColor=colors.HexColor("#1e293b"), spaceAfter=6)
S_BODY_SM  = style("BodySm",   fontSize=9,  leading=14, textColor=SLATE, spaceAfter=4)
S_H1       = style("H1",       fontSize=22, leading=28, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=6, spaceBefore=4)
S_H2       = style("H2",       fontSize=15, leading=20, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=8, spaceBefore=14)
S_H3       = style("H3",       fontSize=11, leading=15, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=6, spaceBefore=10)
S_LABEL    = style("Label",    fontSize=8,  leading=11, textColor=GOLD,  fontName="Helvetica-Bold", spaceAfter=4)
S_CODE     = style("Code",     fontSize=8,  leading=13, textColor=CODE_FG, fontName="Courier", backColor=CODE_BG, spaceAfter=8, leftIndent=8, rightIndent=8, borderPadding=8)
S_CALLOUT  = style("Callout",  fontSize=10, leading=16, textColor=colors.HexColor("#1e293b"), backColor=CALLOUT_BG, leftIndent=12, rightIndent=8, borderPadding=10, spaceAfter=10)
S_MUTED    = style("Muted",    fontSize=8,  leading=12, textColor=MUTED, spaceAfter=4)
S_CENTER   = style("Center",   fontSize=10, leading=16, alignment=TA_CENTER, textColor=colors.HexColor("#1e293b"))
S_COVER_H  = style("CoverH",   fontSize=32, leading=40, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER)
S_COVER_SUB= style("CoverSub", fontSize=14, leading=20, textColor=colors.HexColor("#cbd5e1"), alignment=TA_CENTER)
S_COVER_SM = style("CoverSm",  fontSize=9,  leading=14, textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER)
S_TOC_TITLE= style("TocTitle", fontSize=11, leading=15, textColor=NAVY, fontName="Helvetica-Bold")
S_TOC_DESC = style("TocDesc",  fontSize=9,  leading=13, textColor=MUTED)
S_MONO     = style("Mono",     fontSize=8.5,leading=13, textColor=colors.HexColor("#0f172a"), fontName="Courier", backColor=colors.HexColor("#f1f5f9"), borderPadding=3)
S_BULLET   = style("Bullet",   fontSize=10, leading=15, textColor=SLATE, leftIndent=14, bulletIndent=4, spaceAfter=3)

# ── Custom Flowables ──────────────────────────────────────────────────────

class ColorRect(Flowable):
    """A solid-colour rectangle — used for cover background and section accents."""
    def __init__(self, w, h, fill, radius=0):
        super().__init__()
        self.w, self.h, self.fill, self.radius = w, h, fill, radius
    def wrap(self, *_): return self.w, self.h
    def draw(self):
        self.canv.setFillColor(self.fill)
        if self.radius:
            self.canv.roundRect(0, 0, self.w, self.h, self.radius, fill=1, stroke=0)
        else:
            self.canv.rect(0, 0, self.w, self.h, fill=1, stroke=0)


class SectionHeader(Flowable):
    """Numbered section header with navy circle + title."""
    def __init__(self, num, title, width):
        super().__init__()
        self.num, self.title, self.width = num, title, width
        self.height = 44
    def wrap(self, *_): return self.width, self.height
    def draw(self):
        c = self.canv
        # Circle
        c.setFillColor(NAVY)
        c.circle(18, 18, 16, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(18, 14, self.num)
        # Title
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 17)
        c.drawString(42, 12, self.title)
        # Bottom rule
        c.setStrokeColor(BORDER)
        c.setLineWidth(1.5)
        c.line(0, 0, self.width, 0)


class CalloutBox(Flowable):
    """Gold left-border callout box."""
    def __init__(self, text, width):
        super().__init__()
        self.text, self.width = text, width
        self._para = Paragraph(text, S_BODY)
    def wrap(self, aw, ah):
        pw, ph = self._para.wrap(aw - 28, ah)
        self.height = ph + 20
        return aw, self.height
    def draw(self):
        c = self.canv
        c.setFillColor(CALLOUT_BG)
        c.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.rect(0, 0, 4, self.height, fill=1, stroke=0)
        self._para.drawOn(c, 16, 10)


class CodeBlock(Flowable):
    """Dark code block."""
    def __init__(self, text, width):
        super().__init__()
        self.text, self.width = text, width
        lines = text.strip().split("\n")
        self.lines = lines
        self.height = len(lines) * 13 + 20
    def wrap(self, *_): return self.width, self.height
    def draw(self):
        c = self.canv
        c.setFillColor(CODE_BG)
        c.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=0)
        c.setFillColor(CODE_FG)
        c.setFont("Courier", 8)
        y = self.height - 18
        for line in self.lines:
            c.drawString(12, y, line)
            y -= 13


def badge(text, bg, fg):
    """Inline badge as a Paragraph."""
    return Paragraph(
        f'<font color="#{fg[1:]}" size="7"><b> {text} </b></font>',
        ParagraphStyle("badge", backColor=bg, borderPadding=2,
                       fontSize=7, leading=10, fontName="Helvetica-Bold")
    )


def data_table(headers, rows, col_widths=None):
    """Styled data table."""
    data = [[Paragraph(f"<b>{h}</b>", ParagraphStyle("th", fontSize=8.5, textColor=GOLD,
             fontName="Helvetica-Bold", leading=12)) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), S_BODY_SM) for c in row])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND",  (0, 0), (-1, 0),  NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID",        (0, 0), (-1, -1),  0.5, BORDER),
        ("TOPPADDING",  (0, 0), (-1, -1),  7),
        ("BOTTOMPADDING",(0,0), (-1, -1),  7),
        ("LEFTPADDING", (0, 0), (-1, -1),  8),
        ("RIGHTPADDING",(0, 0), (-1, -1),  8),
        ("VALIGN",      (0, 0), (-1, -1),  "TOP"),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t


def h3(text): return Paragraph(text, S_H3)
def body(text): return Paragraph(text, S_BODY)
def body_sm(text): return Paragraph(text, S_BODY_SM)
def sp(n=6): return Spacer(1, n)
def rule(): return HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=8, spaceBefore=4)
def bullet(text): return Paragraph(f"• {text}", S_BULLET)
def code(text): return CodeBlock(text, W - 40*mm)
def callout(text): return CalloutBox(text, W - 40*mm)
def sec(num, title): return SectionHeader(num, title, W - 40*mm)

# ── Page Templates ────────────────────────────────────────────────────────

def cover_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    # Gold accent bar at bottom
    canvas.setFillColor(GOLD)
    canvas.rect(0, 0, W, 6, fill=1, stroke=0)
    canvas.restoreState()

def content_page(canvas, doc):
    canvas.saveState()
    # Header rule
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(20*mm, H - 14*mm, W - 20*mm, H - 14*mm)
    # Header text
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(20*mm, H - 11*mm, "Lead Automation System  ·  Project Documentation")
    canvas.drawRightString(W - 20*mm, H - 11*mm, GENERATED_AT)
    # Footer rule
    canvas.line(20*mm, 14*mm, W - 20*mm, 14*mm)
    # Footer text
    canvas.drawString(20*mm, 10*mm, "github.com/Lalith9701/lead-automation-system")
    canvas.drawRightString(W - 20*mm, 10*mm, f"Page {doc.page}")
    canvas.restoreState()

# ── Document setup ────────────────────────────────────────────────────────
doc = BaseDocTemplate(
    str(OUTPUT), pagesize=A4,
    leftMargin=20*mm, rightMargin=20*mm,
    topMargin=20*mm, bottomMargin=20*mm,
    title="Lead Automation System — Project Documentation",
    author="Lead Automation System",
)

cover_frame   = Frame(0, 0, W, H, leftPadding=20*mm, rightPadding=20*mm,
                      topPadding=20*mm, bottomPadding=20*mm, id="cover")
content_frame = Frame(20*mm, 18*mm, W - 40*mm, H - 36*mm, id="content")

doc.addPageTemplates([
    PageTemplate(id="Cover",   frames=[cover_frame],   onPage=cover_bg),
    PageTemplate(id="Content", frames=[content_frame], onPage=content_page),
])

story = []

# ══════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════════════════
story.append(NextPageTemplate("Cover"))
story.append(sp(60))
story.append(Paragraph("PROJECT DOCUMENTATION  ·  FULL TECHNICAL REFERENCE",
    ParagraphStyle("badge_cover", fontSize=9, textColor=GOLD, fontName="Helvetica-Bold",
                   alignment=TA_CENTER, letterSpacing=1.5)))
story.append(sp(20))
story.append(Paragraph("Lead Automation System", S_COVER_H))
story.append(sp(10))
story.append(Paragraph("End-to-End AI-Powered Lead Pipeline", S_COVER_SUB))
story.append(sp(14))
story.append(Paragraph(
    "Automated enrichment  ·  Claude AI report generation  ·  WeasyPrint PDF rendering<br/>"
    "SendGrid email delivery  ·  Google Sheets &amp; Drive integration",
    S_COVER_SM))
story.append(sp(30))

# Gold divider line
story.append(Table([[""]], colWidths=[70], style=TableStyle([
    ("LINEABOVE", (0,0), (-1,-1), 3, GOLD),
    ("TOPPADDING", (0,0), (-1,-1), 0),
    ("BOTTOMPADDING", (0,0), (-1,-1), 0),
])))
story.append(sp(30))

# Bottom info row
cover_info = Table([
    [
        Paragraph("<b><font color='white'>Tech Stack</font></b><br/>"
                  "<font color='#94a3b8'>Python 3.10+  ·  FastAPI  ·  Anthropic Claude<br/>"
                  "WeasyPrint  ·  SendGrid  ·  Google APIs  ·  Pydantic v2</font>",
                  ParagraphStyle("ci", fontSize=9, textColor=colors.HexColor("#94a3b8"), leading=14)),
        Paragraph(f"<b><font color='white'>Generated</font></b><br/>"
                  f"<font color='#94a3b8'>{GENERATED_AT}<br/>"
                  f"github.com/Lalith9701/<br/>lead-automation-system</font>",
                  ParagraphStyle("ci2", fontSize=9, textColor=colors.HexColor("#94a3b8"),
                                 leading=14, alignment=TA_RIGHT)),
    ]
], colWidths=[(W-40*mm)*0.55, (W-40*mm)*0.45])
cover_info.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "BOTTOM"),
    ("TOPPADDING", (0,0), (-1,-1), 0),
    ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ("LEFTPADDING", (0,0), (-1,-1), 0),
    ("RIGHTPADDING", (0,0), (-1,-1), 0),
]))
story.append(cover_info)

story.append(NextPageTemplate("Content"))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS
# ══════════════════════════════════════════════════════════════════════════
story.append(Paragraph("Table of Contents", S_H1))
story.append(rule())
story.append(sp(6))

toc_items = [
    ("01", "Project Overview",          "What the system does, goals, and key features"),
    ("02", "System Architecture",       "Full pipeline diagram and component relationships"),
    ("03", "Project Structure",         "File tree with descriptions of every file"),
    ("04", "Tech Stack",                "All libraries, APIs, and tools used"),
    ("05", "API Reference",             "Endpoints, request/response schemas, validation rules"),
    ("06", "Pipeline Deep Dive",        "Step-by-step walkthrough of the automation pipeline"),
    ("07", "Data Models",               "Pydantic models, field types, and validation logic"),
    ("08", "Enrichment Service",        "6-step enrichment strategy and data sources"),
    ("09", "AI Report Generation",      "Claude prompt engineering and JSON parsing"),
    ("10", "PDF Generation",            "Jinja2 templating and WeasyPrint rendering"),
    ("11", "Email Delivery",            "SendGrid primary and SMTP fallback"),
    ("12", "Google Integrations",       "Sheets logging and Drive upload (bonus features)"),
    ("13", "Configuration & Env Vars",  "All environment variables and setup instructions"),
    ("14", "Error Handling",            "Resilience strategy, retries, and fallbacks"),
    ("15", "Running the Project",       "Installation, setup, and running locally"),
    ("16", "Assumptions & Tradeoffs",   "Design decisions, limitations, and future improvements"),
]

for num, title, desc in toc_items:
    row = Table([
        [
            Table([[Paragraph(f"<b>{num}</b>",
                ParagraphStyle("tn", fontSize=9, textColor=GOLD, fontName="Helvetica-Bold",
                               alignment=TA_CENTER))]],
                colWidths=[22], rowHeights=[22],
                style=TableStyle([
                    ("BACKGROUND", (0,0), (-1,-1), NAVY),
                    ("ROUNDEDCORNERS", [11]),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("TOPPADDING", (0,0), (-1,-1), 4),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ])),
            Table([[
                Paragraph(f"<b>{title}</b>", S_TOC_TITLE),
                Paragraph(desc, S_TOC_DESC),
            ]], colWidths=[(W-40*mm)-40],
            style=TableStyle([
                ("TOPPADDING", (0,0), (-1,-1), 2),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                ("LEFTPADDING", (0,0), (-1,-1), 0),
            ])),
        ]
    ], colWidths=[30, (W-40*mm)-30])
    row.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("LINEBELOW", (0,0), (-1,-1), 0.5, BORDER),
    ]))
    story.append(row)

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 01 — PROJECT OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("01", "Project Overview"))
story.append(sp(8))
story.append(callout(
    "Lead Automation System is a fully automated, end-to-end pipeline that captures a "
    "prospect's company details via a web form, enriches the data from multiple sources, "
    "generates a personalised AI-powered PDF audit report using Anthropic Claude, and emails "
    "it directly to the prospect — all without any human intervention."
))
story.append(sp(4))
story.append(h3("What Problem Does It Solve?"))
story.append(body(
    "Sales and marketing teams spend hours manually researching prospects, writing personalised "
    "outreach, and creating custom reports. This system eliminates that entirely. The moment a "
    "prospect submits a form, the pipeline fires automatically and delivers a professional, "
    "data-rich audit report to their inbox within minutes."
))
story.append(sp(4))
story.append(h3("Core Features"))
story.append(data_table(
    ["Feature", "Description", "Status"],
    [
        ["Lead Capture Form",        "Responsive HTML/CSS/JS form served at GET /",                          "Live"],
        ["Input Validation",         "Pydantic v2 with field-level error messages (422)",                    "Live"],
        ["Async Background Pipeline","FastAPI BackgroundTasks — instant 200 response",                       "Live"],
        ["Company Data Enrichment",  "6-source pipeline: scraping, Clearbit, DDG, LinkedIn, News, Tech",    "Live"],
        ["AI Report Generation",     "Claude claude-sonnet-4 — 7-section structured JSON report",           "Live"],
        ["PDF Rendering",            "Jinja2 HTML template → WeasyPrint PDF (10 pages)",                    "Live"],
        ["Email Delivery",           "SendGrid primary, SMTP fallback, HTML email + PDF attachment",        "Live"],
        ["Google Sheets Logging",    "Real-time status tracking across all pipeline stages",                "Bonus"],
        ["Google Drive Upload",      "PDF uploaded with public shareable link",                             "Bonus"],
        ["Swagger API Docs",         "Auto-generated at /docs and /redoc",                                  "Live"],
    ],
    col_widths=[110, 230, 55]
))
story.append(sp(4))
story.append(h3("Key Design Principles"))
for b in [
    "<b>Never crashes</b> — every step is individually try/excepted; the pipeline always completes as many stages as possible",
    "<b>Instant response</b> — the API returns 200 immediately; all heavy work runs in the background",
    "<b>Graceful degradation</b> — if enrichment returns little data, Claude generates the best possible report from what's available",
    "<b>Zero external CSS frameworks</b> — the form and PDF use hand-written CSS for zero dependency overhead",
    "<b>Opt-in integrations</b> — Google Sheets, Drive, Clearbit, and NewsAPI all work without keys; they enhance but don't block",
]:
    story.append(bullet(b))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 02 — SYSTEM ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("02", "System Architecture"))
story.append(sp(8))
story.append(code(
"""Browser (index.html)
        |
        |  POST /api/v1/submit-lead  (JSON body)
        v
+----------------------------------------------------------+
|                   FastAPI  (main.py)                     |
|  1. Validate lead with Pydantic v2                       |
|  2. Append row to Google Sheets  [status: processing]    |
|  3. Return HTTP 200 immediately                          |
|  4. Fire BackgroundTask ─────────────────────────────┐   |
+─────────────────────────────────────────────────────┼───+
                                                      |
                   Background Pipeline                v
          +──────────────────────────────────────────────+
          |  EnrichmentService                           |
          |  Step 1: Scrape homepage + /about            |
          |  Step 2: Clearbit Autocomplete (free)        |
          |  Step 2b: Clearbit Company API (if key set)  |
          |  Step 3: DuckDuckGo Instant Answer           |
          |  Step 4: LinkedIn (best-effort)              |
          |  Step 5: NewsAPI / Google News RSS           |
          |  Step 6: Tech-stack fingerprinting           |
          +──────────────────┬───────────────────────────+
                             v  [status: enriched]
          +──────────────────────────────────────────────+
          |  ReportGenerator — Claude claude-sonnet-4    |
          |  Build prompt → Call API → Parse JSON        |
          |  Render Jinja2 HTML → WeasyPrint PDF         |
          +──────────────────┬───────────────────────────+
                             v  [status: pdf_ready]
          +──────────────────────────────────────────────+
          |  DriveUploader → Google Drive (shareable URL)|
          +──────────────────┬───────────────────────────+
                             v  [status: uploaded]
          +──────────────────────────────────────────────+
          |  EmailSender → SendGrid (primary)            |
          |              → SMTP / Gmail (fallback)       |
          +──────────────────┬───────────────────────────+
                             v  [status: emailed → complete]
          +──────────────────────────────────────────────+
          |  SheetsLogger — update row at every stage    |
          +──────────────────────────────────────────────+"""
))
story.append(sp(6))
story.append(h3("Pipeline Status Flow"))
statuses = ["processing", "enriched", "report_generated", "pdf_ready", "uploaded", "emailed", "complete"]
status_row = [Paragraph(f"<b>{s}</b>",
    ParagraphStyle("st", fontSize=7.5, textColor=BLUE, backColor=BLUE_BG,
                   fontName="Helvetica-Bold", borderPadding=3, leading=11)) for s in statuses]
st = Table([status_row], colWidths=[(W-40*mm)/len(statuses)]*len(statuses))
st.setStyle(TableStyle([
    ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("GRID", (0,0), (-1,-1), 0.5, BORDER),
]))
story.append(st)
story.append(sp(6))
story.append(body_sm(
    "If any step fails, the status updates to &lt;step&gt;_failed with an error note in the "
    "Sheets row. The pipeline always continues to the next step."
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 03 — PROJECT STRUCTURE
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("03", "Project Structure"))
story.append(sp(8))
story.append(code(
"""lead-automation/
├── main.py                   # FastAPI app, static mount, health check
├── config.py                 # All env vars — single source of truth
├── requirements.txt          # 16 pinned dependencies
├── .env.example              # Template for .env — safe to commit
├── .gitignore                # Excludes .env, credentials/, output/
├── README.md                 # Full project documentation
│
├── api/
│   └── routes.py             # POST /api/v1/submit-lead + pipeline
│
├── models/
│   └── lead.py               # LeadSubmission, LeadResponse (Pydantic v2)
│
├── services/
│   ├── enrichment.py         # EnrichmentService — 6-step pipeline
│   ├── report_generator.py   # Claude API + WeasyPrint PDF rendering
│   ├── email_sender.py       # SendGrid primary, SMTP fallback
│   ├── sheets_logger.py      # gspread real-time row updates [bonus]
│   └── drive_uploader.py     # Google Drive upload + public link [bonus]
│
├── templates/
│   ├── report_template.html  # Jinja2 PDF template — 10 pages
│   ├── email_template.html   # Jinja2 HTML email template
│   └── index.html            # Lead intake form — vanilla CSS/JS
│
├── static/
│   └── styles.css            # WeasyPrint print overrides
│
└── utils/
    ├── helpers.py            # async_retry, safe_scrape, truncate_for_llm
    └── scraper.py            # Homepage, DuckDuckGo, News, tech stack"""
))
story.append(sp(6))
story.append(h3("File Responsibilities"))
story.append(data_table(
    ["File", "Responsibility", "~Lines"],
    [
        ["main.py",                    "App factory, route registration, static files, health check",       "75"],
        ["config.py",                  "Centralised env var loading — all modules import from here",        "45"],
        ["api/routes.py",              "Endpoint handler + full pipeline orchestration",                    "130"],
        ["models/lead.py",             "Input validation, URL normalisation, enum definitions",             "75"],
        ["services/enrichment.py",     "Multi-source enrichment, merge logic, confidence scoring",          "230"],
        ["services/report_generator.py","Claude prompt building, JSON parsing, PDF rendering",              "210"],
        ["services/email_sender.py",   "SendGrid + SMTP delivery, email template rendering",               "175"],
        ["services/sheets_logger.py",  "Lazy gspread init, header management, real-time updates",          "120"],
        ["services/drive_uploader.py", "Drive API upload, public permission setting",                      "75"],
        ["utils/helpers.py",           "Retry decorator, safe HTTP, text truncation, domain extraction",   "90"],
        ["utils/scraper.py",           "Homepage scraper, DuckDuckGo, Google News RSS, tech fingerprinting","140"],
    ],
    col_widths=[145, 215, 35]
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 04 — TECH STACK
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("04", "Tech Stack"))
story.append(sp(8))
story.append(data_table(
    ["Layer", "Library / Service", "Version", "Purpose"],
    [
        ["Web Framework",   "FastAPI",                    "0.136+",               "Async REST API, BackgroundTasks, auto Swagger docs"],
        ["ASGI Server",     "Uvicorn",                    "0.47+",                "Production-grade ASGI server with hot reload"],
        ["Validation",      "Pydantic v2",                "2.x",                  "Request body validation, field-level errors, URL validation"],
        ["AI / LLM",        "Anthropic Claude",           "claude-sonnet-4",      "7-section structured JSON report generation"],
        ["PDF Generation",  "WeasyPrint",                 "68+",                  "HTML/CSS to PDF rendering (server-side, no headless Chrome)"],
        ["Templating",      "Jinja2",                     "3.x",                  "PDF report template + HTML email template"],
        ["HTTP Client",     "httpx",                      "0.28+",                "Async HTTP for all external API calls and scraping"],
        ["HTML Parsing",    "BeautifulSoup4 + lxml",      "4.14+",                "Homepage scraping, meta extraction, tech fingerprinting"],
        ["Email (primary)", "SendGrid SDK",               "6.12+",                "Transactional email with PDF attachment"],
        ["Email (fallback)","smtplib (stdlib)",           "built-in",             "Gmail SMTP fallback when SendGrid unavailable"],
        ["Google Sheets",   "gspread",                    "6.2+",                 "Lead logging and real-time status tracking"],
        ["Google Drive",    "google-api-python-client",   "2.x",                  "PDF upload with public shareable link"],
        ["Config",          "python-dotenv",              "1.x",                  ".env file loading"],
    ],
    col_widths=[80, 110, 80, 125]
))
story.append(sp(6))
story.append(h3("External APIs Used"))
story.append(data_table(
    ["API", "Auth Required", "Free Tier", "Data Returned"],
    [
        ["Clearbit Autocomplete",    "No",           "Unlimited",        "Company name, domain, logo URL"],
        ["Clearbit Company API",     "API Key",      "Limited",          "Full profile: founded, employees, HQ, industry"],
        ["Clearbit Logo API",        "No",           "Unlimited",        "Company logo image"],
        ["DuckDuckGo Instant Answer","No",           "Unlimited",        "Short company description / abstract"],
        ["NewsAPI",                  "API Key",      "100 req/day",      "Recent news articles with title, source, date"],
        ["Google News RSS",          "No",           "Unlimited",        "Recent press mentions (RSS fallback)"],
        ["Anthropic Claude",         "API Key",      "Pay per token",    "7-section structured JSON report"],
        ["SendGrid",                 "API Key",      "100 emails/day",   "Transactional email delivery"],
        ["Google Sheets API",        "Service Acct", "Yes",              "Lead logging and status tracking"],
        ["Google Drive API",         "Service Acct", "15 GB storage",    "PDF upload with shareable link"],
    ],
    col_widths=[120, 75, 75, 125]
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 05 — API REFERENCE
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("05", "API Reference"))
story.append(sp(8))
story.append(h3("Available Endpoints"))
story.append(data_table(
    ["Method", "Path", "Description"],
    [
        ["GET",  "/",                      "Serve the lead intake HTML form"],
        ["POST", "/api/v1/submit-lead",    "Submit a lead — triggers the full automation pipeline"],
        ["GET",  "/health",                "Health check — returns {status: ok, version: 1.0.0}"],
        ["GET",  "/docs",                  "Swagger UI — interactive API documentation"],
        ["GET",  "/redoc",                 "ReDoc — alternative API documentation"],
        ["GET",  "/static/*",              "Static file serving (CSS, assets)"],
    ],
    col_widths=[50, 140, 205]
))
story.append(sp(6))
story.append(h3("POST /api/v1/submit-lead — Request Fields"))
story.append(data_table(
    ["Field", "Type", "Required", "Validation Rule"],
    [
        ["full_name",       "string",  "Yes",      "Min 2 characters, whitespace stripped"],
        ["email",           "string",  "Yes",      "Valid email format (RFC 5322 via Pydantic EmailStr)"],
        ["company_name",    "string",  "Yes",      "Min 1 character, whitespace stripped"],
        ["company_website", "string",  "Optional", "Valid URL; https:// prepended automatically if missing"],
        ["industry",        "string",  "Optional", "Free text"],
        ["company_size",    "enum",    "Optional", "One of: 1-10, 11-50, 51-200, 201-500, 500+"],
        ["role",            "string",  "Optional", "Free text (e.g. CEO, Marketing Head)"],
        ["message",         "string",  "Optional", "Free text — pain points or goals"],
    ],
    col_widths=[90, 55, 60, 190]
))
story.append(sp(6))
story.append(h3("Responses"))
story.append(data_table(
    ["HTTP Code", "When", "Body"],
    [
        ["200 OK",                  "Valid submission",         '{"status": "processing", "message": "Your report is being generated..."}'],
        ["422 Unprocessable Entity","Validation failure",       '{"detail": [{"loc": ["body", "email"], "msg": "...", "type": "..."}]}'],
        ["500 Internal Server Error","Unhandled exception",     '{"detail": "An internal error occurred. Please try again later."}'],
    ],
    col_widths=[80, 100, 215]
))
story.append(sp(4))
story.append(callout(
    "The 200 response is returned immediately before the pipeline runs. Enrichment, AI generation, "
    "PDF rendering, and email delivery all happen asynchronously in the background. The prospect "
    "receives their email within 30–120 seconds depending on API response times."
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 06 — PIPELINE DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("06", "Pipeline Deep Dive"))
story.append(sp(8))
story.append(body(
    "The pipeline is orchestrated in <b>api/routes.py</b> inside the <b>_run_pipeline()</b> "
    "async function. It runs as a FastAPI BackgroundTask — completely decoupled from the HTTP "
    "request/response cycle."
))
story.append(h3("Step 1 — Lead Capture & Validation"))
story.append(body(
    "When a POST request arrives, FastAPI automatically deserialises the JSON body into a "
    "<b>LeadSubmission</b> Pydantic model. Validation runs synchronously before the handler "
    "executes. On failure, FastAPI returns a 422 with field-level error details. On success, "
    "the handler converts the model to a plain dict via <b>lead.model_dump()</b>, logs the "
    "initial row to Google Sheets, and returns 200 immediately."
))
story.append(h3("Step 2 — Company Data Enrichment"))
story.append(body(
    "The <b>EnrichmentService.enrich()</b> method runs 6 steps in sequence. Each step is "
    "wrapped in try/except — failure of any step is logged and skipped. Results are merged "
    "into a single enriched dict using <b>_merge()</b>, which only overwrites None or empty "
    "values (never clobbers good data with worse data)."
))
story.append(data_table(
    ["#", "Step", "Source", "Data Gathered", "Key Required"],
    [
        ["1",  "Homepage Scrape",          "httpx + BS4",       "Title, meta description, H1/H2 headings, body text, /about text", "No"],
        ["2",  "Clearbit Autocomplete",    "Clearbit free API", "Company name, domain, logo URL",                                  "No"],
        ["2b", "Clearbit Company API",     "Clearbit paid API", "Founded year, employees, HQ, industry, social handles",           "Yes"],
        ["3",  "DuckDuckGo Instant Answer","DDG API (free)",    "Short company description / abstract",                            "No"],
        ["4",  "LinkedIn Scrape",          "httpx (best-effort)","LinkedIn URL, tagline if not blocked",                           "No"],
        ["5",  "News Fetch",               "NewsAPI / RSS",     "Up to 5 recent news articles with title, source, date",           "Optional"],
        ["6",  "Tech Stack Detection",     "HTML fingerprinting","Detected frameworks: React, Next.js, WordPress, etc. (21 patterns)","No"],
    ],
    col_widths=[18, 90, 80, 155, 52]
))
story.append(h3("Step 3 — AI Report Generation"))
story.append(body(
    "The <b>ReportGenerator.generate()</b> method builds a dynamic prompt combining lead data "
    "and enrichment data (truncated to 4,000 chars). Claude is instructed to respond with a "
    "specific 7-key JSON structure. The response is parsed with <b>_parse_json()</b> which "
    "strips markdown fences and tries substring extraction as a fallback. If parsing fails, "
    "the prompt is retried once with a stricter instruction. If it fails again, a minimal "
    "fallback report dict is used."
))
story.append(h3("Steps 4–6 — PDF, Drive, Email"))
story.append(body(
    "The PDF is rendered by loading the Jinja2 template, rendering it with the full context "
    "dict, then passing the HTML string to WeasyPrint. The PDF is saved to "
    "<b>output/reports/{company}_{timestamp}.pdf</b>. It is then optionally uploaded to "
    "Google Drive (if configured) and the shareable URL is included in the email. The email "
    "is sent via SendGrid with the PDF attached, falling back to SMTP if needed."
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 07 — DATA MODELS
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("07", "Data Models"))
story.append(sp(8))
story.append(h3("LeadSubmission — Input Validation Model"))
story.append(code(
"""class CompanySize(str, Enum):
    micro      = "1-10"
    small      = "11-50"
    medium     = "51-200"
    large      = "201-500"
    enterprise = "500+"

class LeadSubmission(BaseModel):
    full_name:       str                    # required, min_length=2
    email:           EmailStr               # required, RFC 5322 validated
    company_name:    str                    # required, min_length=1
    company_website: Optional[str] = None  # URL validated, https:// prepended
    industry:        Optional[str] = None
    company_size:    Optional[CompanySize] = None
    role:            Optional[str] = None
    message:         Optional[str] = None"""
))
story.append(h3("Enrichment Data Dict — Internal Structure"))
story.append(code(
"""enrichment_data = {
    "company_name":          str,
    "domain":                str | None,       # e.g. "acme.com"
    "description":           str | None,       # from meta tag or DuckDuckGo
    "industry":              str | None,
    "founded_year":          int | None,
    "employee_count":        str | None,       # e.g. "51-200"
    "hq_location":           str | None,       # e.g. "San Francisco, CA"
    "key_products_services": list[str],
    "recent_news":           list[dict],       # {title, source, published, url}
    "tech_stack":            list[str],        # e.g. ["React", "AWS", "HubSpot"]
    "social_media":          dict[str, str],   # {platform: url}
    "logo_url":              str | None,       # Clearbit Logo API URL
    "data_confidence":       str,              # "high" | "medium" | "low"
}"""
))
story.append(h3("Report Content Dict — Claude Output Schema"))
story.append(code(
"""report_content = {
    "executive_summary":      str,
    "company_overview": {
        "what_they_do":       str,
        "market_position":    str,
        "key_strengths":      list[str],
        "notable_achievements": str,
    },
    "digital_presence_audit": {
        "website_analysis":   str,
        "seo_observations":   str,
        "content_strategy":   str,
        "score":              str,   # e.g. "7/10"
        "recommendations":    list[str],
    },
    "competitive_landscape": {
        "market_overview":    str,
        "key_competitors":    list[str],
        "differentiators":    str,
        "threats_and_opportunities": str,
    },
    "growth_opportunities": [{
        "title":              str,
        "description":        str,
        "impact":             str,  # "High" | "Medium" | "Low"
        "effort":             str,  # "High" | "Medium" | "Low"
        "recommended_action": str,
    }],
    "tech_and_operations": {
        "current_stack_observations": str,
        "automation_gaps":    str,
        "recommended_tools":  list[str],
    },
    "action_plan": {
        "immediate_actions":       list[str],
        "short_term_30_60_days":   list[str],
        "long_term_90_plus_days":  list[str],
    },
    "closing_note":           str,
}"""
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 08 — ENRICHMENT SERVICE
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("08", "Enrichment Service"))
story.append(sp(8))
story.append(callout(
    "The EnrichmentService runs 6 independent steps in sequence. Every step is wrapped in "
    "try/except — if one fails, the error is logged and the pipeline continues with whatever "
    "data was already gathered. Results from all steps are merged into a single dict."
))
story.append(h3("_merge() Logic"))
story.append(body(
    "The <b>_merge(base, update)</b> function is the backbone of the enrichment pipeline. "
    "It merges the update dict into base with these rules:"
))
for b in [
    "<b>None / empty values</b> in update are skipped — never overwrite good data with nothing",
    "<b>Lists</b> are extended and deduplicated — tech stack items from multiple sources are combined",
    "<b>Dicts</b> are recursively merged — social media handles from different sources are combined",
    "<b>Scalars</b> only overwrite if the base value is falsy — first good value wins",
]:
    story.append(bullet(b))
story.append(sp(6))
story.append(h3("Tech Stack Detection — 21 Fingerprints"))
story.append(body(
    "Detection works by loading the homepage HTML and checking for known string patterns in "
    "script src attributes, meta tags, and inline content. No external service required."
))
tech_list = [
    "WordPress", "Shopify", "Wix", "Squarespace", "Webflow", "React", "Next.js",
    "Vue.js", "Angular", "jQuery", "Bootstrap", "Tailwind CSS", "Google Analytics",
    "Google Tag Manager", "HubSpot", "Intercom", "Stripe", "Cloudflare", "AWS",
    "Vercel", "Netlify",
]
# Render as a 3-column grid
rows = [tech_list[i:i+3] for i in range(0, len(tech_list), 3)]
tech_table_data = []
for row in rows:
    tech_table_data.append([
        Paragraph(f"<b>{t}</b>", ParagraphStyle("tt", fontSize=8.5, textColor=GOLD,
                  fontName="Helvetica-Bold", backColor=NAVY, borderPadding=4, leading=12))
        for t in (row + [""] * (3 - len(row)))
    ])
tt = Table(tech_table_data, colWidths=[(W-40*mm)/3]*3)
tt.setStyle(TableStyle([
    ("TOPPADDING",    (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ("RIGHTPADDING",  (0,0), (-1,-1), 8),
    ("GRID",          (0,0), (-1,-1), 0.5, BORDER),
    ("ROWBACKGROUNDS",(0,0), (-1,-1), [NAVY, colors.HexColor("#243560")]),
]))
story.append(tt)
story.append(sp(8))
story.append(h3("Confidence Scoring"))
story.append(data_table(
    ["Level", "Condition", "Claude Behaviour"],
    [
        ["High",   "6 or more of 9 key fields populated", "Full analysis with specific data references"],
        ["Medium", "3–5 of 9 key fields populated",       "Analysis with some assumptions noted"],
        ["Low",    "0–2 of 9 key fields populated",       "Prompt instructs Claude to make clearly-labelled reasonable assumptions"],
    ],
    col_widths=[55, 160, 180]
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 09 — AI REPORT GENERATION
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("09", "AI Report Generation"))
story.append(sp(8))
story.append(h3("System Prompt"))
story.append(code(
"""You are a senior business analyst and consultant. You write professional,
insightful business audit reports that help companies understand their
digital presence, competitive position, and growth opportunities.
Your tone is authoritative but approachable. You must tailor every
section specifically to the company provided — never use generic filler text."""
))
story.append(h3("Prompt Construction"))
story.append(body("The user prompt is built dynamically in <b>_build_prompt()</b> and includes:"))
for b in [
    "Prospect name, role, company, website, industry, size",
    "Full enrichment data (truncated to 4,000 chars via truncate_for_llm())",
    "Prospect's free-text message (pain points / goals)",
    "Data confidence level with conditional instruction for low-confidence cases",
    "The exact JSON schema Claude must return — 7 top-level keys",
]:
    story.append(bullet(b))
story.append(sp(6))
story.append(h3("JSON Parsing Strategy"))
story.append(data_table(
    ["Attempt", "Method", "Handles"],
    [
        ["1", "Strip markdown fences, direct json.loads()",          "Clean JSON responses"],
        ["2", "Find outermost { } block, parse substring",           "JSON wrapped in prose"],
        ["3", "Retry Claude with stricter prompt instruction",        "Malformed first response"],
        ["4", "Return _fallback_report() — minimal safe dict",       "Complete Claude failure"],
    ],
    col_widths=[50, 200, 145]
))
story.append(h3("Report Sections Generated by Claude"))
story.append(data_table(
    ["#", "Section", "Content"],
    [
        ["1", "Executive Summary",      "2–3 paragraph personalised overview of the company"],
        ["2", "Company Overview",       "What they do, market position, key strengths, achievements"],
        ["3", "Digital Presence Audit", "Website, SEO, content strategy, score /10, recommendations"],
        ["4", "Competitive Landscape",  "Market overview, competitors, differentiators, threats"],
        ["5", "Growth Opportunities",   "3–4 cards with Impact/Effort ratings and action steps"],
        ["6", "Tech & Operations",      "Stack observations, automation gaps, tool recommendations"],
        ["7", "Action Plan",            "Immediate / 30–60 day / 90+ day phased roadmap"],
    ],
    col_widths=[20, 120, 255]
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 10 — PDF GENERATION
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("10", "PDF Generation"))
story.append(sp(8))
story.append(callout(
    "WeasyPrint converts HTML + CSS to PDF entirely server-side. No headless Chrome, "
    "no Puppeteer, no browser required. The Jinja2 template is rendered first, then the "
    "resulting HTML string is passed directly to WeasyPrint."
))
story.append(h3("Rendering Pipeline"))
story.append(data_table(
    ["Step", "What Happens"],
    [
        ["1. Context build",  "Dict assembled with lead, enrichment, report, generated_at, logo_url, static_dir"],
        ["2. Jinja2 render",  "_jinja_env.get_template('report_template.html').render(**context) → HTML string"],
        ["3. WeasyPrint",     "HTML(string=html_content, base_url=BASE_DIR).write_pdf(output_path)"],
        ["4. CSS loading",    "static/styles.css loaded as WeasyPrint CSS object and passed as stylesheet"],
        ["5. Output",         "Saved to output/reports/{company}_{YYYYMMDD_HHMMSS}.pdf"],
    ],
    col_widths=[90, 305]
))
story.append(h3("Report Template — 10 Pages"))
story.append(data_table(
    ["Page", "Content", "Key Elements"],
    [
        ["1",  "Cover Page",            "Full-bleed navy gradient, company logo, gold badge, prospect details"],
        ["2",  "Table of Contents",     "7 numbered entries with descriptions, About This Report box"],
        ["3",  "Executive Summary",     "Gold left-border callout box, key facts strip (industry, HQ, size)"],
        ["4",  "Company Overview",      "2-column card grid, social links, product/service tags"],
        ["5",  "Digital Presence Audit","Score circle, SVG bar chart, 3 analysis blocks, recommendations"],
        ["6",  "Competitive Landscape", "Market callout, competitor pill tags, differentiators vs threats"],
        ["7",  "Growth Opportunities",  "Opportunity cards with Impact/Effort colour badges"],
        ["8",  "Tech & Operations",     "2-column cards, detected tech stack tags, recommended tools"],
        ["9",  "Action Plan",           "3-column colour-coded timeline, personal closing note, news feed"],
        ["10", "Disclaimer",            "Data sources table, legal notice, branded footer strip"],
    ],
    col_widths=[30, 110, 255]
))
story.append(h3("WeasyPrint CSS Notes"))
for b in [
    "@page content rule adds running footer on every page (left: confidential label, right: page number + date)",
    "@page cover suppresses the footer on the cover page",
    "page-break-inside: avoid applied to all cards and multi-column blocks",
    "-webkit-print-color-adjust: exact forces background colours to render in PDF",
    "All CSS is inline in the template for maximum WeasyPrint compatibility",
    "SVG bar chart uses percentage-based widths — no external chart libraries needed",
]:
    story.append(bullet(b))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 11 — EMAIL DELIVERY
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("11", "Email Delivery"))
story.append(sp(8))
story.append(body(
    "The <b>EmailSender.send_report()</b> method tries SendGrid first. If SendGrid is not "
    "configured or returns an error, it automatically falls back to SMTP. Both paths use "
    "the same rendered HTML email body and PDF attachment."
))
story.append(data_table(
    ["Provider", "When Used", "Config Required", "Free Tier"],
    [
        ["SendGrid", "Primary — when SENDGRID_API_KEY is set",       "SENDGRID_API_KEY, FROM_EMAIL", "100 emails/day"],
        ["SMTP/Gmail","Fallback — when SendGrid fails or key missing","SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD", "Gmail free tier"],
    ],
    col_widths=[65, 145, 145, 40]
))
story.append(h3("Email Content"))
story.append(data_table(
    ["Element", "Content"],
    [
        ["Subject",      "Your Personalized Business Audit Report — {company_name}"],
        ["Greeting",     "Personalised with first name extracted from full_name"],
        ["Teaser",       "First 300 chars of executive summary + first growth opportunity title"],
        ["Digital score","Highlighted score from the digital presence audit section"],
        ["CTA button",   "View Your Full Report — links to Google Drive URL if available"],
        ["Attachment",   "PDF file attached directly to the email"],
        ["Footer",       "Sender name, email, and disclaimer text"],
    ],
    col_widths=[90, 305]
))
story.append(h3("Gmail SMTP Setup"))
story.append(body(
    "To use Gmail as the SMTP fallback, you must use an <b>App Password</b> (not your regular "
    "Gmail password). Enable 2-factor authentication on your Google account, then generate an "
    "App Password at <b>myaccount.google.com/apppasswords</b>. Use that 16-character password "
    "as SMTP_PASSWORD in your .env file."
))
story.append(h3("SendGrid Sender Verification"))
story.append(body(
    "SendGrid requires the FROM_EMAIL address to be verified as a sender. Go to "
    "<b>app.sendgrid.com → Settings → Sender Authentication</b> and verify your domain or "
    "single sender address before emails will be delivered."
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 12 — GOOGLE INTEGRATIONS
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("12", "Google Integrations"))
story.append(sp(8))
story.append(callout(
    "Both Google Sheets logging and Google Drive upload are fully optional bonus features. "
    "The core pipeline works completely without them. They activate automatically when the "
    "relevant environment variables are set."
))
story.append(h3("Google Sheets — Lead Logging Columns"))
story.append(data_table(
    ["Column", "Field", "Updated When"],
    [
        ["A", "Timestamp",            "On lead submission"],
        ["B", "Full Name",            "On lead submission"],
        ["C", "Email",                "On lead submission"],
        ["D", "Company",              "On lead submission"],
        ["E", "Website",              "On lead submission"],
        ["F", "Industry",             "On lead submission"],
        ["G", "Role",                 "On lead submission"],
        ["H", "Report Status",        "Updated at every pipeline stage"],
        ["I", "PDF Path",             "After PDF is rendered"],
        ["J", "Drive URL",            "After Drive upload"],
        ["K", "Enrichment Confidence","After enrichment completes"],
        ["L", "Error Notes",          "If any step fails"],
    ],
    col_widths=[40, 120, 235]
))
story.append(h3("Google Drive — PDF Upload"))
story.append(body(
    "The <b>DriveUploader</b> class uses the Google Drive v3 API to upload the generated PDF "
    "to a configured folder. After upload, it sets the file permission to "
    "<b>anyone with link can view</b> and returns the shareable URL. This URL is then "
    "included in the email as the CTA button link."
))
story.append(h3("Service Account Setup — Step by Step"))
steps = [
    "Go to Google Cloud Console → Create or select a project",
    "Enable Google Sheets API and Google Drive API",
    "Go to IAM & Admin → Service Accounts → Create service account",
    "Download the JSON key file → save to ./credentials/service_account.json",
    "Copy the service account email (e.g. name@project.iam.gserviceaccount.com)",
    "Share your Google Sheet with that email (Editor role)",
    "Share your Drive folder with that email (Editor role)",
    "Set GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SHEET_ID, GOOGLE_DRIVE_FOLDER_ID in .env",
]
for i, s in enumerate(steps, 1):
    story.append(Paragraph(f"{i}. {s}", S_BULLET))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 13 — CONFIGURATION & ENV VARS
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("13", "Configuration & Environment Variables"))
story.append(sp(8))
story.append(body(
    "All configuration is loaded in <b>config.py</b> via python-dotenv. Every other module "
    "imports from config — os.environ is never read directly anywhere else in the codebase."
))
story.append(data_table(
    ["Variable", "Required", "Default", "Description"],
    [
        ["ANTHROPIC_API_KEY",          "Required",  "—",                              "Anthropic API key. Get from console.anthropic.com"],
        ["SENDGRID_API_KEY",           "Or SMTP",   "—",                              "SendGrid API key. Get from app.sendgrid.com"],
        ["FROM_EMAIL",                 "Required",  "noreply@example.com",            "Verified sender email address"],
        ["FROM_NAME",                  "Required",  "Lead Automation",                "Sender display name in email"],
        ["SMTP_HOST",                  "Fallback",  "smtp.gmail.com",                 "SMTP server hostname"],
        ["SMTP_PORT",                  "Fallback",  "587",                            "SMTP port (587 for TLS)"],
        ["SMTP_USER",                  "Fallback",  "—",                              "SMTP username / Gmail address"],
        ["SMTP_PASSWORD",              "Fallback",  "—",                              "SMTP password / Gmail App Password"],
        ["CLEARBIT_API_KEY",           "Optional",  "—",                              "Enables full Clearbit Company API enrichment"],
        ["NEWS_API_KEY",               "Optional",  "—",                              "NewsAPI key. Free tier: 100 req/day"],
        ["GOOGLE_SERVICE_ACCOUNT_JSON","Bonus",     "./credentials/service_account.json","Path to Google service account JSON key"],
        ["GOOGLE_SHEET_ID",            "Bonus",     "—",                              "Google Sheet ID (from the URL)"],
        ["GOOGLE_DRIVE_FOLDER_ID",     "Bonus",     "—",                              "Google Drive folder ID for PDF uploads"],
        ["PORT",                       "Optional",  "8000",                           "Server port for uvicorn"],
        ["OUTPUT_DIR",                 "Optional",  "./output/reports",               "Directory where generated PDFs are saved"],
    ],
    col_widths=[120, 55, 100, 120]
))
story.append(h3("Minimum Required Configuration"))
story.append(body("To run the full pipeline end-to-end, you need at minimum:"))
story.append(code(
"""ANTHROPIC_API_KEY=sk-ant-...        # for AI report generation
SENDGRID_API_KEY=SG....             # for email delivery
FROM_EMAIL=you@yourdomain.com       # verified sender address
FROM_NAME=Your Company Name"""
))
story.append(body_sm(
    "Everything else is optional and degrades gracefully when not set. "
    "The enrichment pipeline, form, and PDF rendering all work without any optional keys."
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 14 — ERROR HANDLING
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("14", "Error Handling & Resilience"))
story.append(sp(8))
story.append(callout(
    "The system is designed to never fully crash. Every external call is individually wrapped "
    "in try/except. If a step fails, the error is logged, the Sheets row is updated with the "
    "failure reason, and the pipeline continues to the next step."
))
story.append(h3("async_retry Decorator"))
story.append(body(
    "Located in <b>utils/helpers.py</b>, the @async_retry decorator wraps any async function "
    "with exponential back-off retry logic:"
))
story.append(code(
"""@async_retry(retries=3, delay=1.0)
async def my_api_call():
    ...

# Retry schedule:
# Attempt 1 → wait 1s → Attempt 2 → wait 2s → Attempt 3
# If all 3 fail, the last exception is re-raised"""))
story.append(h3("safe_scrape Helper"))
story.append(body("All web scraping goes through <b>safe_scrape(url)</b> which:"))
for b in [
    "Sets a 10-second timeout on every request",
    "Sends browser-like headers (User-Agent, Accept, Accept-Language) to reduce blocking",
    "Follows redirects automatically",
    "Returns None on any exception — never raises, never crashes the pipeline",
]:
    story.append(bullet(b))
story.append(sp(6))
story.append(h3("Failure Behaviour Per Pipeline Step"))
story.append(data_table(
    ["Step", "On Failure", "Pipeline Continues?"],
    [
        ["Enrichment (any sub-step)",  "Log warning, skip that source, continue with partial data",          "Yes"],
        ["Enrichment (entire service)","Log error, use empty enrichment dict, update Sheets",                "Yes"],
        ["Claude API call",            "Retry once with stricter prompt, then use fallback report dict",     "Yes"],
        ["JSON parsing",               "Try substring extraction, retry Claude, use fallback dict",          "Yes"],
        ["PDF rendering",              "Log error, skip email step, update Sheets as pdf_failed",            "Partial"],
        ["Drive upload",               "Log warning, continue without Drive URL in email",                   "Yes"],
        ["SendGrid email",             "Fall back to SMTP automatically",                                    "Yes"],
        ["SMTP email",                 "Log error, mark email_failed in Sheets, do not re-raise",            "Yes"],
        ["Sheets logging",             "Log warning, silently skip — never blocks pipeline",                 "Yes"],
    ],
    col_widths=[120, 215, 60]
))
story.append(h3("truncate_for_llm"))
story.append(body(
    "Scraped text is truncated before being sent to Claude using "
    "<b>truncate_for_llm(text, max_chars=3000)</b>. It breaks at a word boundary (not "
    "mid-word) and appends '… [truncated]'. This prevents token overflow and keeps "
    "API costs predictable."
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 15 — RUNNING THE PROJECT
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("15", "Running the Project"))
story.append(sp(8))
story.append(h3("1. Clone the Repository"))
story.append(code(
"""git clone https://github.com/Lalith9701/lead-automation-system.git
cd lead-automation-system"""))
story.append(h3("2. Create Virtual Environment"))
story.append(code(
"""python -m venv .venv

# Windows
.venv\\Scripts\\activate

# macOS / Linux
source .venv/bin/activate"""))
story.append(h3("3. Install Dependencies"))
story.append(code("pip install -r requirements.txt"))
story.append(h3("4. WeasyPrint System Dependencies"))
story.append(code(
"""# Windows — install GTK3 runtime first:
# https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

# macOS
brew install pango

# Ubuntu / Debian
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0"""))
story.append(h3("5. Configure Environment"))
story.append(code(
"""# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env

# Then edit .env and fill in your API keys"""))
story.append(h3("6. Run the Server"))
story.append(code("uvicorn main:app --reload --port 8000"))
story.append(h3("7. Access the Application"))
story.append(data_table(
    ["URL", "Description"],
    [
        ["http://localhost:8000",       "Lead intake form"],
        ["http://localhost:8000/docs",  "Swagger UI — interactive API docs"],
        ["http://localhost:8000/redoc", "ReDoc API documentation"],
        ["http://localhost:8000/health","Health check — returns {status: ok, version: 1.0.0}"],
    ],
    col_widths=[175, 220]
))
story.append(h3("8. Test the Pipeline via curl"))
story.append(code(
"""curl -X POST http://localhost:8000/api/v1/submit-lead \\
  -H "Content-Type: application/json" \\
  -d '{
    "full_name": "Jane Smith",
    "email": "jane@acme.com",
    "company_name": "Acme Corp",
    "company_website": "https://acme.com",
    "industry": "SaaS",
    "company_size": "51-200",
    "role": "CEO",
    "message": "We want to improve our SEO."
  }'

# Expected response:
{"status": "processing", "message": "Your report is being generated..."}"""))
story.append(body_sm(
    "After submitting, watch the server logs — you will see each pipeline step execute in "
    "real time. The generated PDF will appear in output/reports/."
))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# 16 — ASSUMPTIONS & TRADEOFFS
# ══════════════════════════════════════════════════════════════════════════
story.append(sec("16", "Assumptions & Tradeoffs"))
story.append(sp(8))
story.append(h3("Design Assumptions"))
story.append(data_table(
    ["Area", "Assumption", "Rationale"],
    [
        ["Clearbit free tier",   "Autocomplete endpoint always called without a key",          "Publicly accessible, returns useful logo + domain data"],
        ["LinkedIn scraping",    "Best-effort only — expected to fail most of the time",       "LinkedIn aggressively blocks bots; pipeline continues gracefully"],
        ["WeasyPrint CSS",       "All CSS is inline in the template",                          "WeasyPrint has limited external stylesheet support"],
        ["Claude model",         "claude-sonnet-4-20250514 used by default",                  "Best balance of quality and speed; configurable in config.py"],
        ["Output directory",     "./output/reports/ created automatically on startup",         "Avoids manual setup step for new deployments"],
        ["Google features",      "Fully opt-in — pipeline works without Google credentials",   "Reduces setup friction for users who don't need logging/Drive"],
        ["Background tasks",     "FastAPI BackgroundTasks used for pipeline execution",        "Simple, in-process, zero infrastructure — good for low-medium volume"],
        ["PDF storage",          "PDFs saved to local filesystem",                             "Simple default; replace with S3 for production scale"],
    ],
    col_widths=[85, 145, 165]
))
story.append(h3("Tradeoffs"))
story.append(data_table(
    ["Decision", "Benefit", "Limitation"],
    [
        ["WeasyPrint over headless Chrome", "No browser dependency, lighter, faster startup",    "Limited CSS support — flexbox/grid partially supported"],
        ["Single Claude call + 1 retry",    "Fast, low cost, simple",                            "Complex JSON can occasionally fail parsing on first attempt"],
        ["Multi-source enrichment",         "More data, higher confidence scores",               "Slower (3–8s total); all steps are async to mitigate"],
        ["SendGrid → SMTP fallback",        "Reliable delivery with automatic failover",         "SMTP requires Gmail App Password setup"],
        ["FastAPI BackgroundTasks",         "Zero infrastructure, simple deployment",            "Tasks lost on server restart; use Celery+Redis for production"],
        ["Local PDF storage",               "No cloud setup required",                           "Not suitable for multi-instance deployments"],
    ],
    col_widths=[120, 140, 135]
))
story.append(h3("How to Scale to Production"))
story.append(data_table(
    ["Component", "Current", "Production Recommendation"],
    [
        ["Task queue",      "FastAPI BackgroundTasks",  "Celery + Redis or AWS SQS"],
        ["PDF storage",     "Local filesystem",         "AWS S3 or Google Cloud Storage"],
        ["State persistence","Google Sheets (optional)","PostgreSQL with SQLAlchemy"],
        ["Rate limiting",   "None",                     "slowapi middleware on /submit-lead"],
        ["Authentication",  "None (open endpoint)",     "API key header or OAuth2"],
        ["Monitoring",      "Python logging to stdout", "Sentry for errors, Datadog for metrics"],
        ["Deployment",      "uvicorn locally",          "Docker + Gunicorn + Nginx or AWS ECS"],
        ["Secrets",         ".env file",                "AWS Secrets Manager or HashiCorp Vault"],
    ],
    col_widths=[90, 130, 175]
))
story.append(h3("Extending the System"))
for b in [
    "<b>New enrichment source:</b> Add a method to EnrichmentService, call it in enrich(), merge with _merge()",
    "<b>New email provider:</b> Add _send_&lt;provider&gt;() to EmailSender, update dispatch logic in send_report()",
    "<b>New report section:</b> Extend JSON schema in _build_prompt(), add HTML block to report_template.html",
    "<b>CRM webhook:</b> Add a step in _run_pipeline() after email to POST lead data to HubSpot/Salesforce",
    "<b>Multi-language reports:</b> Pass a language field in the lead form and include it in the Claude system prompt",
    "<b>Report caching:</b> Hash the company domain and cache enrichment data in Redis to avoid re-scraping",
]:
    story.append(bullet(b))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# CLOSING / QUICK REFERENCE PAGE
# ══════════════════════════════════════════════════════════════════════════
story.append(Paragraph("Quick Reference Summary", S_H1))
story.append(rule())
story.append(sp(8))

# 3-column summary
col_w = (W - 40*mm) / 3 - 4

pipeline_steps = [
    "1. Lead form submission",
    "2. Pydantic v2 validation",
    "3. Instant 200 response",
    "4. Company enrichment (6 sources)",
    "5. Claude AI report generation",
    "6. WeasyPrint PDF rendering",
    "7. Google Drive upload",
    "8. SendGrid / SMTP email",
    "9. Sheets status logging",
]
key_files = [
    "main.py — App entry point",
    "config.py — All settings",
    "api/routes.py — Endpoint + pipeline",
    "models/lead.py — Validation",
    "services/enrichment.py",
    "services/report_generator.py",
    "services/email_sender.py",
    "templates/report_template.html",
    "utils/helpers.py — Retry / scrape",
]
min_config = [
    "ANTHROPIC_API_KEY",
    "  → AI report generation",
    "",
    "SENDGRID_API_KEY",
    "  → Email delivery",
    "",
    "FROM_EMAIL",
    "  → Verified sender",
    "",
    "FROM_NAME",
    "  → Sender display name",
]

def summary_col(title, items):
    content = [Paragraph(f"<b>{title}</b>",
        ParagraphStyle("sc", fontSize=8, textColor=GOLD, fontName="Helvetica-Bold",
                       leading=11, spaceAfter=6))]
    for item in items:
        if item:
            content.append(Paragraph(item,
                ParagraphStyle("si", fontSize=8.5, textColor=SLATE, leading=13,
                               fontName="Courier" if item.startswith("  ") else "Helvetica")))
        else:
            content.append(Spacer(1, 4))
    return content

summary = Table(
    [[summary_col("Core Pipeline", pipeline_steps),
      summary_col("Key Files", key_files),
      summary_col("Minimum Config", min_config)]],
    colWidths=[col_w, col_w, col_w],
)
summary.setStyle(TableStyle([
    ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ("TOPPADDING",    (0,0), (-1,-1), 12),
    ("BOTTOMPADDING", (0,0), (-1,-1), 12),
    ("LEFTPADDING",   (0,0), (-1,-1), 10),
    ("RIGHTPADDING",  (0,0), (-1,-1), 10),
    ("BACKGROUND",    (0,0), (-1,-1), LIGHT),
    ("GRID",          (0,0), (-1,-1), 0.5, BORDER),
    ("ROUNDEDCORNERS",[6]),
]))
story.append(summary)
story.append(sp(12))

# Start command
story.append(h3("Start the Server"))
story.append(code("uvicorn main:app --reload --port 8000"))
story.append(sp(12))

# Footer branding strip
footer_strip = Table(
    [[
        Paragraph(
            "<b><font color='#f59e0b'>Lead Automation System</font></b><br/>"
            "<font color='#94a3b8'>Automated · AI-Powered · Personalised<br/>"
            "github.com/Lalith9701/lead-automation-system</font>",
            ParagraphStyle("fs1", fontSize=9, textColor=colors.HexColor("#94a3b8"),
                           leading=14, backColor=NAVY)
        ),
        Paragraph(
            f"<font color='white'><b>Generated</b></font><br/>"
            f"<font color='#64748b'>{GENERATED_AT}<br/>"
            f"Full Technical Reference<br/>16 Sections · ReportLab PDF</font>",
            ParagraphStyle("fs2", fontSize=9, textColor=colors.HexColor("#64748b"),
                           leading=14, alignment=TA_RIGHT, backColor=NAVY)
        ),
    ]],
    colWidths=[(W-40*mm)*0.6, (W-40*mm)*0.4],
)
footer_strip.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,-1), NAVY),
    ("TOPPADDING",    (0,0), (-1,-1), 16),
    ("BOTTOMPADDING", (0,0), (-1,-1), 16),
    ("LEFTPADDING",   (0,0), (-1,-1), 18),
    ("RIGHTPADDING",  (0,0), (-1,-1), 18),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ("ROUNDEDCORNERS",[8]),
]))
story.append(footer_strip)

# ══════════════════════════════════════════════════════════════════════════
# BUILD PDF
# ══════════════════════════════════════════════════════════════════════════
print("Building PDF...")
doc.build(story)
size_kb = OUTPUT.stat().st_size / 1024
print(f"\nDone!")
print(f"Saved to : {OUTPUT}")
print(f"File size: {size_kb:.1f} KB")
print(f"Pages    : 16 sections + cover + TOC + closing")
