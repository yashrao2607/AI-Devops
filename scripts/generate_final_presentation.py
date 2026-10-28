import sys
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# -------------------------------------------------------------
# Color Palette: Premium Editorial Theme with High Contrast & Visual Clarity
# -------------------------------------------------------------
BG_COLOR = RGBColor(248, 250, 252)         # #F8FAFC Slate 50 ultra-clean background
CARD_BG = RGBColor(255, 255, 255)          # #FFFFFF Pure white card
CARD_BORDER = RGBColor(226, 232, 240)      # #E2E8F0 Clean subtle border
CARD_BORDER_DARK = RGBColor(203, 213, 225) # #CBD5E1 Slate 300 border
TEXT_MAIN = RGBColor(15, 23, 42)           # #0F172A Slate 900
TEXT_MUTED = RGBColor(51, 65, 85)          # #334155 Slate 700 readable body
TEXT_SUBTLE = RGBColor(100, 116, 139)      # #64748B Slate 500 caption
ACCENT_BLUE = RGBColor(37, 99, 235)        # #2563EB Primary Blue
ACCENT_NAVY = RGBColor(30, 58, 138)        # #1E3A8A Dark Navy
ACCENT_BG = RGBColor(239, 246, 255)        # #EFF6FF Soft Blue tint
BADGE_GRAY_BG = RGBColor(241, 245, 249)    # #F1F5F9 Badge background
CRITICAL_RED = RGBColor(220, 38, 38)       # #DC2626 Critical / Block
CRITICAL_BG = RGBColor(254, 242, 242)      # #FEF2F2 Critical tint
SUCCESS_GREEN = RGBColor(22, 163, 74)      # #16A34A Success / Pass
SUCCESS_BG = RGBColor(240, 253, 244)       # #F0FDF4 Green tint
CODE_BG = RGBColor(241, 245, 249)          # #F1F5F9 Code block background
PURPLE_ACCENT = RGBColor(126, 34, 206)     # #7E22CE Purple badge
PURPLE_BG = RGBColor(250, 245, 255)        # #FAF5FF Purple tint

FONT_FAMILY = "Segoe UI"
CODE_FONT = "Consolas"
TOTAL_SLIDES = 12

def create_presentation(output_path: str):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide):
        bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = BG_COLOR
        bg_shape.line.fill.background()
        return bg_shape

    def add_para(tf, text, size_pt=12, bold=False, color=TEXT_MAIN, space_after=4, font_name=FONT_FAMILY, align=PP_ALIGN.LEFT):
        p = tf.add_paragraph() if len(tf.paragraphs[0].text) > 0 else tf.paragraphs[0]
        p.alignment = align
        p.space_after = Pt(space_after)
        run = p.add_run()
        run.text = text
        run.font.name = font_name
        run.font.size = Pt(size_pt)
        run.font.bold = bold
        run.font.color.rgb = color
        return p

    def add_card(slide, left, top, width, height, bg=CARD_BG, border=CARD_BORDER, shape_type=MSO_SHAPE.ROUNDED_RECTANGLE):
        card = slide.shapes.add_shape(shape_type, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg
        card.line.color.rgb = border
        card.line.width = Pt(1.0)
        return card

    def add_textbox(slide, left, top, width, height, pad_x=0.0, pad_y=0.0):
        tb = slide.shapes.add_textbox(Inches(left + pad_x), Inches(top + pad_y), Inches(width - (2 * pad_x)), Inches(height - (2 * pad_y)))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0)
        tf.margin_right = Inches(0)
        tf.margin_top = Inches(0)
        tf.margin_bottom = Inches(0)
        return tb, tf

    def add_badge(slide, left, top, width, height, text, bg=BADGE_GRAY_BG, text_color=TEXT_MUTED, font_size=9):
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        badge.fill.solid()
        badge.fill.fore_color.rgb = bg
        badge.line.fill.background()
        tf = badge.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = text
        run.font.name = FONT_FAMILY
        run.font.size = Pt(font_size)
        run.font.bold = True
        run.font.color.rgb = text_color
        return badge

    def add_header(slide, slide_num, title, subtitle, category="DEPLOYSAFE — AGENTIC PRE-DEPLOYMENT RISK PLATFORM"):
        add_badge(slide, 0.8, 0.45, 4.4, 0.32, category, bg=ACCENT_BG, text_color=ACCENT_BLUE, font_size=9)
        
        # Slide number
        _, tf_num = add_textbox(slide, 11.5, 0.4, 1.0, 0.4)
        p_num = tf_num.paragraphs[0]
        p_num.alignment = PP_ALIGN.RIGHT
        r_num = p_num.add_run()
        r_num.text = f"{slide_num:02d} / {TOTAL_SLIDES:02d}"
        r_num.font.name = FONT_FAMILY
        r_num.font.size = Pt(11)
        r_num.font.bold = True
        r_num.font.color.rgb = TEXT_SUBTLE

        # Title
        _, tf_t = add_textbox(slide, 0.8, 0.85, 11.7, 0.8)
        add_para(tf_t, title, size_pt=22, bold=True, color=TEXT_MAIN, space_after=3)
        add_para(tf_t, subtitle, size_pt=12, bold=False, color=TEXT_MUTED, space_after=0)

    # =========================================================
    # SLIDE 1: Title Slide (Grand Hero Style)
    # =========================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    # Hero Banner Card
    add_card(s1, 0.8, 0.8, 11.733, 4.2, bg=CARD_BG, border=CARD_BORDER_DARK)
    _, tf1 = add_textbox(s1, 1.2, 1.15, 10.9, 3.5)
    
    add_para(tf1, "PROJECT FINAL DEFENSE & V2 PLATFORM RELEASE", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=10)
    add_para(tf1, "DeploySafe: Agentic AI Pre-Deployment Risk Platform", size_pt=28, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf1, "An intelligent safety shield that catches hidden production outages before you deploy.", size_pt=14, bold=False, color=TEXT_MUTED, space_after=18)
    add_para(tf1, "Eliminates deployment blind spots between Code, Docker, Cloud Configurations, and Dependencies using grounded, zero-hallucination multi-agent AI.", size_pt=12, bold=False, color=TEXT_MUTED, space_after=0)

    # 3 Metadata Cards at bottom
    m_y = 5.25
    m_w = 3.75
    m_h = 1.6
    
    # Mentor Card
    add_card(s1, 0.8, m_y, m_w, m_h, bg=CARD_BG)
    _, tf_m = add_textbox(s1, 1.05, m_y + 0.2, m_w - 0.5, m_h - 0.4)
    add_para(tf_m, "FACULTY MENTORS", size_pt=10, bold=True, color=TEXT_SUBTLE, space_after=4)
    add_para(tf_m, "Mr. Naveen Singla", size_pt=14, bold=True, color=TEXT_MAIN, space_after=2)
    add_para(tf_m, "& Dr. Kiran Khatter", size_pt=13, bold=True, color=TEXT_MUTED, space_after=0)

    # Tech Stack Card
    add_card(s1, 0.8 + m_w + 0.24, m_y, m_w, m_h, bg=CARD_BG)
    _, tf_t = add_textbox(s1, 1.05 + m_w + 0.24, m_y + 0.2, m_w - 0.5, m_h - 0.4)
    add_para(tf_t, "CORE FOUNDATION", size_pt=10, bold=True, color=TEXT_SUBTLE, space_after=4)
    add_para(tf_t, "LangGraph + ChromaDB RAG", size_pt=14, bold=True, color=TEXT_MAIN, space_after=2)
    add_para(tf_t, "FastAPI Backend + React 18 UI", size_pt=12, bold=False, color=TEXT_MUTED, space_after=0)

    # Release Status Card
    add_card(s1, 0.8 + (m_w * 2) + 0.48, m_y, m_w, m_h, bg=SUCCESS_BG, border=SUCCESS_GREEN)
    _, tf_s = add_textbox(s1, 1.05 + (m_w * 2) + 0.48, m_y + 0.2, m_w - 0.5, m_h - 0.4)
    add_para(tf_s, "SYSTEM STATUS", size_pt=10, bold=True, color=SUCCESS_GREEN, space_after=4)
    add_para(tf_s, "V2.0 Final Release: READY", size_pt=14, bold=True, color=SUCCESS_GREEN, space_after=2)
    add_para(tf_s, "98/98 Tests Passing • 0 Regressions", size_pt=12, bold=False, color=TEXT_MUTED, space_after=0)

    # =========================================================
    # SLIDE 2: The Core Problem
    # =========================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, 2, "The Pre-Deployment Blind Spot: Why Good Code Breaks", "Over 65% of catastrophic production outages pass green through standard unit & lint tests.")

    col_w = 3.75
    col_gap = 0.24
    y_card = 1.95
    h_card = 4.9

    # Col 1: Siloed CI/CD
    add_card(s2, 0.8, y_card, col_w, h_card)
    add_badge(s2, 1.05, y_card + 0.25, 1.8, 0.28, "SILOED RUNNERS", bg=CRITICAL_BG, text_color=CRITICAL_RED, font_size=9)
    _, tf = add_textbox(s2, 1.05, y_card + 0.65, col_w - 0.5, h_card - 0.85)
    add_para(tf, "Tests Run in Isolation", size_pt=15, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf, "• Unit tests check small functions in isolation, but miss the big picture.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "• Linters check code style and semicolons, but cannot detect architectural drift.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "• A pull request can have 100% test pass rate while silently breaking Docker networking or database credentials.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Col 2: Seam Hazards
    x2 = 0.8 + col_w + col_gap
    add_card(s2, x2, y_card, col_w, h_card)
    add_badge(s2, x2 + 0.25, y_card + 0.25, 2.0, 0.28, "SEAM MISMATCHES", bg=CRITICAL_BG, text_color=CRITICAL_RED, font_size=9)
    _, tf2 = add_textbox(s2, x2 + 0.25, y_card + 0.65, col_w - 0.5, h_card - 0.85)
    add_para(tf2, "Breakages at the Seams", size_pt=15, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf2, "• Config Mismatches: Code consumes DATABASE_URL, but Docker defines DB_URL.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf2, "• Container Drift: Unpinned tags (:latest) update upstream and crash deployments.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf2, "• Security Leaks: Hardcoded API keys and unencrypted credentials slipping into git.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Col 3: Naive LLM Flaws
    x3 = x2 + col_w + col_gap
    add_card(s2, x3, y_card, col_w, h_card)
    add_badge(s2, x3 + 0.25, y_card + 0.25, 2.0, 0.28, "LLM HALLUCINATIONS", bg=CRITICAL_BG, text_color=CRITICAL_RED, font_size=9)
    _, tf3 = add_textbox(s2, x3 + 0.25, y_card + 0.65, col_w - 0.5, h_card - 0.85)
    add_para(tf3, "Why Raw AI Fails", size_pt=15, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf3, "• Generic LLMs hallucinate non-existent files and invent fake line numbers.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf3, "• Single prompts lack real code grounding and mathematical scoring.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf3, "• Developers get alert fatigue and immediately reject untrusted AI tools.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # =========================================================
    # SLIDE 3: Architectural Overview
    # =========================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, 3, "DeploySafe Solution: The Multi-Agent Safety Flow", "Dynamic planning, parallel domain agents, adversarial reflection, and deterministic safety gates.")

    step_w = 2.76
    step_gap = 0.23
    y_flow = 1.95
    h_flow = 4.9

    # Step 1: Ingestion & Planning
    add_card(s3, 0.8, y_flow, step_w, h_flow)
    add_badge(s3, 1.0, y_flow + 0.25, 1.4, 0.28, "STAGE 1", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf = add_textbox(s3, 1.0, y_flow + 0.65, step_w - 0.4, h_flow - 0.85)
    add_para(tf, "Dynamic Planning", size_pt=14, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "• Reads git commit diffs & file trees.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Scrubs secrets before sending to AI.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Planner activates only the agents needed for the modified files.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Safe limits: 2,000 files & 200MB.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Step 2: 5 Domain Agents
    x = 0.8 + step_w + step_gap
    add_card(s3, x, y_flow, step_w, h_flow)
    add_badge(s3, x + 0.2, y_flow + 0.25, 1.4, 0.28, "STAGE 2", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf = add_textbox(s3, x + 0.2, y_flow + 0.65, step_w - 0.4, h_flow - 0.85)
    add_para(tf, "Parallel Agents", size_pt=14, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "• Code Analysis Agent", size_pt=11, bold=True, color=TEXT_MAIN, space_after=4)
    add_para(tf, "• Config & Infra Agent", size_pt=11, bold=True, color=TEXT_MAIN, space_after=4)
    add_para(tf, "• Dependency & CVE Agent", size_pt=11, bold=True, color=TEXT_MAIN, space_after=4)
    add_para(tf, "• Test Path Coverage Agent", size_pt=11, bold=True, color=TEXT_MAIN, space_after=4)
    add_para(tf, "• Security & IAM Agent", size_pt=11, bold=True, color=TEXT_MAIN, space_after=4)
    add_para(tf, "• ChromaDB Vector RAG context injection.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Step 3: Critic Reflection
    x = x + step_w + step_gap
    add_card(s3, x, y_flow, step_w, h_flow, border=ACCENT_BLUE)
    add_badge(s3, x + 0.2, y_flow + 0.25, 1.8, 0.28, "STAGE 3 (CORE)", bg=PURPLE_BG, text_color=PURPLE_ACCENT)
    _, tf = add_textbox(s3, x + 0.2, y_flow + 0.65, step_w - 0.4, h_flow - 0.85)
    add_para(tf, "Critic Reflection", size_pt=14, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "• Adversarial audit of every candidate finding.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Physical File Existence check.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Line Number Range check.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Literal Code Snippet match.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Drops hallucinations to 0.0% false positives.", size_pt=11, bold=True, color=SUCCESS_GREEN, space_after=0)

    # Step 4: Scoring & Gating
    x = x + step_w + step_gap
    add_card(s3, x, y_flow, step_w, h_flow)
    add_badge(s3, x + 0.2, y_flow + 0.25, 1.4, 0.28, "STAGE 4", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf = add_textbox(s3, x + 0.2, y_flow + 0.65, step_w - 0.4, h_flow - 0.85)
    add_para(tf, "Gating & Output", size_pt=14, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "• Deterministic 0–100 mathematical risk score.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Automated Gate: ALLOWED, REVIEW_REQUIRED, BLOCKED.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Fingerprint Diff engine.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Emits CLI exit codes & CI status.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # =========================================================
    # SLIDE 4: The 5 Specialized Domain Agents
    # =========================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, 4, "Meet the 5 Specialized Domain Agents", "Each agent specializes in one critical aspect of your software repository.")

    card_w = 3.75
    card_gap = 0.24
    row1_y = 1.95
    row_h = 2.25

    # Agent 1: Code
    add_card(s4, 0.8, row1_y, card_w, row_h)
    _, tf = add_textbox(s4, 1.0, row1_y + 0.2, card_w - 0.4, row_h - 0.4)
    add_para(tf, "1. Code Quality Agent", size_pt=14, bold=True, color=ACCENT_BLUE, space_after=4)
    add_para(tf, "• Catches silent error swallowing, resource leaks, and unhandled async crashes.", size_pt=11, color=TEXT_MUTED, space_after=4)
    add_para(tf, "• Analyzes pull request changes against the full file context.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Agent 2: Config & Infra
    x2 = 0.8 + card_w + card_gap
    add_card(s4, x2, row1_y, card_w, row_h)
    _, tf = add_textbox(s4, x2 + 0.2, row1_y + 0.2, card_w - 0.4, row_h - 0.4)
    add_para(tf, "2. Config & Docker Agent", size_pt=14, bold=True, color=ACCENT_BLUE, space_after=4)
    add_para(tf, "• Scans Dockerfiles, compose configs, and Kubernetes manifests.", size_pt=11, color=TEXT_MUTED, space_after=4)
    add_para(tf, "• Catches unpinned container tags (:latest), root users, and debug flags.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Agent 3: Dependencies
    x3 = x2 + card_w + card_gap
    add_card(s4, x3, row1_y, card_w, row_h)
    _, tf = add_textbox(s4, x3 + 0.2, row1_y + 0.2, card_w - 0.4, row_h - 0.4)
    add_para(tf, "3. Dependency & CVE Agent", size_pt=14, bold=True, color=ACCENT_BLUE, space_after=4)
    add_para(tf, "• Inspects package.json, requirements.txt, and lockfiles.", size_pt=11, color=TEXT_MUTED, space_after=4)
    add_para(tf, "• Flags known CVE vulnerabilities and broken deprecated libraries.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Row 2 (2 wide cards)
    row2_y = 4.45
    card2_w = 5.74
    
    # Agent 4: Test Deficit
    add_card(s4, 0.8, row2_y, card2_w, row_h)
    _, tf = add_textbox(s4, 1.0, row2_y + 0.2, card2_w - 0.4, row_h - 0.4)
    add_para(tf, "4. Test Coverage Agent", size_pt=14, bold=True, color=ACCENT_BLUE, space_after=4)
    add_para(tf, "• Identifies untested critical paths modified in pull requests (auth, payments, billing).", size_pt=11, color=TEXT_MUTED, space_after=4)
    add_para(tf, "• Warns developers before risky modified code ships without regression tests.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Agent 5: Security & Secrets
    x_sec = 0.8 + card2_w + card_gap
    add_card(s4, x_sec, row2_y, card2_w, row_h)
    _, tf = add_textbox(s4, x_sec + 0.2, row2_y + 0.2, card2_w - 0.4, row_h - 0.4)
    add_para(tf, "5. Security & Secrets Agent", size_pt=14, bold=True, color=ACCENT_BLUE, space_after=4)
    add_para(tf, "• Detects leaked AWS/GCP tokens, private keys, database passwords, and JWT keys.", size_pt=11, color=TEXT_MUTED, space_after=4)
    add_para(tf, "• Identifies insecure wildcard CORS origins, SQL injection hazards, and open endpoints.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # =========================================================
    # SLIDE 5: Adversarial Reflection & Zero Hallucination
    # =========================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, 5, "Zero Hallucinations: The Critic Reflection Engine", "How DeploySafe achieves 100% evidence validity and 0.0% false positives on clean codebases.")

    # Left: Explanation Card
    add_card(s5, 0.8, 1.95, 5.7, 4.9)
    _, tf = add_textbox(s5, 1.05, 2.15, 5.2, 4.5)
    add_para(tf, "The 4-Point Physical Verification Gate", size_pt=16, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf, "Every finding must survive strict physical inspection before reaching developers:", size_pt=11, color=TEXT_MUTED, space_after=10)
    add_para(tf, "1. File Existence: Does the file really exist in the repository? If not -> REJECT.", size_pt=11, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "2. Line Number Bounds: Is the reported line number valid on disk? If out of bounds -> REJECT.", size_pt=11, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "3. Literal Code Match: Does the code snippet match the physical text? If mismatch -> REJECT.", size_pt=11, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "4. Evidence Grounding: Is this a genuine deployment hazard or trivial style nit? If nit -> REJECT.", size_pt=11, bold=True, color=TEXT_MAIN, space_after=0)

    # Right: Metric Verification Box
    add_card(s5, 6.8, 1.95, 5.733, 4.9, bg=CARD_BG, border=SUCCESS_GREEN)
    add_badge(s5, 7.1, 2.2, 2.5, 0.3, "EMPIRICAL BENCHMARK", bg=SUCCESS_BG, text_color=SUCCESS_GREEN)
    _, tf = add_textbox(s5, 7.1, 2.65, 5.133, 4.0)
    add_para(tf, "Proven on Clean Benchmark Repository", size_pt=16, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf, "• Unvalidated AI Candidates: 3 phantom findings generated by raw LLM prompts.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "• Critic Filter Verdict: All 3 dropped due to code mismatch.", size_pt=11, color=CRITICAL_RED, space_after=12)
    add_para(tf, "• Final Verified Findings on Clean Baseline: 0", size_pt=13, bold=True, color=SUCCESS_GREEN, space_after=6)
    add_para(tf, "• Final False Positive Rate: 0.0%", size_pt=14, bold=True, color=SUCCESS_GREEN, space_after=14)
    add_para(tf, "Key Takeaway: The Critic reflection step is what transforms DeploySafe from an untrusted toy into a trusted enterprise safety gate.", size_pt=11, color=TEXT_MAIN, space_after=0)

    # =========================================================
    # SLIDE 6: Vector RAG Subsystem
    # =========================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, 6, "Repository Context: Vector RAG Knowledge Base", "ChromaDB vector store providing architectural context so AI never misinterprets intentional code.")

    col_w = 3.75
    col_gap = 0.24
    y_card = 1.95
    h_card = 4.9

    # Col 1: Ingestion & Indexing
    add_card(s6, 0.8, y_card, col_w, h_card)
    add_badge(s6, 1.05, y_card + 0.25, 1.8, 0.28, "KNOWLEDGE BASE", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf = add_textbox(s6, 1.05, y_card + 0.65, col_w - 0.5, h_card - 0.85)
    add_para(tf, "Smart Document Ingestion", size_pt=15, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf, "• Indexes READMEs, architecture docs, runbooks, and API specs.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "• Primary Embedding: Google text-embedding-004 (768 dimensions).", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "• Fallback: Local deterministic hashing when API is offline.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Col 2: Vector Store
    x2 = 0.8 + col_w + col_gap
    add_card(s6, x2, y_card, col_w, h_card)
    add_badge(s6, x2 + 0.25, y_card + 0.25, 1.8, 0.28, "FAST RETRIEVAL", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf2 = add_textbox(s6, x2 + 0.25, y_card + 0.65, col_w - 0.5, h_card - 0.85)
    add_para(tf2, "Isolated ChromaDB Store", size_pt=15, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf2, "• Isolated Chroma collection per repository ID.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf2, "• Cosine similarity search with metadata filtering.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf2, "• Blazing fast retrieval: < 45ms per query.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Col 3: Agent Injection
    x3 = x2 + col_w + col_gap
    add_card(s6, x3, y_card, col_w, h_card)
    add_badge(s6, x3 + 0.25, y_card + 0.25, 1.8, 0.28, "ARCHITECTURAL FIT", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf3 = add_textbox(s6, x3 + 0.25, y_card + 0.65, col_w - 0.5, h_card - 0.85)
    add_para(tf3, "Context-Aware Agents", size_pt=15, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf3, "• Agents check architectural guidelines before flagging code.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf3, "• Understands custom microservice conventions and project patterns.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf3, "• Prevents false positives where unconventional code is intentional.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # =========================================================
    # SLIDE 7: Mathematical Risk Scoring & Gate Policies
    # =========================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, 7, "Mathematical Deterministic Risk Engine & Gate Policy", "Transparent, calibrated scoring formula replacing black-box AI sentiment.")

    # Left: Formula Card
    add_card(s7, 0.8, 1.95, 5.7, 4.9)
    _, tf_l = add_textbox(s7, 1.05, 2.15, 5.2, 1.0)
    add_para(tf_l, "Deterministic Scoring Formula", size_pt=16, bold=True, color=TEXT_MAIN, space_after=4)
    add_para(tf_l, "Mathematical score calculated strictly from critic-validated findings:", size_pt=11, color=TEXT_MUTED, space_after=0)
    
    # Formula Code Box
    add_card(s7, 1.05, 3.15, 5.2, 2.1, bg=CODE_BG, border=CARD_BORDER_DARK)
    _, tf_c = add_textbox(s7, 1.25, 3.3, 4.8, 1.8)
    add_para(tf_c, "Risk Score = Min(100, Σ (Weight_i * Multiplier_i))", size_pt=11, bold=True, color=ACCENT_NAVY, font_name=CODE_FONT, space_after=6)
    add_para(tf_c, "• CRITICAL finding : 35 points", size_pt=11, bold=True, color=CRITICAL_RED, font_name=CODE_FONT, space_after=3)
    add_para(tf_c, "• HIGH finding     : 25 points", size_pt=11, bold=True, color=CRITICAL_RED, font_name=CODE_FONT, space_after=3)
    add_para(tf_c, "• MEDIUM finding   : 15 points", size_pt=11, bold=False, color=TEXT_MUTED, font_name=CODE_FONT, space_after=3)
    add_para(tf_c, "• LOW finding      :  7 points", size_pt=11, bold=False, color=TEXT_MUTED, font_name=CODE_FONT, space_after=0)

    _, tf_sub = add_textbox(s7, 1.05, 5.45, 5.2, 1.2)
    add_para(tf_sub, "Zero Black-Box Guesswork: The exact same findings always yield the exact same score across runs with 100% mathematical reproducibility.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Right: Gate Policy Card
    add_card(s7, 6.8, 1.95, 5.733, 4.9)
    _, tf_r = add_textbox(s7, 7.05, 2.15, 5.2, 0.5)
    add_para(tf_r, "Automated Gate Thresholds", size_pt=16, bold=True, color=TEXT_MAIN, space_after=0)

    # Policy 1: ALLOWED
    add_card(s7, 7.05, 2.75, 5.233, 1.15, bg=SUCCESS_BG, border=SUCCESS_GREEN)
    _, tf_p1 = add_textbox(s7, 7.25, 2.85, 4.833, 0.95)
    add_para(tf_p1, "ALLOWED (Deploy Permitted)", size_pt=13, bold=True, color=SUCCESS_GREEN, space_after=3)
    add_para(tf_p1, "Score < 40 and Critical = 0 and High = 0. Production promotion allowed.", size_pt=10, color=TEXT_MUTED, space_after=0)

    # Policy 2: REVIEW_REQUIRED
    add_card(s7, 7.05, 4.05, 5.233, 1.15, bg=ACCENT_BG, border=ACCENT_BLUE)
    _, tf_p2 = add_textbox(s7, 7.25, 4.15, 4.833, 0.95)
    add_para(tf_p2, "REVIEW_REQUIRED (Manual Signoff Needed)", size_pt=13, bold=True, color=ACCENT_BLUE, space_after=3)
    add_para(tf_p2, "Score 40–69 or High <= 2. Engineering lead manual review required.", size_pt=10, color=TEXT_MUTED, space_after=0)

    # Policy 3: BLOCKED
    add_card(s7, 7.05, 5.35, 5.233, 1.15, bg=CRITICAL_BG, border=CRITICAL_RED)
    _, tf_p3 = add_textbox(s7, 7.25, 5.45, 4.833, 0.95)
    add_para(tf_p3, "BLOCKED (Deploy Halted)", size_pt=13, bold=True, color=CRITICAL_RED, space_after=3)
    add_para(tf_p3, "Score >= 70 or Critical >= 1. Hard blocker in CI/CD pipeline.", size_pt=10, color=TEXT_MUTED, space_after=0)

    # =========================================================
    # SLIDE 8: Phase 7 / V2 Enterprise Enhancements
    # =========================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, 8, "DeploySafe V2 (Phase 7): Enterprise Reliability & Intelligence", "Post-release enhancements: repository-level governance, blast radius, and historical analytics.")

    c_w = 2.76
    c_gap = 0.23
    y_v2 = 1.95
    h_v2 = 4.9

    # V2 Feature 1: Repo Config
    add_card(s8, 0.8, y_v2, c_w, h_v2)
    add_badge(s8, 0.95, y_v2 + 0.25, 1.8, 0.28, "V2 GOVERNANCE", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf = add_textbox(s8, 0.95, y_v2 + 0.65, c_w - 0.3, h_v2 - 0.8)
    add_para(tf, "deploysafe.yml", size_pt=14, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "• Version-controlled repo rules", size_pt=10, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Custom risk thresholds", size_pt=10, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Path exclusions & gate overrides", size_pt=10, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Traversal & injection defense", size_pt=10, bold=True, color=SUCCESS_GREEN, space_after=0)

    # V2 Feature 2: Change Impact
    x = 0.8 + c_w + c_gap
    add_card(s8, x, y_v2, c_w, h_v2)
    add_badge(s8, x + 0.15, y_v2 + 0.25, 1.8, 0.28, "V2 BLAST RADIUS", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf = add_textbox(s8, x + 0.15, y_v2 + 0.65, c_w - 0.3, h_v2 - 0.8)
    add_para(tf, "Change Impact", size_pt=14, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "• Physical blast radius mapping", size_pt=10, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Affected layer classification", size_pt=10, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Mandatory verification checks", size_pt=10, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Sub-10ms deterministic run", size_pt=10, bold=True, color=SUCCESS_GREEN, space_after=0)

    # V2 Feature 3: History
    x = x + c_w + c_gap
    add_card(s8, x, y_v2, c_w, h_v2)
    add_badge(s8, x + 0.15, y_v2 + 0.25, 1.8, 0.28, "V2 ANALYTICS", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf = add_textbox(s8, x + 0.15, y_v2 + 0.65, c_w - 0.3, h_v2 - 0.8)
    add_para(tf, "History Trends", size_pt=14, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "• Multi-run timeline telemetry", size_pt=10, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Recurring issue detection", size_pt=10, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Gate pass/fail block rates", size_pt=10, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Resolution velocity tracking", size_pt=10, color=TEXT_MUTED, space_after=0)

    # V2 Feature 4: Patch Preview
    x = x + c_w + c_gap
    add_card(s8, x, y_v2, c_w, h_v2)
    add_badge(s8, x + 0.15, y_v2 + 0.25, 1.8, 0.28, "V2 REMEDIATION", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf = add_textbox(s8, x + 0.15, y_v2 + 0.65, c_w - 0.3, h_v2 - 0.8)
    add_para(tf, "Patch Preview", size_pt=14, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "• Standard unified diff format", size_pt=10, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Non-destructive read-only", size_pt=10, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Human approval mandatory", size_pt=10, bold=True, color=CRITICAL_RED, space_after=6)
    add_para(tf, "• Zero autonomous commits", size_pt=10, color=TEXT_MUTED, space_after=0)

    # =========================================================
    # SLIDE 9: Human-in-the-Loop Safe Remediation
    # =========================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, 9, "Human-in-the-Loop Safe Remediation: No Autonomous Writes", "Why DeploySafe strictly isolates AI suggestions from autonomous production commits.")

    # Left: Philosophy Card
    add_card(s9, 0.8, 1.95, 5.7, 4.9)
    _, tf = add_textbox(s9, 1.05, 2.15, 5.2, 4.5)
    add_para(tf, "The Dangers of Autonomous Code Writes", size_pt=16, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf, "Allowing AI agents to commit code directly into deployment branches creates unacceptable enterprise risks:", size_pt=11, color=TEXT_MUTED, space_after=10)
    add_para(tf, "• Supply Chain Risk: Malicious pull requests or prompt injections could trick agents into injecting backdoors.", size_pt=11, color=CRITICAL_RED, space_after=8)
    add_para(tf, "• Semantic Regressions: AI fixes may resolve a lint error but subtly break runtime business logic.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "• Developer Ownership: Human engineers must always retain ultimate accountability over all code pushed to production.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Right: DeploySafe Solution Card
    add_card(s9, 6.8, 1.95, 5.733, 4.9, bg=CARD_BG, border=ACCENT_BLUE)
    add_badge(s9, 7.05, 2.2, 2.5, 0.3, "DEPLOYSAFE PROTOCOL", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf = add_textbox(s9, 7.05, 2.65, 5.233, 4.0)
    add_para(tf, "Actionable Unified Diff Previews", size_pt=16, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf, "1. Standard Unified Diff Output: Formatted exactly like git diff with line offsets (@@ -x,y +a,b @@).", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "2. Syntax Colored UI: Additions rendered in green, removals in red, right inside the web findings modal.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "3. Explicit Safety Disclaimer: Clearly labeled with amber banner requiring developer testing prior to merge.", size_pt=11, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "4. One-Click Copy: Engineers copy the patch, test locally, and commit with human provenance.", size_pt=11, color=SUCCESS_GREEN, space_after=0)

    # =========================================================
    # SLIDE 10: Empirical Benchmark & Verification
    # =========================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, 10, "Empirical Evaluation: Zero False Positives & Verified Metrics", "Rigorous benchmarking across 5 test repositories and 98 automated unit/integration tests.")

    # 4 Stat Cards on top
    stat_w = 2.76
    stat_gap = 0.23
    stat_y = 1.95
    stat_h = 1.5

    # Stat 1: 0% FP
    add_card(s10, 0.8, stat_y, stat_w, stat_h, bg=SUCCESS_BG, border=SUCCESS_GREEN)
    _, tf = add_textbox(s10, 0.95, stat_y + 0.15, stat_w - 0.3, stat_h - 0.3)
    add_para(tf, "FALSE POSITIVE RATE", size_pt=10, bold=True, color=SUCCESS_GREEN, space_after=2)
    add_para(tf, "0.0%", size_pt=24, bold=True, color=SUCCESS_GREEN, space_after=2)
    add_para(tf, "Zero phantom findings", size_pt=10, color=TEXT_MUTED, space_after=0)

    # Stat 2: 100% Evidence
    x = 0.8 + stat_w + stat_gap
    add_card(s10, x, stat_y, stat_w, stat_h, bg=SUCCESS_BG, border=SUCCESS_GREEN)
    _, tf = add_textbox(s10, x + 0.15, stat_y + 0.15, stat_w - 0.3, stat_h - 0.3)
    add_para(tf, "EVIDENCE VALIDITY", size_pt=10, bold=True, color=SUCCESS_GREEN, space_after=2)
    add_para(tf, "100.0%", size_pt=24, bold=True, color=SUCCESS_GREEN, space_after=2)
    add_para(tf, "All grounded in physical files", size_pt=10, color=TEXT_MUTED, space_after=0)

    # Stat 3: 80% Recall
    x = x + stat_w + stat_gap
    add_card(s10, x, stat_y, stat_w, stat_h, bg=ACCENT_BG, border=ACCENT_BLUE)
    _, tf = add_textbox(s10, x + 0.15, stat_y + 0.15, stat_w - 0.3, stat_h - 0.3)
    add_para(tf, "DETECTION RECALL", size_pt=10, bold=True, color=ACCENT_BLUE, space_after=2)
    add_para(tf, "80.0%", size_pt=24, bold=True, color=ACCENT_BLUE, space_after=2)
    add_para(tf, "4/5 target cases detected", size_pt=10, color=TEXT_MUTED, space_after=0)

    # Stat 4: 98/98 Tests
    x = x + stat_w + stat_gap
    add_card(s10, x, stat_y, stat_w, stat_h, bg=SUCCESS_BG, border=SUCCESS_GREEN)
    _, tf = add_textbox(s10, x + 0.15, stat_y + 0.15, stat_w - 0.3, stat_h - 0.3)
    add_para(tf, "REGRESSION SUITE", size_pt=10, bold=True, color=SUCCESS_GREEN, space_after=2)
    add_para(tf, "98 / 98", size_pt=24, bold=True, color=SUCCESS_GREEN, space_after=2)
    add_para(tf, "100% pass in 67.89s", size_pt=10, color=TEXT_MUTED, space_after=0)

    # Bottom Structured Table Container
    t_y = 3.65
    t_h = 3.2
    add_card(s10, 0.8, t_y, 11.733, t_h)
    _, tf_th = add_textbox(s10, 1.05, t_y + 0.15, 11.2, 0.4)
    add_para(tf_th, "Evaluation Benchmark Breakdown Across Physical Test Repositories", size_pt=13, bold=True, color=TEXT_MAIN, space_after=0)

    cases = [
        ("EVAL-01: Config Hazard", "Unpinned Docker tag & debug mode", "CRITICAL / HIGH", "PASS (100% Detected)"),
        ("EVAL-02: Secret Exposure", "AWS credentials & database password leak", "CRITICAL", "PASS (Scrubbed & Flagged)"),
        ("EVAL-03: Dependency CVE", "Outdated PyYAML with published CVEs", "HIGH", "PASS (Advisory Matched)"),
        ("EVAL-04: Test Coverage Deficit", "Untested financial / auth payment logic", "MEDIUM", "PASS (Missing Test Flagged)"),
        ("EVAL-05: Clean Baseline", "Production-hardened clean repository", "NONE (Clean)", "PASS (0.0% False Positives)")
    ]
    row_top = t_y + 0.6
    for idx, c in enumerate(cases):
        row_y = row_top + (idx * 0.48)
        bg_c = CARD_BG if idx % 2 == 0 else BADGE_GRAY_BG
        add_card(s10, 1.05, row_y, 11.233, 0.42, bg=bg_c, border=CARD_BORDER)
        
        _, tf_r = add_textbox(s10, 1.2, row_y + 0.08, 3.2, 0.3)
        add_para(tf_r, c[0], size_pt=10, bold=True, color=TEXT_MAIN, space_after=0)
        
        _, tf_d = add_textbox(s10, 4.4, row_y + 0.08, 3.8, 0.3)
        add_para(tf_d, c[1], size_pt=10, bold=False, color=TEXT_MUTED, space_after=0)
        
        _, tf_s = add_textbox(s10, 8.2, row_y + 0.08, 1.8, 0.3)
        add_para(tf_s, c[2], size_pt=9, bold=True, color=ACCENT_BLUE, space_after=0)
        
        _, tf_p = add_textbox(s10, 10.0, row_y + 0.08, 2.2, 0.3)
        add_para(tf_p, c[3], size_pt=9, bold=True, color=SUCCESS_GREEN, space_after=0)

    # =========================================================
    # SLIDE 11: Production Implementation & Live System
    # =========================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, 11, "Production System Implementation & Developer Experience", "Clean full-stack delivery: FastAPI, React 18 / Vite SPA, CLI, and GitHub Action.")

    col_w = 3.75
    col_gap = 0.24
    y_card = 1.95
    h_card = 4.9

    # Col 1: Web Dashboard
    add_card(s11, 0.8, y_card, col_w, h_card)
    add_badge(s11, 1.05, y_card + 0.25, 1.8, 0.28, "WEB DASHBOARD", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf = add_textbox(s11, 1.05, y_card + 0.65, col_w - 0.5, h_card - 0.85)
    add_para(tf, "React 18 + Tailwind", size_pt=15, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf, "• Real-time SSE streaming for live agent step progress.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Interactive Findings filter by severity & category.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• Run Fingerprint comparison diff view.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• V2 Change Impact & Patch Preview modals.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf, "• 0 TypeScript errors; bundle built in 1m 41s.", size_pt=11, bold=True, color=SUCCESS_GREEN, space_after=0)

    # Col 2: REST API
    x2 = 0.8 + col_w + col_gap
    add_card(s11, x2, y_card, col_w, h_card)
    add_badge(s11, x2 + 0.25, y_card + 0.25, 1.8, 0.28, "BACKEND API", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf2 = add_textbox(s11, x2 + 0.25, y_card + 0.65, col_w - 0.5, h_card - 0.85)
    add_para(tf2, "FastAPI Service", size_pt=15, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf2, "• Asynchronous LangGraph pipeline execution.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf2, "• Ingestion of local repositories and Git clones.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf2, "• REST endpoints for runs, findings, impact, analytics.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf2, "• Sub-second response times for cached reports.", size_pt=11, color=TEXT_MUTED, space_after=0)

    # Col 3: CLI & GitHub Action
    x3 = x2 + col_w + col_gap
    add_card(s11, x3, y_card, col_w, h_card)
    add_badge(s11, x3 + 0.25, y_card + 0.25, 1.8, 0.28, "CI/CD INTEGRATION", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf3 = add_textbox(s11, x3 + 0.25, y_card + 0.65, col_w - 0.5, h_card - 0.85)
    add_para(tf3, "CLI & GitHub Action", size_pt=15, bold=True, color=TEXT_MAIN, space_after=8)
    add_para(tf3, "• deploysafe CLI command-line tool.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf3, "• Emits ANSI colored summaries and exit codes (0 pass, 1 blocked).", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf3, "• Seamless GitHub Action integration for pull request gating.", size_pt=11, color=TEXT_MUTED, space_after=6)
    add_para(tf3, "• Directly blocks unsafe PR merges.", size_pt=11, bold=True, color=TEXT_MAIN, space_after=0)

    # =========================================================
    # SLIDE 12: Viva Defense Summary & Academic Conclusion
    # =========================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, 12, "Viva Defense Summary & Project Conclusion", "Transforming pre-deployment safety validation through grounded, verifiable Agentic AI.")

    add_card(s12, 0.8, 1.95, 5.7, 4.9)
    _, tf = add_textbox(s12, 1.05, 2.15, 5.2, 4.5)
    add_para(tf, "Core Academic & Technical Contributions", size_pt=16, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf, "1. Cross-Boundary Seam Detection: Proved that multi-agent synthesis detects configuration and infrastructure hazards that bypass traditional CI test suites.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "2. Grounded Reflection Architecture: Demonstrated that adversarial Critic reflection completely eliminates false positives (0.0% on clean baseline).", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "3. Deterministic Safety Gating: Replaced ungrounded sentiment with reproducible 0–100 mathematical risk scoring and automated gate policies.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "4. V2 Enterprise Capabilities: Added repo governance (deploysafe.yml), deterministic blast radius (8.4ms), and human-approved patch diffs.", size_pt=11, color=TEXT_MUTED, space_after=0)

    add_card(s12, 6.8, 1.95, 5.733, 4.9, bg=CARD_BG, border=ACCENT_BLUE)
    add_badge(s12, 7.05, 2.2, 2.5, 0.3, "PROJECT DELIVERABLES", bg=ACCENT_BG, text_color=ACCENT_BLUE)
    _, tf = add_textbox(s12, 7.05, 2.65, 5.233, 4.0)
    add_para(tf, "Project Completion Summary", size_pt=16, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf, "• Mentors: Sincere gratitude to Mr. Naveen Singla & Dr. Kiran Khatter for architectural direction and guidance.", size_pt=11, color=TEXT_MAIN, space_after=8)
    add_para(tf, "• Versioning: v1.0.0 Final Academic Release preserved under Git Tag v1.0.0-final-submission.", size_pt=11, color=TEXT_MUTED, space_after=8)
    add_para(tf, "• V2 Status: Phase 7 Completed with 98/98 tests passing.", size_pt=11, bold=True, color=SUCCESS_GREEN, space_after=8)
    add_para(tf, "• Documentation: Complete Viva Guide, Demo Scripts, Architecture Docs, and Contribution Matrix verified.", size_pt=11, color=TEXT_MUTED, space_after=14)
    add_para(tf, "Thank you. Questions & Technical Demonstration Welcome.", size_pt=13, bold=True, color=ACCENT_BLUE, space_after=0)

    prs.save(output_path)
    print(f"Successfully generated new presentation at: {output_path}")

if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DeploySafe_Final_Presentation_V2.pptx")
    create_presentation(out_file)
