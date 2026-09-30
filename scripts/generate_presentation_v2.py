import sys
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# -------------------------------------------------------------
# Color Palette: Editorial / Technical Light Theme
# -------------------------------------------------------------
BG_COLOR = RGBColor(248, 249, 250)        # #F8F9FA Warm off-white
CARD_BG = RGBColor(255, 255, 255)         # #FFFFFF Crisp white
CARD_BORDER = RGBColor(226, 232, 240)     # #E2E8F0 Subtle border
CARD_BORDER_DARK = RGBColor(203, 213, 225)# #CBD5E1 Slate border
TEXT_MAIN = RGBColor(15, 23, 42)          # #0F172A Near-black / Charcoal
TEXT_MUTED = RGBColor(71, 85, 105)        # #475569 Slate body
TEXT_SUBTLE = RGBColor(148, 163, 184)     # #94A3B8 Caption / Footer
ACCENT_BLUE = RGBColor(37, 99, 235)       # #2563EB Restrained Indigo / Royal Blue
ACCENT_BG = RGBColor(239, 246, 255)       # #EFF6FF Soft blue tint
BADGE_GRAY_BG = RGBColor(241, 245, 249)   # #F1F5F9 Badge background
CRITICAL_RED = RGBColor(220, 38, 38)      # #DC2626 Critical / High
CRITICAL_BG = RGBColor(254, 242, 242)     # #FEF2F2 Critical tint
SUCCESS_GREEN = RGBColor(22, 163, 74)     # #16A34A Success / Validated
SUCCESS_BG = RGBColor(240, 253, 244)      # #F0FDF4 Green tint
CODE_BG = RGBColor(248, 250, 252)         # #F8FAFC Code block background

FONT_FAMILY = "Segoe UI"
CODE_FONT = "Consolas"

def create_presentation():
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

    def add_para(tf, text, size_pt=13, bold=False, color=TEXT_MAIN, space_after=6, font_name=FONT_FAMILY, align=PP_ALIGN.LEFT):
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
        if border:
            card.line.color.rgb = border
            card.line.width = Pt(1.0)
        else:
            card.line.fill.background()
        return card

    def add_header(slide, title, subtitle=None, slide_num=None):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.55), Inches(11.733), Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.space_after = Pt(4)
        run1 = p1.add_run()
        run1.text = title
        run1.font.name = FONT_FAMILY
        run1.font.size = Pt(28)
        run1.font.bold = True
        run1.font.color.rgb = TEXT_MAIN

        if subtitle:
            p2 = tf.add_paragraph()
            p2.space_after = Pt(0)
            run2 = p2.add_run()
            run2.text = subtitle
            run2.font.name = FONT_FAMILY
            run2.font.size = Pt(14)
            run2.font.bold = False
            run2.font.color.rgb = TEXT_MUTED

    def add_footer(slide, slide_num):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(6.95), Inches(11.733), Inches(0.35))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = "DeploySafe  ·  Agentic AI  ·  CSE3101"
        r1.font.name = FONT_FAMILY
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_SUBTLE

        r_spacer = p.add_run()
        r_spacer.text = " " * 85
        r2 = p.add_run()
        r2.text = f"{slide_num:02d} / 10"
        r2.font.name = FONT_FAMILY
        r2.font.size = Pt(10)
        r2.font.bold = True
        r2.font.color.rgb = TEXT_MUTED

    def add_speaker_notes(slide, notes_dict):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = ""
        p1 = tf.paragraphs[0]
        p1.text = "TALKING POINTS:"
        p1.font.bold = True
        p1.font.size = Pt(12)
        for tp in notes_dict.get("talking_points", []):
            p = tf.add_paragraph()
            p.text = f"• {tp}"
            p.font.size = Pt(11)

        p_q = tf.add_paragraph()
        p_q.text = "\nLIKELY PROFESSOR QUESTION:"
        p_q.font.bold = True
        p_q.font.size = Pt(12)

        p_qt = tf.add_paragraph()
        p_qt.text = notes_dict.get("question", "")
        p_qt.font.size = Pt(11)

        p_a = tf.add_paragraph()
        p_a.text = "\nCONCISE ANSWER:"
        p_a.font.bold = True
        p_a.font.size = Pt(12)

        p_at = tf.add_paragraph()
        p_at.text = notes_dict.get("answer", "")
        p_at.font.size = Pt(11)

    # =========================================================================
    # SLIDE 1: Title & Product Overview
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1)

    # Left Column: Clean Title & Context
    tb1 = slide1.shapes.add_textbox(Inches(0.9), Inches(1.5), Inches(5.6), Inches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = 0

    add_para(tf1, "DEPLOYSAFE", size_pt=12, bold=True, color=ACCENT_BLUE, space_after=12)
    add_para(tf1, "Deployment Readiness Analysis Before Release", size_pt=34, bold=True, color=TEXT_MAIN, space_after=16)
    add_para(tf1, "An intelligent analysis layer that identifies cross-domain deployment risks across code, configurations, dependencies, and documentation.", size_pt=15, bold=False, color=TEXT_MUTED, space_after=32)

    add_para(tf1, "Agentic AI  ·  CSE3101  ·  Midterm Presentation", size_pt=11, bold=True, color=TEXT_SUBTLE, space_after=4)
    add_para(tf1, "Team DeploySafe  ·  Evaluation Repository Demo", size_pt=11, bold=False, color=TEXT_MUTED, space_after=0)

    # Right Column: Clean Product UI Card
    card_right = add_card(slide1, 6.7, 1.2, 5.8, 5.0, bg=CARD_BG, border=CARD_BORDER)
    # Add real UI screenshot inside card
    if os.path.exists("docs/assets/screenshot_dashboard.png"):
        slide1.shapes.add_picture("docs/assets/screenshot_dashboard.png", Inches(6.85), Inches(1.35), Inches(5.5), Inches(4.4))

    # Caption under product card
    tb_cap = slide1.shapes.add_textbox(Inches(6.85), Inches(5.85), Inches(5.5), Inches(0.3))
    tf_cap = tb_cap.text_frame
    tf_cap.margin_top = tf_cap.margin_left = tf_cap.margin_right = tf_cap.margin_bottom = 0
    p_cap = tf_cap.paragraphs[0]
    p_cap.alignment = PP_ALIGN.RIGHT
    run_cap = p_cap.add_run()
    run_cap.text = "Actual DeploySafe Console  ·  Deterministic Risk Overview"
    run_cap.font.name = FONT_FAMILY
    run_cap.font.size = Pt(10)
    run_cap.font.color.rgb = TEXT_SUBTLE

    add_footer(slide1, 1)
    add_speaker_notes(slide1, {
        "talking_points": [
            "Good morning Professor. Today we present DeploySafe, an AI-powered deployment readiness platform.",
            "DeploySafe analyzes software repositories before release to detect deployment-blocking risks that traditional CI tests miss.",
            "It evaluates code changes, deployment configurations, dependencies, and documentation in unison.",
            "All findings are validated by an adversarial Critic agent and scored with a deterministic risk engine."
        ],
        "question": "Why is this problem best solved by Agentic AI rather than standard static analysis?",
        "answer": "Static analysis checks individual files for syntax and stylistic rules in isolation. DeploySafe uses specialized agents to correlate human intent in documentation with deployment manifests, catching cross-file misconfigurations."
    })

    # =========================================================================
    # SLIDE 2: The Problem
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2)
    add_header(slide2, "A Passing Pipeline Doesn't Tell the Whole Story", "Standard CI/CD checks whether code compiles and passes unit tests—not whether it is safe to deploy.")

    # Top Flow: Traditional Pipeline
    flow_bg = add_card(slide2, 0.8, 1.8, 11.733, 1.3, bg=CARD_BG, border=CARD_BORDER)
    tb_flow = slide2.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(11.333), Inches(1.0))
    tf_flow = tb_flow.text_frame
    tf_flow.word_wrap = True
    tf_flow.margin_left = tf_flow.margin_top = tf_flow.margin_right = tf_flow.margin_bottom = 0

    add_para(tf_flow, "TRADITIONAL RELEASE PIPELINE", size_pt=10, bold=True, color=TEXT_SUBTLE, space_after=6)
    add_para(tf_flow, "Code Change    →    Unit Tests (Passed)    →    Container Build    →    Production Deployment (Outage)", size_pt=14, bold=True, color=TEXT_MAIN, space_after=4)
    add_para(tf_flow, "Blind spot: Unit tests pass completely while environment configurations and service dependencies are broken.", size_pt=12, bold=False, color=CRITICAL_RED, space_after=0)

    # Bottom Gap: 3 Concrete Cards
    examples = [
        ("Configuration Mismatch", "Documentation specifies Redis for session storage, but Redis is completely missing from docker-compose.yml.", "Deployment fails on container boot."),
        ("Dependency Drift", "Unpinned package versions or missing native build dependencies in requirements.txt.", "Build succeeds locally but crashes in production."),
        ("Missing Environment Variables", "Source code expects runtime secrets or port configurations that were never declared in deployment manifests.", "Application throws unhandled 500 crashes.")
    ]

    card_w = 3.65
    gap_x = 0.39
    start_x = 0.8
    for i, (title, desc, impact) in enumerate(examples):
        cx = start_x + i * (card_w + gap_x)
        c = add_card(slide2, cx, 3.4, card_w, 3.2, bg=CARD_BG, border=CARD_BORDER)
        tb_c = slide2.shapes.add_textbox(Inches(cx + 0.25), Inches(3.6), Inches(card_w - 0.5), Inches(2.8))
        tf_c = tb_c.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = tf_c.margin_top = tf_c.margin_right = tf_c.margin_bottom = 0

        add_para(tf_c, f"0{i+1}", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=6)
        add_para(tf_c, title, size_pt=16, bold=True, color=TEXT_MAIN, space_after=10)
        add_para(tf_c, desc, size_pt=13, bold=False, color=TEXT_MUTED, space_after=14)
        add_para(tf_c, f"Impact: {impact}", size_pt=12, bold=True, color=TEXT_MAIN, space_after=0)

    add_footer(slide2, 2)
    add_speaker_notes(slide2, {
        "talking_points": [
            "Every engineering team experiences green CI builds that immediately fail when deployed to production.",
            "Traditional pipelines execute tests and builds, but they do not reason about cross-file configuration mismatches.",
            "For example, code can pass 100% of unit tests while docker-compose is missing a required database service.",
            "DeploySafe bridges this gap by analyzing the systemic deployment context across code, config, and docs."
        ],
        "question": "Why don't staging environments catch these problems?",
        "answer": "Staging catches only scenarios exercised by scripted integration tests. It misses unpinned dependencies, silent config drift, and missing documentation requirements before release."
    })

    # =========================================================================
    # SLIDE 3: The Idea
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3)
    add_header(slide3, "DeploySafe Adds an Analysis Layer", "DeploySafe does not replace CI/CD—it analyzes the change before production release.")

    # Two Column Comparison
    col_w = 5.6
    # Left: CI/CD
    c_left = add_card(slide3, 0.8, 1.8, col_w, 3.6, bg=CARD_BG, border=CARD_BORDER)
    tb_l = slide3.shapes.add_textbox(Inches(1.1), Inches(2.05), Inches(col_w - 0.6), Inches(3.1))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = tf_l.margin_top = tf_l.margin_right = tf_l.margin_bottom = 0

    add_para(tf_l, "CI / CD PIPELINES", size_pt=12, bold=True, color=TEXT_SUBTLE, space_after=8)
    add_para(tf_l, "Executes Predefined Checks", size_pt=20, bold=True, color=TEXT_MAIN, space_after=16)
    add_para(tf_l, "• Runs pre-programmed test suites and builds", size_pt=14, bold=False, color=TEXT_MUTED, space_after=8)
    add_para(tf_l, "• Checks binary exit codes (0 = Success, 1 = Failure)", size_pt=14, bold=False, color=TEXT_MUTED, space_after=8)
    add_para(tf_l, "• Operates on single files without architectural context", size_pt=14, bold=False, color=TEXT_MUTED, space_after=8)
    add_para(tf_l, "• Cannot read documentation or correlate requirements", size_pt=14, bold=False, color=TEXT_MUTED, space_after=0)

    # Right: DeploySafe
    c_right = add_card(slide3, 6.933, 1.8, col_w, 3.6, bg=CARD_BG, border=ACCENT_BLUE)
    tb_r = slide3.shapes.add_textbox(Inches(7.233), Inches(2.05), Inches(col_w - 0.6), Inches(3.1))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_top = tf_r.margin_right = tf_r.margin_bottom = 0

    add_para(tf_r, "DEPLOYSAFE INTELLIGENCE", size_pt=12, bold=True, color=ACCENT_BLUE, space_after=8)
    add_para(tf_r, "Analyzes Deployment Readiness", size_pt=20, bold=True, color=TEXT_MAIN, space_after=16)
    add_para(tf_r, "• Correlates code changes against deployment manifests", size_pt=14, bold=False, color=TEXT_MAIN, space_after=8)
    add_para(tf_r, "• Retrieves architectural intent from docs via vector RAG", size_pt=14, bold=False, color=TEXT_MAIN, space_after=8)
    add_para(tf_r, "• Critic verifies physical evidence on repository disk", size_pt=14, bold=False, color=TEXT_MAIN, space_after=8)
    add_para(tf_r, "• Computes a deterministic 0–100 risk score with fixes", size_pt=14, bold=False, color=TEXT_MAIN, space_after=0)

    # Bottom Banner: How they work together
    c_bot = add_card(slide3, 0.8, 5.7, 11.733, 1.0, bg=ACCENT_BG, border=CARD_BORDER)
    tb_bot = slide3.shapes.add_textbox(Inches(1.1), Inches(5.85), Inches(11.133), Inches(0.7))
    tf_bot = tb_bot.text_frame
    tf_bot.word_wrap = True
    tf_bot.margin_left = tf_bot.margin_top = tf_bot.margin_right = tf_bot.margin_bottom = 0

    add_para(tf_bot, "THE COMBINED WORKFLOW", size_pt=10, bold=True, color=ACCENT_BLUE, space_after=2)
    add_para(tf_bot, "Repository Change    →    [ CI / CD Pipeline   +   DeploySafe Analysis ]    →    Deterministic Risk Score + Fixes", size_pt=14, bold=True, color=TEXT_MAIN, space_after=0)

    add_footer(slide3, 3)
    add_speaker_notes(slide3, {
        "talking_points": [
            "We want to emphasize clearly: DeploySafe does not attempt to replace GitHub Actions, GitLab CI, or Jenkins.",
            "CI/CD is an execution engine. It asks 'Did the tests pass?'",
            "DeploySafe is an analytical intelligence layer. It asks 'Is this change safe to deploy?'",
            "By analyzing context and cross-file relationships, DeploySafe complements standard pipelines."
        ],
        "question": "Does DeploySafe slow down the development workflow?",
        "answer": "No. In our tested runs, full multi-agent analysis, Critic validation, and scoring complete in under 2.5 seconds on typical repository sizes."
    })

    # =========================================================================
    # SLIDE 4: How It Works (Pipeline)
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4)
    add_header(slide4, "How DeploySafe Works", "An end-to-end pipeline from repository ingestion to deterministic risk scoring.")

    steps = [
        ("01", "Repository", "Code, config, tests,\nand documentation"),
        ("02", "Context & RAG", "Discovers files and indexes\narchitectural intent"),
        ("03", "Agents", "Specialized agents analyze\ntechnical domains"),
        ("04", "Critic", "Checks findings against\nactual disk evidence"),
        ("05", "Risk Engine", "Calculates deterministic\n0–100 risk score"),
        ("06", "Result", "Actionable findings with\nline numbers and fixes")
    ]

    box_w = 1.75
    gap = 0.246
    top_y = 2.4
    height_y = 3.6

    for i, (num, title, desc) in enumerate(steps):
        bx = 0.8 + i * (box_w + gap)
        is_highlight = (num in ["04", "05"])
        b_color = ACCENT_BLUE if is_highlight else CARD_BORDER
        bg_col = ACCENT_BG if is_highlight else CARD_BG

        card = add_card(slide4, bx, top_y, box_w, height_y, bg=bg_col, border=b_color)
        tb_box = slide4.shapes.add_textbox(Inches(bx + 0.15), Inches(top_y + 0.25), Inches(box_w - 0.3), Inches(height_y - 0.5))
        tf_box = tb_box.text_frame
        tf_box.word_wrap = True
        tf_box.margin_left = tf_box.margin_top = tf_box.margin_right = tf_box.margin_bottom = 0

        add_para(tf_box, num, size_pt=14, bold=True, color=ACCENT_BLUE, space_after=12)
        add_para(tf_box, title, size_pt=16, bold=True, color=TEXT_MAIN, space_after=14)
        add_para(tf_box, desc, size_pt=12, bold=False, color=TEXT_MUTED, space_after=0)

        if i < len(steps) - 1:
            tb_arr = slide4.shapes.add_textbox(Inches(bx + box_w), Inches(top_y + 1.5), Inches(gap), Inches(0.5))
            tf_arr = tb_arr.text_frame
            tf_arr.margin_left = tf_arr.margin_top = tf_arr.margin_right = tf_arr.margin_bottom = 0
            p_arr = tf_arr.paragraphs[0]
            p_arr.alignment = PP_ALIGN.CENTER
            r_arr = p_arr.add_run()
            r_arr.text = "→"
            r_arr.font.size = Pt(13)
            r_arr.font.color.rgb = TEXT_SUBTLE

    c_note = add_card(slide4, 0.8, 6.2, 11.733, 0.65, bg=CARD_BG, border=CARD_BORDER)
    tb_n = slide4.shapes.add_textbox(Inches(1.0), Inches(6.3), Inches(11.333), Inches(0.45))
    tf_n = tb_n.text_frame
    tf_n.margin_left = tf_n.margin_top = tf_n.margin_right = tf_n.margin_bottom = 0
    add_para(tf_n, "Key Architectural Principle: LLMs propose candidate findings; the Critic and Risk Engine enforce strict evidence and deterministic scoring.", size_pt=12, bold=True, color=TEXT_MAIN, space_after=0)

    add_footer(slide4, 4)
    add_speaker_notes(slide4, {
        "talking_points": [
            "Here is the high-level data flow through the DeploySafe pipeline.",
            "First, the repository is ingested and indexed into ChromaDB for semantic retrieval.",
            "Specialized domain agents analyze code, configuration, dependencies, tests, and documentation in parallel.",
            "Candidate findings are submitted to the Critic agent for physical verification before the Risk Engine calculates the score."
        ],
        "question": "What happens if an agent suggests a finding that does not exist in the code?",
        "answer": "The Critic reads the actual target file on disk. If the cited line does not exist or the evidence is invalid, the Critic rejects the finding with a detailed reason, preventing hallucinated alerts."
    })

    # =========================================================================
    # SLIDE 5: Multi-Agent Architecture
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5)
    add_header(slide5, "Why Multiple Agents?", "Each agent focuses on one type of repository evidence, allowing focused analysis.")

    c_orch = add_card(slide5, 4.3, 1.8, 4.733, 0.85, bg=CARD_BG, border=ACCENT_BLUE)
    tb_orch = slide5.shapes.add_textbox(Inches(4.5), Inches(1.92), Inches(4.333), Inches(0.6))
    tf_orch = tb_orch.text_frame
    tf_orch.margin_left = tf_orch.margin_top = tf_orch.margin_right = tf_orch.margin_bottom = 0
    add_para(tf_orch, "Orchestrator Agent", size_pt=14, bold=True, color=ACCENT_BLUE, space_after=2, align=PP_ALIGN.CENTER)
    add_para(tf_orch, "Inspects tech stack · Plans domain tasks · Runs agents in parallel", size_pt=11, bold=False, color=TEXT_MUTED, space_after=0, align=PP_ALIGN.CENTER)

    agents = [
        ("Code Agent", "Analyzes source code changes, error handling, and runtime safety."),
        ("Config Agent", "Inspects Dockerfiles, compose specs, and environment variables."),
        ("Dependency Agent", "Audits package manifests, unpinned versions, and supply chain risks."),
        ("Test Agent", "Reviews test suite coverage, skipped tests, and deployment relevance."),
        ("Documentation RAG", "Queries architectural requirements and deployment instructions."),
        ("Security Agent", "Scans for committed secrets, permissive keys, and security flags.")
    ]

    grid_w = 3.65
    grid_gap = 0.39
    r1_y = 2.95
    r2_y = 4.25

    for i, (name, role) in enumerate(agents):
        gx = 0.8 + (i % 3) * (grid_w + grid_gap)
        gy = r1_y if i < 3 else r2_y
        c_ag = add_card(slide5, gx, gy, grid_w, 1.15, bg=CARD_BG, border=CARD_BORDER)
        tb_ag = slide5.shapes.add_textbox(Inches(gx + 0.2), Inches(gy + 0.15), Inches(grid_w - 0.4), Inches(0.85))
        tf_ag = tb_ag.text_frame
        tf_ag.word_wrap = True
        tf_ag.margin_left = tf_ag.margin_top = tf_ag.margin_right = tf_ag.margin_bottom = 0

        add_para(tf_ag, name, size_pt=13, bold=True, color=TEXT_MAIN, space_after=4)
        add_para(tf_ag, role, size_pt=11, bold=False, color=TEXT_MUTED, space_after=0)

    c_crit = add_card(slide5, 0.8, 5.65, 11.733, 1.05, bg=ACCENT_BG, border=ACCENT_BLUE)
    tb_cr = slide5.shapes.add_textbox(Inches(1.1), Inches(5.8), Inches(11.133), Inches(0.75))
    tf_cr = tb_cr.text_frame
    tf_cr.word_wrap = True
    tf_cr.margin_left = tf_cr.margin_top = tf_cr.margin_right = tf_cr.margin_bottom = 0

    add_para(tf_cr, "Critic Agent & Validation Gate", size_pt=13, bold=True, color=ACCENT_BLUE, space_after=2)
    add_para(tf_cr, "All 6 domain agents submit findings to the Critic. The Critic verifies line existence, checks false positive heuristics, and deduplicates findings before passing them to the Risk Engine.", size_pt=12, bold=False, color=TEXT_MAIN, space_after=0)

    add_footer(slide5, 5)
    add_speaker_notes(slide5, {
        "talking_points": [
            "Why use multiple agents instead of one large prompt? Because deployment readiness spans heterogeneous domains.",
            "A prompt loaded with Docker syntax, Python ASTs, and package manifests suffers from attention loss.",
            "DeploySafe divides work into 6 specialized domain agents that execute in parallel.",
            "All findings must be approved by the Critic agent, ensuring every finding is backed by physical evidence."
        ],
        "question": "How are the agents orchestrated?",
        "answer": "The Orchestrator inspects the repository's technology stack (e.g. Python, Docker, Node) and dispatches independent domain agents concurrently using a thread pool before aggregating findings."
    })

    # =========================================================================
    # SLIDE 6: RAG + Evidence
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6)
    add_header(slide6, "The AI Uses Repository Context", "RAG bridges the gap between written developer documentation and deployment code.")

    # Left: 40% Width RAG Pipeline
    c_rag = add_card(slide6, 0.8, 1.8, 4.5, 4.9, bg=CARD_BG, border=CARD_BORDER)
    tb_rag = slide6.shapes.add_textbox(Inches(1.05), Inches(2.0), Inches(4.0), Inches(4.5))
    tf_rag = tb_rag.text_frame
    tf_rag.word_wrap = True
    tf_rag.margin_left = tf_rag.margin_top = tf_rag.margin_right = tf_rag.margin_bottom = 0

    add_para(tf_rag, "SEMANTIC RETRIEVAL PIPELINE", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=12)
    rag_steps = [
        ("1. Ingestion", "Parses README, docs, guides, and configs."),
        ("2. Chunking", "Splits markdown into header-aware sections."),
        ("3. Embeddings", "Generates dense semantic vector embeddings."),
        ("4. ChromaDB", "Stores vectors locally with line metadata."),
        ("5. Agent Query", "Agents query context via similarity search.")
    ]
    for step_title, step_desc in rag_steps:
        add_para(tf_rag, step_title, size_pt=13, bold=True, color=TEXT_MAIN, space_after=2)
        add_para(tf_rag, step_desc, size_pt=11, bold=False, color=TEXT_MUTED, space_after=8)

    # Right: 60% Width Real Evidence Example (Optimized spacing to avoid touching border)
    c_ev = add_card(slide6, 5.6, 1.8, 6.933, 4.9, bg=CARD_BG, border=CARD_BORDER)
    tb_ev = slide6.shapes.add_textbox(Inches(5.85), Inches(1.98), Inches(6.433), Inches(4.5))
    tf_ev = tb_ev.text_frame
    tf_ev.word_wrap = True
    tf_ev.margin_left = tf_ev.margin_top = tf_ev.margin_right = tf_ev.margin_bottom = 0

    add_para(tf_ev, "REAL REPOSITORY EXAMPLE", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=4)
    add_para(tf_ev, "Documentation Context vs. Deployment Manifest", size_pt=17, bold=True, color=TEXT_MAIN, space_after=10)

    add_para(tf_ev, "1. Retrieved Architectural Intent (README.md, lines 18–22):", size_pt=11, bold=True, color=TEXT_MUTED, space_after=3)
    add_para(tf_ev, '"DeploySafe demo requires an active Redis cache service for distributed session storage (REDIS_URL=redis://redis:6379/0)."', size_pt=10.5, bold=False, color=TEXT_MAIN, space_after=10, font_name=CODE_FONT)

    add_para(tf_ev, "2. Inspected Deployment Manifest (docker-compose.yml, lines 1–15):", size_pt=11, bold=True, color=TEXT_MUTED, space_after=3)
    add_para(tf_ev, "services:\n  web:\n    build: .\n    ports: ['8000:8000']\n    # Redis service completely omitted from compose specification", size_pt=10.5, bold=False, color=TEXT_MAIN, space_after=10, font_name=CODE_FONT)

    add_para(tf_ev, "3. Critic-Validated Finding & Risk Impact:", size_pt=11, bold=True, color=CRITICAL_RED, space_after=3)
    add_para(tf_ev, "High Severity: Missing Redis container definition. Web service will crash on initial boot when resolving session cache endpoint.", size_pt=11.5, bold=False, color=TEXT_MAIN, space_after=0)

    add_footer(slide6, 6)
    add_speaker_notes(slide6, {
        "talking_points": [
            "This slide demonstrates the real power of RAG in DeploySafe.",
            "Traditional linters only see syntax. They don't know what external services the developer intended to run.",
            "Here, our RAG agent retrieved documentation from README.md specifying that Redis is required for sessions.",
            "The Config Agent cross-referenced docker-compose.yml, discovered Redis was missing, and flagged a High-severity crash risk."
        ],
        "question": "What happens if a repository has no documentation?",
        "answer": "DeploySafe continues operating cleanly. Agents fall back to static code inspection and configuration manifests, while the Documentation RAG agent gracefully reports no indexed guidelines."
    })

    # =========================================================================
    # SLIDE 7: Finding -> Evidence -> Risk
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7)
    add_header(slide7, "From Finding to Risk", "Findings are backed by exact source lines, and risk is calculated deterministically.")

    stages = [
        ("STAGE 1", "Candidate Finding", "LLM Proposal", "The specialized agent identifies a potential problem.", [
            ("Category", "Configuration Drift"),
            ("Title", "Missing Redis Service"),
            ("Agent", "Config Analysis Agent"),
            ("Confidence", "0.90 (High certainty)")
        ]),
        ("STAGE 2", "Physical Verification", "Critic Verification", "The Critic checks the actual repository disk.", [
            ("Target File", "docker-compose.yml"),
            ("Line Reference", "Lines 1–15 checked"),
            ("Heuristic Check", "No false-positive flags"),
            ("Validation Status", "VALIDATED (Approved)")
        ]),
        ("STAGE 3", "Risk Calculation", "Deterministic Engine", "The Risk Engine computes the score with zero AI.", [
            ("Severity Base", "HIGH: 25.0 points"),
            ("Confidence Factor", "0.90 weight applied"),
            ("Impact Factor", "1.0 (Runtime critical)"),
            ("Final Contribution", "+22.5 Risk Points")
        ])
    ]

    card_w = 3.65
    gap_x = 0.39
    start_x = 0.8
    for i, (stage_num, title, badge, desc, items) in enumerate(stages):
        cx = start_x + i * (card_w + gap_x)
        c = add_card(slide7, cx, 1.8, card_w, 4.0, bg=CARD_BG, border=CARD_BORDER)
        tb_c = slide7.shapes.add_textbox(Inches(cx + 0.25), Inches(2.0), Inches(card_w - 0.5), Inches(3.6))
        tf_c = tb_c.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = tf_c.margin_top = tf_c.margin_right = tf_c.margin_bottom = 0

        add_para(tf_c, stage_num, size_pt=10, bold=True, color=ACCENT_BLUE, space_after=4)
        add_para(tf_c, title, size_pt=18, bold=True, color=TEXT_MAIN, space_after=2)
        add_para(tf_c, badge, size_pt=11, bold=True, color=TEXT_MUTED, space_after=8)
        add_para(tf_c, desc, size_pt=11, bold=False, color=TEXT_MUTED, space_after=12)

        for label, val in items:
            add_para(tf_c, f"• {label}: {val}", size_pt=11, bold=False, color=TEXT_MAIN, space_after=4)

    c_bot = add_card(slide7, 0.8, 6.0, 11.733, 0.85, bg=ACCENT_BG, border=CARD_BORDER)
    tb_b = slide7.shapes.add_textbox(Inches(1.0), Inches(6.12), Inches(11.333), Inches(0.6))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = 0

    add_para(tf_b, "Mathematical Safety Guarantee:", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=2)
    add_para(tf_b, "LLMs propose findings. The Critic verifies physical evidence. The Risk Engine calculates the 0–100 score mathematically. An LLM never generates the risk score directly.", size_pt=12, bold=False, color=TEXT_MAIN, space_after=0)

    add_footer(slide7, 7)
    add_speaker_notes(slide7, {
        "talking_points": [
            "A critical design choice in DeploySafe is the strict separation between AI reasoning and risk scoring.",
            "The LLM is responsible for identifying potential issues based on repository evidence.",
            "The Critic verifies that the cited file and lines physically exist on disk.",
            "Finally, deterministic Python code calculates the risk score using fixed severity weights and confidence factors."
        ],
        "question": "Can the LLM hallucinate a risk score of 95?",
        "answer": "No. The LLM never outputs numbers or risk scores. Risk scores are calculated deterministically by pure Python arithmetic based on verified findings."
    })

    # =========================================================================
    # SLIDE 8: The Product
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide8)
    add_header(slide8, "The Working Product", "A clean web console for reviewing deployment risks, evidence, and history.")

    screen_w = 3.65
    screens = [
        ("docs/assets/screenshot_dashboard.png", "Risk Overview Dashboard", "100/100 risk score hero, severity cards, and Critic audit health."),
        ("docs/assets/screenshot_findings.png", "Findings Directory", "Line-accurate evidence, confidence metrics, and score contributions."),
        ("docs/assets/screenshot_analyze.png", "Real-Time Execution", "Multi-agent parallel execution timeline and runtime telemetry.")
    ]

    for i, (path, cap_title, cap_desc) in enumerate(screens):
        sx = 0.8 + i * (screen_w + gap_x)
        c_frame = add_card(slide8, sx, 1.8, screen_w, 4.9, bg=CARD_BG, border=CARD_BORDER)

        if os.path.exists(path):
            slide8.shapes.add_picture(path, Inches(sx + 0.12), Inches(1.92), Inches(screen_w - 0.24), Inches(2.75))

        tb_cap = slide8.shapes.add_textbox(Inches(sx + 0.2), Inches(4.8), Inches(screen_w - 0.4), Inches(1.7))
        tf_cap = tb_cap.text_frame
        tf_cap.word_wrap = True
        tf_cap.margin_left = tf_cap.margin_top = tf_cap.margin_right = tf_cap.margin_bottom = 0

        add_para(tf_cap, cap_title, size_pt=14, bold=True, color=TEXT_MAIN, space_after=4)
        add_para(tf_cap, cap_desc, size_pt=11, bold=False, color=TEXT_MUTED, space_after=0)

    add_footer(slide8, 8)
    add_speaker_notes(slide8, {
        "talking_points": [
            "This slide showcases the actual running DeploySafe web console built in React, TypeScript, and Tailwind CSS.",
            "Engineers can review the overall risk score hero, inspect severity breakdowns, and see real-time pipeline status.",
            "Each finding links directly to the source file, line numbers, and actionable remediation instructions.",
            "Our run telemetry tracks per-agent duration, finding counts, and Critic validation rates."
        ],
        "question": "How does the frontend communicate with the backend?",
        "answer": "The React frontend communicates with our FastAPI REST gateway via typed API endpoints, supporting real-time status polling during analysis runs."
    })

    # =========================================================================
    # SLIDE 9: What We Built
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide9)
    add_header(slide9, "What Is Working Today", "Core capabilities implemented and verified across Phases 1 through 4.")

    capabilities = [
        ("01", "Core Foundation", [
            "FastAPI REST service with typed Pydantic models",
            "React 19 + TypeScript + Tailwind CSS web console",
            "Multi-provider LLM abstraction (OpenAI, Groq, Mock)",
            "62 automated unit and integration tests passing"
        ]),
        ("02", "Repository Understanding", [
            "Recursive AST and safe repository file-tree parsing",
            "Markdown chunking with line number preservation",
            "ChromaDB persistent vector store with cosine search",
            "Semantic context retrieval for specialized agents"
        ]),
        ("03", "Multi-Agent Engine", [
            "CrewAI orchestration with parallel domain tasks",
            "6 specialized domain agents + Orchestrator",
            "Typed inspection tools (file reader, diff, grep)",
            "Critic validation agent & semantic deduplication"
        ]),
        ("04", "Risk & Reporting", [
            "Deterministic 0–100 mathematical risk scoring",
            "Findings catalog with line-accurate citations",
            "Multi-format deployment reports (HTML, MD, JSON)",
            "Verified on realistic evaluation repositories"
        ])
    ]

    card_w2 = 5.6
    card_h2 = 2.3
    row1_y = 1.8
    row2_y = 4.3

    for i, (num, title, bullets) in enumerate(capabilities):
        cx = 0.8 if (i % 2 == 0) else 6.933
        cy = row1_y if i < 2 else row2_y

        c = add_card(slide9, cx, cy, card_w2, card_h2, bg=CARD_BG, border=CARD_BORDER)
        tb_c = slide9.shapes.add_textbox(Inches(cx + 0.25), Inches(cy + 0.18), Inches(card_w2 - 0.5), Inches(card_h2 - 0.35))
        tf_c = tb_c.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = tf_c.margin_top = tf_c.margin_right = tf_c.margin_bottom = 0

        add_para(tf_c, f"{num}  ·  {title}", size_pt=14, bold=True, color=TEXT_MAIN, space_after=8)
        for b in bullets:
            add_para(tf_c, f"• {b}", size_pt=11, bold=False, color=TEXT_MUTED, space_after=3)

    add_footer(slide9, 9)
    add_speaker_notes(slide9, {
        "talking_points": [
            "Rather than showing abstract phase names, this slide details our completed capabilities by functional area.",
            "Everything on this slide is implemented, tested, and operational today.",
            "We have 62 passing automated tests covering our API, RAG store, agents, Critic, and Risk Engine.",
            "The system supports multiple LLM providers, including Groq for fast inference and a local mock for offline testing."
        ],
        "question": "What is the test coverage of the backend?",
        "answer": "Our test suite includes 62 unit and integration tests covering the ingestion pipeline, Chroma storage, agent orchestration, Critic validation, and the mathematical risk formula."
    })

    # =========================================================================
    # SLIDE 10: Live Demo + What Comes Next
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide10)
    add_header(slide10, "Next: See It Run", "Live demonstration on our evaluation repository, followed by future roadmap.")

    # Top Box: High-Level Central Pipeline
    c_flow = add_card(slide10, 0.8, 1.8, 11.733, 1.0, bg=ACCENT_BG, border=CARD_BORDER)
    tb_fl = slide10.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(11.333), Inches(0.7))
    tf_fl = tb_fl.text_frame
    tf_fl.word_wrap = True
    tf_fl.margin_left = tf_fl.margin_top = tf_fl.margin_right = tf_fl.margin_bottom = 0
    add_para(tf_fl, "LIVE DEMO ARCHITECTURAL FLOW", size_pt=10, bold=True, color=ACCENT_BLUE, space_after=3)
    add_para(tf_fl, "Repository    →    Run Analysis    →    Parallel Agents    →    Critic Evidence    →    Risk Score    →    Fix Recommendations", size_pt=13, bold=True, color=TEXT_MAIN, space_after=0)

    # Middle Box: 6 Demo Steps
    c_demo = add_card(slide10, 0.8, 3.0, 11.733, 2.75, bg=CARD_BG, border=CARD_BORDER)
    tb_demo = slide10.shapes.add_textbox(Inches(1.1), Inches(3.18), Inches(11.133), Inches(2.4))
    tf_demo = tb_demo.text_frame
    tf_demo.word_wrap = True
    tf_demo.margin_left = tf_demo.margin_top = tf_demo.margin_right = tf_demo.margin_bottom = 0

    add_para(tf_demo, "DEMONSTRATION SEQUENCE", size_pt=11, bold=True, color=TEXT_SUBTLE, space_after=8)
    demo_steps = [
        "1. Select Evaluation Repository — Target local demo-repos/deploysafe-analysis-demo",
        "2. Trigger Multi-Agent Pipeline — Watch real-time execution status across all 6 domain agents",
        "3. Review Chroma Vector RAG Context — Observe semantic retrieval from project documentation",
        "4. Inspect Critic-Validated Findings — Review verified findings with line-accurate file citations",
        "5. Examine Deterministic Risk Score — Understand the 100 / 100 CRITICAL score calculation",
        "6. Export Multi-Format Deployment Report — Inspect generated HTML, Markdown, and JSON reports"
    ]
    for ds in demo_steps:
        add_para(tf_demo, ds, size_pt=12, bold=False, color=TEXT_MAIN, space_after=4)

    # Bottom Callout: Next Development
    c_next = add_card(slide10, 0.8, 5.95, 11.733, 0.75, bg=CARD_BG, border=CARD_BORDER)
    tb_nxt = slide10.shapes.add_textbox(Inches(1.1), Inches(6.08), Inches(11.133), Inches(0.55))
    tf_nxt = tb_nxt.text_frame
    tf_nxt.word_wrap = True
    tf_nxt.margin_left = tf_nxt.margin_top = tf_nxt.margin_right = tf_nxt.margin_bottom = 0

    add_para(tf_nxt, "Next development (Phases 5 & 6): GitHub Actions CI workflow integration, automated PR commenting bot, and benchmark evaluations.", size_pt=11.5, bold=False, color=TEXT_MUTED, space_after=0)

    add_footer(slide10, 10)
    add_speaker_notes(slide10, {
        "talking_points": [
            "We will now transition to the live demonstration of DeploySafe running on our evaluation repository.",
            "We will trigger an analysis run, watch the agents execute, inspect findings, and review the risk score.",
            "Following the demo, we are excited to expand DeploySafe into GitHub Actions and PR commenting bots in Phase 5.",
            "Thank you Professor, and we are ready for your questions."
        ],
        "question": "How will GitHub Actions integration work in Phase 5?",
        "answer": "DeploySafe will run as a containerized action triggered on pull_request events, analyzing the git diff against the target branch and posting a risk summary comment."
    })

    # Save Presentation
    output_path = "DeploySafe_Midterm_Presentation_v2.pptx"
    prs.save(output_path)
    print(f"Successfully generated {output_path} with {len(prs.slides)} slides.")

if __name__ == "__main__":
    create_presentation()
