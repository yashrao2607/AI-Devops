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
TOTAL_SLIDES = 10

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

    def add_header(slide, title, subtitle=None):
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
            run2.font.size = Pt(13.5)
            run2.font.bold = False
            run2.font.color.rgb = TEXT_MUTED

    def add_footer(slide, slide_num):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(6.95), Inches(11.733), Inches(0.35))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = "DeploySafe  |  CSE 4011: Intelligent Developer Tools & AI DevOps Workflows"
        r1.font.name = FONT_FAMILY
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_SUBTLE

        r_spacer = p.add_run()
        r_spacer.text = " " * 50
        r2 = p.add_run()
        r2.text = f"{slide_num:02d} / {TOTAL_SLIDES:02d}"
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
            p.text = f"- {tp}"
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
    # SLIDE 1: Title & Course Context (Grounded, direct)
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1)

    # Left Column: Title & Metadata
    tb1 = slide1.shapes.add_textbox(Inches(0.8), Inches(1.2), Inches(5.8), Inches(5.2))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = 0

    add_para(tf1, "DEPLOYSAFE  |  PROJECT PHASE EVALUATION 2 (A2)", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=10)
    add_para(tf1, "Automated Pre-Deployment Risk Analysis for DevOps Pipelines", size_pt=28, bold=True, color=TEXT_MAIN, space_after=14)
    add_para(tf1, "An intelligent analysis tool that inspects repositories before release, detecting configuration drift, unpinned dependencies, and missing environment secrets.", size_pt=13.5, bold=False, color=TEXT_MUTED, space_after=24)

    # Course Metadata Box
    c_meta = add_card(slide1, 0.8, 4.35, 5.65, 2.35, bg=CARD_BG, border=CARD_BORDER)
    tb_m = slide1.shapes.add_textbox(Inches(1.0), Inches(4.5), Inches(5.25), Inches(2.05))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    tf_m.margin_left = tf_m.margin_top = tf_m.margin_right = tf_m.margin_bottom = 0

    add_para(tf_m, "Course: CSE 4011 — Intelligent Developer Tools and AI DevOps Workflows", size_pt=11, bold=True, color=TEXT_MAIN, space_after=4)
    add_para(tf_m, "Faculty Mentors: Dr. Kiran Khatter & Mr. Naveen Singh", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=4)
    add_para(tf_m, "Evaluation: Mid-Term Examination (A2 · 30% Weightage · 5–9 Oct 2026)", size_pt=10.5, bold=False, color=TEXT_MUTED, space_after=4)
    add_para(tf_m, "Student: Yash Rao  |  Batch 2023–27 (7th Semester)", size_pt=10.5, bold=False, color=TEXT_MAIN, space_after=0)

    # Right Column: UI Card
    card_right = add_card(slide1, 6.75, 1.2, 5.78, 5.5, bg=CARD_BG, border=CARD_BORDER)
    if os.path.exists("docs/assets/screenshot_dashboard.png"):
        slide1.shapes.add_picture("docs/assets/screenshot_dashboard.png", Inches(6.9), Inches(1.35), Inches(5.48), Inches(4.7))

    tb_cap = slide1.shapes.add_textbox(Inches(6.9), Inches(6.2), Inches(5.48), Inches(0.35))
    tf_cap = tb_cap.text_frame
    tf_cap.margin_top = tf_cap.margin_left = tf_cap.margin_right = tf_cap.margin_bottom = 0
    p_cap = tf_cap.paragraphs[0]
    p_cap.alignment = PP_ALIGN.RIGHT
    run_cap = p_cap.add_run()
    run_cap.text = "DeploySafe Web Console  |  Deterministic Risk Overview Hero"
    run_cap.font.name = FONT_FAMILY
    run_cap.font.size = Pt(10)
    run_cap.font.color.rgb = TEXT_SUBTLE

    add_footer(slide1, 1)
    add_speaker_notes(slide1, {
        "talking_points": [
            "Good morning Dr. Kiran Khatter and Mr. Naveen Singh. Today I am presenting DeploySafe for our CSE 4011 Mid-Term Evaluation (A2).",
            "DeploySafe is an automated pre-deployment risk analysis tool that inspects repositories before release to catch critical deployment failures.",
            "It bridges modern software engineering, AI code intelligence, and DevOps workflows as outlined in our course syllabus.",
            "All findings are validated against actual disk files by a Critic agent, and scored through a deterministic mathematical formula."
        ],
        "question": "Why is this problem best solved by an AI DevOps tool rather than standard static analysis?",
        "answer": "Static analysis checks individual files for syntax rules in isolation. DeploySafe uses specialized domain agents to correlate human intent in documentation with deployment manifests, catching cross-domain misconfigurations like a missing database container."
    })

    # =========================================================================
    # SLIDE 2: The Problem: Why Green Builds Still Fail in Production
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2)
    add_header(slide2, "Why Green Builds Still Fail in Production", "Unit tests pass in isolated environments, but fail when deployed to real production infrastructure.")

    col_w2 = 5.67
    card_h2 = 3.95

    # Left: The Problem
    c_prob = add_card(slide2, 0.8, 1.8, col_w2, card_h2, bg=CARD_BG, border=CARD_BORDER)
    tb_p = slide2.shapes.add_textbox(Inches(1.02), Inches(1.98), Inches(col_w2 - 0.44), Inches(card_h2 - 0.36))
    tf_p = tb_p.text_frame
    tf_p.word_wrap = True
    tf_p.margin_left = tf_p.margin_top = tf_p.margin_right = tf_p.margin_bottom = 0

    add_para(tf_p, "COMMON DEPLOYMENT BLIND SPOTS", size_pt=11, bold=True, color=CRITICAL_RED, space_after=6)
    add_para(tf_p, "What CI/CD Pipelines Miss Before Release", size_pt=17, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf_p, "Traditional CI runs unit tests in isolation. It does not verify deployment environment parity:", size_pt=12, bold=False, color=TEXT_MUTED, space_after=10)

    prob_items = [
        ("Missing Services in Compose", "Source code connects to redis://redis:6379, but Redis is completely missing from docker-compose.yml. Tests pass; container crashes on boot."),
        ("Unpinned Dependency Drift", "requirements.txt or package.json uses unpinned versions. Tests pass on cached CI runners, but newer breaking releases fail in production."),
        ("Undeclared Environment Variables", "Code calls os.environ['DATABASE_URL'] without fallback. Variable is omitted from .env.example, causing runtime KeyError crashes.")
    ]
    for p_title, p_desc in prob_items:
        add_para(tf_p, f"- {p_title}:", size_pt=11, bold=True, color=TEXT_MAIN, space_after=1)
        add_para(tf_p, f"  {p_desc}", size_pt=10, bold=False, color=TEXT_MUTED, space_after=5)

    # Right: The Solution
    c_sol = add_card(slide2, 6.863, 1.8, col_w2, card_h2, bg=CARD_BG, border=ACCENT_BLUE)
    tb_s = slide2.shapes.add_textbox(Inches(7.083), Inches(1.98), Inches(col_w2 - 0.44), Inches(card_h2 - 0.36))
    tf_s = tb_s.text_frame
    tf_s.word_wrap = True
    tf_s.margin_left = tf_s.margin_top = tf_s.margin_right = tf_s.margin_bottom = 0

    add_para(tf_s, "HOW DEPLOYSAFE ADDRESSES THIS", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=6)
    add_para(tf_s, "Pre-Flight Intelligence Layer Before Deployment", size_pt=17, bold=True, color=TEXT_MAIN, space_after=10)
    add_para(tf_s, "DeploySafe analyzes the entire repository context before code reaches the production cluster:", size_pt=12, bold=False, color=TEXT_MUTED, space_after=10)

    sol_items = [
        ("Cross-File Correlation", "Inspects whether external services used in source code are declared in Dockerfiles and docker-compose.yml."),
        ("Documentation Comparison", "Uses ChromaDB to query README.md instructions and check if required ports and secrets are configured."),
        ("Static AST Parsing", "Uses Python's ast module to inspect unhandled exceptions, database retry logic, and network call safety.")
    ]
    for s_title, s_desc in sol_items:
        add_para(tf_s, f"- {s_title}:", size_pt=11, bold=True, color=TEXT_MAIN, space_after=1)
        add_para(tf_s, f"  {s_desc}", size_pt=10, bold=False, color=TEXT_MUTED, space_after=5)

    # Bottom Banner
    c_bot2 = add_card(slide2, 0.8, 5.95, 11.733, 0.85, bg=ACCENT_BG, border=CARD_BORDER)
    tb_b2 = slide2.shapes.add_textbox(Inches(1.0), Inches(6.08), Inches(11.333), Inches(0.6))
    tf_b2 = tb_b2.text_frame
    tf_b2.word_wrap = True
    tf_b2.margin_left = tf_b2.margin_top = tf_b2.margin_right = tf_b2.margin_bottom = 0

    add_para(tf_b2, "RELEASE WORKFLOW PLACEMENT", size_pt=10, bold=True, color=ACCENT_BLUE, space_after=2)
    add_para(tf_b2, "Code Commit  ->  Run Unit Tests (CI)  ->  Run DeploySafe (Pre-Flight Analysis)  ->  Deterministic Go/No-Go Release Gate", size_pt=12.5, bold=True, color=TEXT_MAIN, space_after=0)

    add_footer(slide2, 2)
    add_speaker_notes(slide2, {
        "talking_points": [
            "This slide highlights the common blind spots in traditional CI/CD pipelines.",
            "Unit tests check code logic in isolation, but they miss missing container services, unpinned dependencies, and undeclared secrets.",
            "DeploySafe analyzes cross-file relationships and documentation context to catch these issues before release.",
            "It sits right after unit tests pass, acting as an automated pre-flight gatekeeper."
        ],
        "question": "Why don't staging environments catch these problems?",
        "answer": "Staging catches only scenarios covered by existing integration tests against running infrastructure. It misses unpinned container tags that change overnight and missing documentation requirements before release. DeploySafe catches these statically in under 5 seconds."
    })

    # =========================================================================
    # SLIDE 3: Course Alignment & Midterm Evaluation Rubrics (A2 · 30%)
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3)
    add_header(slide3, "Course Alignment & Evaluation Rubrics (A2 · 30%)", "Direct mapping of project deliverables to CSE 4011 Mid-Term evaluation components.")

    rubric_cards = [
        ("01", "RAG & Code Retrieval (10%)", "CO2, CO3  |  ChromaDB & AST", [
            "ChromaDB persistent vector store with cosine similarity search",
            "Markdown chunking that preserves section headers and line numbers",
            "Retrieves deployment prerequisites from README and documentation",
            "Cross-references documented services against compose manifests"
        ]),
        ("02", "CI/CD & Release Automation (10%)", "CO2, CO3  |  Pre-Flight Gates", [
            "Automated pre-deployment verification gate with non-zero exit codes",
            "Blocks deployment release when Critical severity findings are detected",
            "Generates structured audit reports in JSON, Markdown, and HTML",
            "Outputs copyable CLI commands for immediate developer remediation"
        ]),
        ("03", "Test Suite & AST Inspection (5%)", "CO2  |  Python AST & Pytest", [
            "62 automated unit and integration tests covering all pipeline stages",
            "Static AST parsing for Python files and package manifests for Node.js",
            "Audit checks for missing error handling and unhandled exceptions",
            "Deterministic mock tests allowing zero-cost CI execution"
        ]),
        ("04", "Working Prototype & Docs (5%)", "CO3  |  FastAPI & React 19", [
            "Functional backend using FastAPI with typed Pydantic models",
            "Interactive web console built with React 19, TypeScript, and Tailwind",
            "Multi-container deployment using Docker Compose and Nginx proxy",
            "Complete OpenAPI / Swagger documentation at /docs"
        ])
    ]

    card_w4 = 5.67
    card_h4 = 2.05
    row1_y4 = 1.8
    row2_y4 = 4.0

    for i, (num, title, badge, bullets) in enumerate(rubric_cards):
        cx = 0.8 if (i % 2 == 0) else 6.863
        cy = row1_y4 if i < 2 else row2_y4

        c = add_card(slide3, cx, cy, card_w4, card_h4, bg=CARD_BG, border=CARD_BORDER)
        tb_c = slide3.shapes.add_textbox(Inches(cx + 0.22), Inches(cy + 0.14), Inches(card_w4 - 0.44), Inches(card_h4 - 0.28))
        tf_c = tb_c.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = tf_c.margin_top = tf_c.margin_right = tf_c.margin_bottom = 0

        add_para(tf_c, f"{num}  ·  {title}", size_pt=13, bold=True, color=TEXT_MAIN, space_after=2)
        add_para(tf_c, badge, size_pt=9.5, bold=True, color=ACCENT_BLUE, space_after=6)
        for b in bullets:
            add_para(tf_c, f"- {b}", size_pt=9.5, bold=False, color=TEXT_MUTED, space_after=2)

    c_bot3 = add_card(slide3, 0.8, 6.15, 11.733, 0.7, bg=ACCENT_BG, border=CARD_BORDER)
    tb_b3 = slide3.shapes.add_textbox(Inches(1.0), Inches(6.22), Inches(11.333), Inches(0.55))
    tf_b3 = tb_b3.text_frame
    tf_b3.word_wrap = True
    tf_b3.margin_left = tf_b3.margin_top = tf_b3.margin_right = tf_b3.margin_bottom = 0

    add_para(tf_b3, "Evaluation Criteria Mapping:", size_pt=10.5, bold=True, color=ACCENT_BLUE, space_after=1)
    add_para(tf_b3, "C6 (Progress vs Plan)  |  C7 (Technical Understanding)  |  C8 (Problem Solving)  |  C9 (Documentation)  |  C10 (Individual Contribution)", size_pt=11, bold=True, color=TEXT_MAIN, space_after=0)

    add_footer(slide3, 3)
    add_speaker_notes(slide3, {
        "talking_points": [
            "This slide maps our project deliverables to the 4 components of the A2 Mid-Term Rubric in the CSE 4011 Course Handout.",
            "Component 1 (10%): RAG-based code and docs retrieval using ChromaDB and AST parsing.",
            "Component 2 (10%): Pre-deployment verification gate with non-zero exit codes to block broken releases.",
            "Component 3 (5%): Test suite quality with 62 unit and integration tests running in CI.",
            "Component 4 (5%): Working prototype with FastAPI, React 19, Docker Compose, and OpenAPI docs."
        ],
        "question": "How does DeploySafe satisfy Course Outcomes CO1, CO2, and CO3?",
        "answer": "DeploySafe fulfills CO1 through prompt engineering and model selection; CO2 through semantic code search with ChromaDB and automated test analysis; and CO3 through an end-to-end AI-augmented release gate."
    })

    # =========================================================================
    # SLIDE 4: System Architecture & Agent Responsibilities
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4)
    add_header(slide4, "System Architecture & Agent Responsibilities", "A multi-agent pipeline that divides repository inspection across dedicated domains.")

    # Top Pipeline (5 horizontal steps)
    pipe_steps = [
        ("01", "Ingestion & AST", "Parse file trees, ASTs, and dependencies"),
        ("02", "ChromaDB RAG", "Embed & index doc intent into vector DB"),
        ("03", "Specialist Agents", "Agents inspect code, config, and dependencies"),
        ("04", "Critic Validation", "Physical line verification on repository disk"),
        ("05", "Risk Formula", "Deterministic 0–100 math & release gate")
    ]
    p_w = 2.15
    p_gap = 0.245
    p_top = 1.8
    p_h = 1.45

    for i, (num, title, desc) in enumerate(pipe_steps):
        bx = 0.8 + i * (p_w + p_gap)
        is_hi = (num in ["04", "05"])
        b_c = ACCENT_BLUE if is_hi else CARD_BORDER
        bg_c = ACCENT_BG if is_hi else CARD_BG

        add_card(slide4, bx, p_top, p_w, p_h, bg=bg_c, border=b_c)
        tb_box = slide4.shapes.add_textbox(Inches(bx + 0.12), Inches(p_top + 0.12), Inches(p_w - 0.24), Inches(p_h - 0.24))
        tf_box = tb_box.text_frame
        tf_box.word_wrap = True
        tf_box.margin_left = tf_box.margin_top = tf_box.margin_right = tf_box.margin_bottom = 0

        add_para(tf_box, f"{num}  ·  {title}", size_pt=11.5, bold=True, color=ACCENT_BLUE if is_hi else TEXT_MAIN, space_after=3)
        add_para(tf_box, desc, size_pt=9.5, bold=False, color=TEXT_MUTED, space_after=0)

        if i < len(pipe_steps) - 1:
            tb_arr = slide4.shapes.add_textbox(Inches(bx + p_w), Inches(p_top + 0.5), Inches(p_gap), Inches(0.4))
            tf_arr = tb_arr.text_frame
            tf_arr.margin_left = tf_arr.margin_top = tf_arr.margin_right = tf_arr.margin_bottom = 0
            p_arr = tf_arr.paragraphs[0]
            p_arr.alignment = PP_ALIGN.CENTER
            r_arr = p_arr.add_run()
            r_arr.text = "->"
            r_arr.font.size = Pt(12)
            r_arr.font.color.rgb = TEXT_SUBTLE

    # Bottom Grid: 4 Core Specialist Agents + Critic
    agents_list = [
        ("Code Agent", "Uses Python's ast module to detect unhandled exceptions, bare except blocks, and missing timeouts."),
        ("Config Agent", "Inspects Dockerfiles (base image, non-root user) and docker-compose.yml for missing services."),
        ("Dependency Agent", "Scans requirements.txt and package.json for unpinned versions and missing native build flags."),
        ("Documentation RAG", "Queries ChromaDB vector database for documented environment variables, databases, and ports."),
        ("Critic Agent", "Verifies that reported files and line numbers physically exist on disk before any score is calculated."),
        ("Orchestrator", "Inspects repository technology stack and dispatches domain agents concurrently in a thread pool.")
    ]

    grid_w = 3.65
    grid_gap = 0.39
    r1_y = 3.45
    r2_y = 4.65

    for i, (name, role) in enumerate(agents_list):
        gx = 0.8 + (i % 3) * (grid_w + grid_gap)
        gy = r1_y if i < 3 else r2_y
        add_card(slide4, gx, gy, grid_w, 1.05, bg=CARD_BG, border=CARD_BORDER)
        tb_ag = slide4.shapes.add_textbox(Inches(gx + 0.18), Inches(gy + 0.12), Inches(grid_w - 0.36), Inches(0.81))
        tf_ag = tb_ag.text_frame
        tf_ag.word_wrap = True
        tf_ag.margin_left = tf_ag.margin_top = tf_ag.margin_right = tf_ag.margin_bottom = 0

        add_para(tf_ag, name, size_pt=12, bold=True, color=TEXT_MAIN, space_after=2)
        add_para(tf_ag, role, size_pt=9.5, bold=False, color=TEXT_MUTED, space_after=0)

    # Bottom Banner
    c_crit = add_card(slide4, 0.8, 5.85, 11.733, 0.95, bg=ACCENT_BG, border=ACCENT_BLUE)
    tb_cr = slide4.shapes.add_textbox(Inches(1.0), Inches(5.95), Inches(11.333), Inches(0.75))
    tf_cr = tb_cr.text_frame
    tf_cr.word_wrap = True
    tf_cr.margin_left = tf_cr.margin_top = tf_cr.margin_right = tf_cr.margin_bottom = 0

    add_para(tf_cr, "Why Multiple Agents Over a Single Prompt?", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=2)
    add_para(tf_cr, "A single prompt loaded with Docker syntax, AST trees, and package manifests suffers from attention loss. Dividing analysis across specialist agents keeps prompts focused, runs concurrently in ~1.8 seconds, and isolates findings for validation.", size_pt=10.5, bold=False, color=TEXT_MAIN, space_after=0)

    add_footer(slide4, 4)
    add_speaker_notes(slide4, {
        "talking_points": [
            "This slide explains our multi-agent architecture and division of labor.",
            "Instead of sending an entire repository to one giant LLM prompt, we divide work across specialist agents.",
            "The Code Agent checks Python ASTs, Config Agent checks Docker manifests, and Dependency Agent checks version pins.",
            "The Critic agent performs physical disk verification to ensure every reported line actually exists."
        ],
        "question": "How are the agents orchestrated?",
        "answer": "The Orchestrator inspects the repository's technology stack (e.g., Python, Docker, Node) and dispatches independent domain agents concurrently using a thread pool before aggregating findings into a Pydantic blackboard."
    })

    # =========================================================================
    # SLIDE 5: Semantic RAG: Correlating Docs with Configs
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5)
    add_header(slide5, "RAG in Practice: Detecting Configuration Drift", "ChromaDB semantic retrieval correlates written documentation with deployment manifests.")

    # Left: RAG Pipeline
    c_rag = add_card(slide5, 0.8, 1.8, 4.5, 4.9, bg=CARD_BG, border=CARD_BORDER)
    tb_rag = slide5.shapes.add_textbox(Inches(1.05), Inches(2.0), Inches(4.0), Inches(4.5))
    tf_rag = tb_rag.text_frame
    tf_rag.word_wrap = True
    tf_rag.margin_left = tf_rag.margin_top = tf_rag.margin_right = tf_rag.margin_bottom = 0

    add_para(tf_rag, "RAG PIPELINE IMPLEMENTATION", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=12)
    rag_steps = [
        ("1. Documentation Parsing", "Parses README.md, setup guides, and env examples."),
        ("2. Header-Aware Chunking", "Splits markdown into sections while preserving line numbers."),
        ("3. Dense Vector Embeddings", "Generates semantic vector embeddings for each chunk."),
        ("4. ChromaDB Storage", "Stores vectors locally with file path and line metadata."),
        ("5. Agent Querying", "Agents query context using cosine similarity search.")
    ]
    for step_title, step_desc in rag_steps:
        add_para(tf_rag, step_title, size_pt=12.5, bold=True, color=TEXT_MAIN, space_after=2)
        add_para(tf_rag, step_desc, size_pt=10.5, bold=False, color=TEXT_MUTED, space_after=8)

    # Right: Real Repository Case Study
    c_ev = add_card(slide5, 5.6, 1.8, 6.933, 4.9, bg=CARD_BG, border=CARD_BORDER)
    tb_ev = slide5.shapes.add_textbox(Inches(5.85), Inches(1.98), Inches(6.433), Inches(4.5))
    tf_ev = tb_ev.text_frame
    tf_ev.word_wrap = True
    tf_ev.margin_left = tf_ev.margin_top = tf_ev.margin_right = tf_ev.margin_bottom = 0

    add_para(tf_ev, "REAL CASE STUDY: DEMO MICROSERVICE", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=4)
    add_para(tf_ev, "Catching a Missing Service Before Production Boot", size_pt=17, bold=True, color=TEXT_MAIN, space_after=10)

    add_para(tf_ev, "1. Retrieved from README.md (lines 18-22 via ChromaDB):", size_pt=11, bold=True, color=TEXT_MUTED, space_after=3)
    add_para(tf_ev, '"Requires Redis for session caching: REDIS_URL=redis://redis:6379/0"', size_pt=10.5, bold=False, color=TEXT_MAIN, space_after=10, font_name=CODE_FONT)

    add_para(tf_ev, "2. Inspected Deployment Manifest (docker-compose.yml, lines 1-12):", size_pt=11, bold=True, color=TEXT_MUTED, space_after=3)
    add_para(tf_ev, "services:\n  web:\n    build: .\n    ports: ['8000:8000']\n    # Redis service completely omitted", size_pt=10.5, bold=False, color=TEXT_MAIN, space_after=10, font_name=CODE_FONT)

    add_para(tf_ev, "3. Critic Verification & Risk Output:", size_pt=11, bold=True, color=CRITICAL_RED, space_after=3)
    add_para(tf_ev, "Validated docker-compose.yml on disk. Emitted High Severity finding: Web service will fail health checks on container startup due to unreachable Redis endpoint.", size_pt=11, bold=False, color=TEXT_MAIN, space_after=0)

    add_footer(slide5, 5)
    add_speaker_notes(slide5, {
        "talking_points": [
            "This slide demonstrates how our RAG pipeline catches configuration drift, fulfilling the 10% RAG requirement.",
            "Traditional linters check syntax inside docker-compose.yml, but they have no idea what services the code actually expects.",
            "Our RAG agent queries ChromaDB for documentation requirements, discovers Redis is required, and checks docker-compose.yml.",
            "The Critic verifies the file on disk and confirms the service is missing, flagging a High-severity deployment blocker."
        ],
        "question": "What happens if a repository has no documentation?",
        "answer": "DeploySafe handles missing documentation gracefully. If no markdown files exist, the RAG agent returns an empty context set, and the other agents continue static code, manifest, and dependency analysis without interruption."
    })

    # =========================================================================
    # SLIDE 6: Deterministic Risk Scoring vs. LLM Hallucinations
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6)
    add_header(slide6, "Deterministic Risk Scoring vs. LLM Hallucinations", "LLMs propose findings; a deterministic Python formula calculates the 0–100 score.")

    stages = [
        ("STAGE 1", "Candidate Finding", "LLM Proposal", "Specialist agent identifies a potential problem.", [
            ("Category", "Configuration Drift"),
            ("Finding", "Missing Redis Service"),
            ("Agent", "Config Agent"),
            ("Confidence", "0.90 (High certainty)")
        ]),
        ("STAGE 2", "Physical Verification", "Critic Verification", "Critic validates the file on actual disk.", [
            ("Target File", "docker-compose.yml"),
            ("Line Reference", "Lines 1–12 checked"),
            ("Disk Check", "File exists, lines matched"),
            ("Status", "VALIDATED (Approved)")
        ]),
        ("STAGE 3", "Risk Calculation", "Deterministic Formula", "Python arithmetic calculates score with zero AI.", [
            ("Severity Base", "HIGH: 25.0 points"),
            ("Confidence", "0.90 weight applied"),
            ("Impact Factor", "1.0 (Runtime critical)"),
            ("Contribution", "+22.5 Risk Points")
        ])
    ]

    card_w = 3.65
    gap_x = 0.39
    start_x = 0.8
    for i, (stage_num, title, badge, desc, items) in enumerate(stages):
        cx = start_x + i * (card_w + gap_x)
        c = add_card(slide6, cx, 1.8, card_w, 4.0, bg=CARD_BG, border=CARD_BORDER)
        tb_c = slide6.shapes.add_textbox(Inches(cx + 0.25), Inches(2.0), Inches(card_w - 0.5), Inches(3.6))
        tf_c = tb_c.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = tf_c.margin_top = tf_c.margin_right = tf_c.margin_bottom = 0

        add_para(tf_c, stage_num, size_pt=10, bold=True, color=ACCENT_BLUE, space_after=4)
        add_para(tf_c, title, size_pt=18, bold=True, color=TEXT_MAIN, space_after=2)
        add_para(tf_c, badge, size_pt=11, bold=True, color=TEXT_MUTED, space_after=8)
        add_para(tf_c, desc, size_pt=10.5, bold=False, color=TEXT_MUTED, space_after=12)

        for label, val in items:
            add_para(tf_c, f"- {label}: {val}", size_pt=10.5, bold=False, color=TEXT_MAIN, space_after=4)

    c_bot = add_card(slide6, 0.8, 6.0, 11.733, 0.85, bg=ACCENT_BG, border=CARD_BORDER)
    tb_b = slide6.shapes.add_textbox(Inches(1.0), Inches(6.12), Inches(11.333), Inches(0.6))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = 0

    add_para(tf_b, "Mathematical Risk Formula & Gate Threshold:", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=2)
    add_para(tf_b, "Score = min(100, Sum(BaseWeight * Confidence)). Weights: Critical = 40, High = 25, Medium = 12, Low = 5. Threshold: Score >= 70 -> NO-GO (Exit Code 1); Score < 70 -> GO. An LLM never generates numbers directly.", size_pt=11, bold=False, color=TEXT_MAIN, space_after=0)

    add_footer(slide6, 6)
    add_speaker_notes(slide6, {
        "talking_points": [
            "A core design decision in DeploySafe is strictly separating LLM reasoning from mathematical scoring.",
            "If an LLM directly outputs a risk score like '85', that number is subjective and cannot be audited.",
            "In DeploySafe, the LLM only outputs categorical findings.",
            "The Critic verifies the evidence on disk, and pure Python arithmetic calculates the final 0–100 score."
        ],
        "question": "Can the LLM hallucinate a high risk score?",
        "answer": "No. The LLM never outputs numbers or scores. Risk scores are computed deterministically by pure Python math based on verified findings that pass Critic validation."
    })

    # =========================================================================
    # SLIDE 7: Working Product: Web Dashboard
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7)
    add_header(slide7, "The Working Product: Web Dashboard", "React 19 interface displaying risk scores, line citations, and execution telemetry.")

    screen_w = 3.65
    screens = [
        ("docs/assets/screenshot_dashboard.png", "Risk Overview Dashboard", "Displays the 0–100 risk score hero, severity count cards, and Critic validation status."),
        ("docs/assets/screenshot_findings.png", "Findings Directory", "Shows findings with exact file paths, line references, and copyable CLI remediation commands."),
        ("docs/assets/screenshot_analyze.png", "Execution Telemetry", "Displays per-agent execution times (~1.8s per agent), pipeline logs, and real-time status polling.")
    ]

    for i, (path, cap_title, cap_desc) in enumerate(screens):
        sx = 0.8 + i * (screen_w + gap_x)
        c_frame = add_card(slide7, sx, 1.8, screen_w, 4.9, bg=CARD_BG, border=CARD_BORDER)

        if os.path.exists(path):
            slide7.shapes.add_picture(path, Inches(sx + 0.12), Inches(1.92), Inches(screen_w - 0.24), Inches(2.75))

        tb_cap = slide7.shapes.add_textbox(Inches(sx + 0.2), Inches(4.8), Inches(screen_w - 0.4), Inches(1.7))
        tf_cap = tb_cap.text_frame
        tf_cap.word_wrap = True
        tf_cap.margin_left = tf_cap.margin_top = tf_cap.margin_right = tf_cap.margin_bottom = 0

        add_para(tf_cap, cap_title, size_pt=14, bold=True, color=TEXT_MAIN, space_after=4)
        add_para(tf_cap, cap_desc, size_pt=10.5, bold=False, color=TEXT_MUTED, space_after=0)

    add_footer(slide7, 7)
    add_speaker_notes(slide7, {
        "talking_points": [
            "This slide showcases the running DeploySafe web console built in React 19, TypeScript, and Tailwind CSS.",
            "The dashboard displays the overall risk score hero, severity cards, and Critic audit health.",
            "Each finding links directly to the source file, line numbers, and actionable remediation instructions.",
            "The execution view displays real-time telemetry and per-agent execution duration."
        ],
        "question": "How does the frontend communicate with the backend?",
        "answer": "The React frontend communicates with our FastAPI REST gateway via typed API endpoints, supporting real-time status polling during analysis runs."
    })

    # =========================================================================
    # SLIDE 8: Implementation Status & Test Verification (Realistic, no fluff)
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide8)
    add_header(slide8, "Implementation Status & Test Verification", "Completed components, work in progress, and automated test suite coverage.")

    # Left: Status Breakdown (Grounded & honest)
    c_p8 = add_card(slide8, 0.8, 1.8, 5.67, 4.0, bg=CARD_BG, border=CARD_BORDER)
    tb_p8 = slide8.shapes.add_textbox(Inches(1.02), Inches(1.95), Inches(5.23), Inches(3.7))
    tf_p8 = tb_p8.text_frame
    tf_p8.word_wrap = True
    tf_p8.margin_left = tf_p8.margin_top = tf_p8.margin_right = tf_p8.margin_bottom = 0

    add_para(tf_p8, "IMPLEMENTATION PROGRESS (MIDTERM)", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=8)

    status_sections = [
        ("Implemented & Operational", [
            "Repository ingestion and Python AST code parser",
            "ChromaDB persistent vector store and markdown chunker",
            "4 specialist agents (Code, Config, Dependency, Doc RAG)",
            "Adversarial Critic physical disk line verification",
            "Deterministic risk scoring formula and Go/No-Go gate",
            "FastAPI REST backend and React 19 web console"
        ]),
        ("Currently In Progress / Next Phase", [
            "GitHub Actions PR bot workflow integration",
            "Automated patch PR generator for simple config fixes"
        ])
    ]

    for sec_title, sec_bullets in status_sections:
        add_para(tf_p8, sec_title, size_pt=11.5, bold=True, color=TEXT_MAIN, space_after=2)
        for b in sec_bullets:
            add_para(tf_p8, f"- {b}", size_pt=9.5, bold=False, color=TEXT_MUTED, space_after=2)
        add_para(tf_p8, "", size_pt=4, space_after=2)

    # Right: Automated Testing Suite Breakdown
    c_t8 = add_card(slide8, 6.863, 1.8, 5.67, 4.0, bg=CARD_BG, border=CARD_BORDER)
    tb_t8 = slide8.shapes.add_textbox(Inches(7.083), Inches(1.95), Inches(5.23), Inches(3.7))
    tf_t8 = tb_t8.text_frame
    tf_t8.word_wrap = True
    tf_t8.margin_left = tf_t8.margin_top = tf_t8.margin_right = tf_t8.margin_bottom = 0

    add_para(tf_t8, "62 AUTOMATED PYTEST SUITE BREAKDOWN", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=8)
    test_suites = [
        ("18 Ingestion & Vector RAG Tests", "AST parsing, markdown chunking, metadata retention, and ChromaDB cosine similarity retrieval."),
        ("16 Multi-Agent Orchestration Tests", "Concurrent task dispatch, isolated domain prompts, and Groq/Mock LLM fallback resilience."),
        ("14 Adversarial Critic Verification Tests", "Physical file existence verification, line reference bounds, and false-positive suppression heuristics."),
        ("14 Deterministic Risk & API Gateway Tests", "Mathematical formula consistency, Go/No-Go release threshold, and Pydantic schema validation.")
    ]
    for ts_name, ts_desc in test_suites:
        add_para(tf_t8, f"- {ts_name}", size_pt=11, bold=True, color=TEXT_MAIN, space_after=1)
        add_para(tf_t8, f"  {ts_desc}", size_pt=9.5, bold=False, color=TEXT_MUTED, space_after=5)

    c_bot8 = add_card(slide8, 0.8, 6.0, 11.733, 0.85, bg=SUCCESS_BG, border=CARD_BORDER)
    tb_b8 = slide8.shapes.add_textbox(Inches(1.0), Inches(6.12), Inches(11.333), Inches(0.6))
    tf_b8 = tb_b8.text_frame
    tf_b8.word_wrap = True
    tf_b8.margin_left = tf_b8.margin_top = tf_b8.margin_right = tf_b8.margin_bottom = 0

    add_para(tf_b8, "Test Execution & Quality Note (5% Rubric):", size_pt=10.5, bold=True, color=SUCCESS_GREEN, space_after=2)
    add_para(tf_b8, "All 62 unit and integration tests run locally and in CI with zero external API dependencies using a deterministic mock provider, ensuring fast, reproducible execution.", size_pt=11, bold=False, color=TEXT_MAIN, space_after=0)

    add_footer(slide8, 8)
    add_speaker_notes(slide8, {
        "talking_points": [
            "This slide presents an honest view of what is working today versus what is scheduled for the final evaluation.",
            "Our core backend, ChromaDB vector store, multi-agent engine, Critic, and web console are fully operational.",
            "To prove code quality, we have 62 automated unit and integration tests running in CI.",
            "Our test suite covers AST parsing, vector search, agent prompts, Critic line checks, and risk calculation."
        ],
        "question": "How do you ensure your automated tests are reliable?",
        "answer": "Our test suite exercises real file tree traversals, real ChromaDB vector insertions and cosine queries, real AST code parsing, and real mathematical risk calculations with zero mocking of internal business logic."
    })

    # =========================================================================
    # SLIDE 9: Docker Containerization & Demo Repositories
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide9)
    add_header(slide9, "Docker Architecture & Tested Repositories", "Multi-container setup via Docker Compose and evaluation across real codebases.")

    # Left: Docker Architecture
    c_dock = add_card(slide9, 0.8, 1.8, col_w2, card_h2, bg=CARD_BG, border=CARD_BORDER)
    tb_dk = slide9.shapes.add_textbox(Inches(1.02), Inches(1.98), Inches(col_w2 - 0.44), Inches(card_h2 - 0.36))
    tf_dk = tb_dk.text_frame
    tf_dk.word_wrap = True
    tf_dk.margin_left = tf_dk.margin_top = tf_dk.margin_right = tf_dk.margin_bottom = 0

    add_para(tf_dk, "DOCKER COMPOSE SETUP", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=6)
    dock_features = [
        ("FastAPI Backend Container", "Runs python:3.11-slim under dedicated non-root user 'appuser' (UID 1000) for security. Mounts persistent volume for ChromaDB SQLite."),
        ("Nginx Reverse Proxy", "Lightweight 21MB Alpine Nginx image. Serves compiled React 19 static assets and reverse-proxies /api/ requests, eliminating CORS friction."),
        ("Isolated Bridge Network", "Both containers communicate over internal 'deploysafe-net' bridge network with Docker health checks on /api/v1/health."),
        ("Single-Command Startup", "Runs with 'docker compose up --build -d', providing instant, reproducible deployment across Linux, macOS, and Windows.")
    ]
    for d_title, d_desc in dock_features:
        add_para(tf_dk, f"- {d_title}:", size_pt=11, bold=True, color=TEXT_MAIN, space_after=1)
        add_para(tf_dk, f"  {d_desc}", size_pt=9.5, bold=False, color=TEXT_MUTED, space_after=5)

    # Right: Live Demo Repositories
    c_demo = add_card(slide9, 6.863, 1.8, col_w2, card_h2, bg=CARD_BG, border=CARD_BORDER)
    tb_dm = slide9.shapes.add_textbox(Inches(7.083), Inches(1.98), Inches(col_w2 - 0.44), Inches(card_h2 - 0.36))
    tf_dm = tb_dm.text_frame
    tf_dm.word_wrap = True
    tf_dm.margin_left = tf_dm.margin_top = tf_dm.margin_right = tf_dm.margin_bottom = 0

    add_para(tf_dm, "EVALUATION REPOSITORIES TESTED", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=6)
    demo_points = [
        ("web-scrape (Node.js)", "Detected unpinned package dependencies and missing production build script in package.json."),
        ("bottle-app (Python WSGI)", "Detected missing production WSGI server (gunicorn) in Dockerfile and missing healthcheck endpoint."),
        ("demo-microservice (Python)", "Detected missing Redis container service in docker-compose.yml and undeclared DATABASE_URL secret."),
        ("Execution Speed Benchmark", "End-to-end multi-agent audit, Critic verification, and Groq LLM synthesis complete in ~5.0 seconds.")
    ]
    for dm_title, dm_desc in demo_points:
        add_para(tf_dm, f"- {dm_title}:", size_pt=11, bold=True, color=TEXT_MAIN, space_after=1)
        add_para(tf_dm, f"  {dm_desc}", size_pt=9.5, bold=False, color=TEXT_MUTED, space_after=5)

    # Bottom Banner
    c_bot9 = add_card(slide9, 0.8, 5.95, 11.733, 0.85, bg=ACCENT_BG, border=CARD_BORDER)
    tb_b9 = slide9.shapes.add_textbox(Inches(1.0), Inches(6.08), Inches(11.333), Inches(0.6))
    tf_b9 = tb_b9.text_frame
    tf_b9.word_wrap = True
    tf_b9.margin_left = tf_b9.margin_top = tf_b9.margin_right = tf_b9.margin_bottom = 0

    add_para(tf_b9, "Deployment Verification Status:", size_pt=10.5, bold=True, color=ACCENT_BLUE, space_after=2)
    add_para(tf_b9, "DeploySafe runs self-contained in Docker Compose with zero host dependencies other than Docker itself. Ready for cloud cluster deployment (ECS, Cloud Run, Kubernetes).", size_pt=11, bold=False, color=TEXT_MAIN, space_after=0)

    add_footer(slide9, 9)
    add_speaker_notes(slide9, {
        "talking_points": [
            "We containerized DeploySafe to production standards using Docker Compose.",
            "The backend runs securely under a dedicated non-root user with persistent Chroma storage.",
            "The frontend is compiled into static assets served by an ultra-light Nginx Alpine reverse proxy, eliminating CORS issues.",
            "In our live tests across real repositories, the entire pipeline executes in ~5.0 seconds with zero hallucinations."
        ],
        "question": "Why use a multi-stage Docker build for the frontend rather than running Node.js in production?",
        "answer": "A multi-stage build compiles our React application into lightweight static files during the build phase and discards all Node.js build tooling, producing an ultra-secure 21MB Alpine Nginx container with zero unnecessary runtime dependencies."
    })

    # =========================================================================
    # SLIDE 10: Project Roadmap & Individual Responsibilities (Grounded)
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide10)
    add_header(slide10, "Project Roadmap & Individual Responsibilities", "Next milestones for final evaluation and individual responsibility breakdown.")

    # Left: Roadmap
    c_road = add_card(slide10, 0.8, 1.8, col_w2, card_h2, bg=CARD_BG, border=CARD_BORDER)
    tb_rd = slide10.shapes.add_textbox(Inches(1.02), Inches(1.98), Inches(col_w2 - 0.44), Inches(card_h2 - 0.36))
    tf_rd = tb_rd.text_frame
    tf_rd.word_wrap = True
    tf_rd.margin_left = tf_rd.margin_top = tf_rd.margin_right = tf_rd.margin_bottom = 0

    add_para(tf_rd, "ROADMAP FOR FINAL EVALUATION (A3)", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=6)
    road_items = [
        ("GitHub Action Bot Integration", "Trigger analysis automatically on pull request events and post sticky comments with the risk breakdown."),
        ("Diff-Targeted Scans", "Analyze only files modified in the pull request to reduce analysis execution time to under 2.0 seconds."),
        ("Automated Patch PR Generator", "Generate ready-to-merge fix PRs for common issues (e.g., adding missing services to docker-compose.yml or pinning tags)."),
        ("Custom Policy Rules", "Allow teams to define organization-specific rules using declarative YAML policies.")
    ]
    for r_title, r_desc in road_items:
        add_para(tf_rd, f"- {r_title}:", size_pt=11, bold=True, color=TEXT_MAIN, space_after=1)
        add_para(tf_rd, f"  {r_desc}", size_pt=9.5, bold=False, color=TEXT_MUTED, space_after=5)

    # Right: Team Responsibility Matrix (Criterion C10)
    c_team = add_card(slide10, 6.863, 1.8, col_w2, card_h2, bg=CARD_BG, border=CARD_BORDER)
    tb_tm = slide10.shapes.add_textbox(Inches(7.083), Inches(1.98), Inches(col_w2 - 0.44), Inches(card_h2 - 0.36))
    tf_tm = tb_tm.text_frame
    tf_tm.word_wrap = True
    tf_tm.margin_left = tf_tm.margin_top = tf_tm.margin_right = tf_tm.margin_bottom = 0

    add_para(tf_tm, "INDIVIDUAL RESPONSIBILITIES (CRITERION C10)", size_pt=11, bold=True, color=ACCENT_BLUE, space_after=4)
    add_para(tf_tm, "Yash Rao — Lead Architect & Developer", size_pt=12, bold=True, color=TEXT_MAIN, space_after=8)

    roles = [
        ("Backend & API Architecture", "Designed FastAPI endpoints (/analyze, /repositories, /health) and Pydantic data schemas."),
        ("RAG & Ingestion Engine", "Implemented ChromaDB vector indexing and header-aware markdown AST chunking."),
        ("Multi-Agent Logic & Prompts", "Engineered specialist agent prompts, Critic validation checks, and Groq LLM integration."),
        ("Deterministic Risk Scoring", "Formulated the 0–100 mathematical risk calculation and Go/No-Go release threshold."),
        ("Docker & Test Engineering", "Created Docker Compose setup, Nginx reverse proxy, and 62 automated unit/integration tests."),
        ("Web Dashboard UI", "Built React 19 web console with real-time status polling and telemetry display.")
    ]
    for r_title, r_desc in roles:
        add_para(tf_tm, f"- {r_title}:", size_pt=10, bold=True, color=TEXT_MAIN, space_after=1)
        add_para(tf_tm, f"  {r_desc}", size_pt=9, bold=False, color=TEXT_MUTED, space_after=3)

    # Bottom Banner
    c_bot10 = add_card(slide10, 0.8, 5.95, 11.733, 0.85, bg=SUCCESS_BG, border=CARD_BORDER)
    tb_b10 = slide10.shapes.add_textbox(Inches(1.0), Inches(6.08), Inches(11.333), Inches(0.6))
    tf_b10 = tb_b10.text_frame
    tf_b10.word_wrap = True
    tf_b10.margin_left = tf_b10.margin_top = tf_b10.margin_right = tf_b10.margin_bottom = 0

    add_para(tf_b10, "Mid-Term Evaluation Readiness (A2 · 30%):", size_pt=10.5, bold=True, color=SUCCESS_GREEN, space_after=2)
    add_para(tf_b10, "Working prototype is functional, containerized, verified by 62 automated tests, and ready for live demonstration with Dr. Kiran Khatter & Mr. Naveen Singh.", size_pt=11, bold=False, color=TEXT_MAIN, space_after=0)

    add_footer(slide10, 10)
    add_speaker_notes(slide10, {
        "talking_points": [
            "To conclude, DeploySafe provides automated pre-deployment risk analysis to catch configuration drift before production.",
            "Our roadmap focuses on GitHub PR bot automation, diff-only scanning, and auto-fix PR generation.",
            "Under Criterion C10, I led the end-to-end architecture, RAG pipeline, agent prompts, testing, and container deployment.",
            "Thank you Dr. Kiran Khatter and Mr. Naveen Singh, and I warmly welcome your questions."
        ],
        "question": "What was the single most challenging architectural hurdle you solved in this midterm?",
        "answer": "Eliminating hallucination in risk scoring. By strictly restricting the LLM to evidence-backed finding proposals and delegating verification to the Critic and scoring to pure Python arithmetic, we created a system that engineers and managers can mathematically trust."
    })

    # Save Presentation (handles PowerPoint file locks gracefully)
    target_files = [
        "DeploySafe_Midterm_Presentation_CSE4011.pptx",
        "DeploySafe_Midterm_Presentation_v3.pptx",
        "DeploySafe_Midterm_Presentation_v2.pptx"
    ]

    saved_files = []
    locked_files = []

    for target in target_files:
        try:
            prs.save(target)
            saved_files.append(target)
            print(f"Successfully saved {target} ({len(prs.slides)} slides).")
        except PermissionError:
            locked_files.append(target)
            print(f"Notice: '{target}' is currently open/locked in PowerPoint.")

    if saved_files:
        print(f"\nDeck generation complete! Accessible files: {', '.join(saved_files)}")
    if locked_files:
        print(f"To update locked files ({', '.join(locked_files)}), close them in PowerPoint and re-run.")

if __name__ == "__main__":
    create_presentation()
