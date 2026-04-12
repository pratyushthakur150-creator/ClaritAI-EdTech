#!/usr/bin/env python3
"""
ClaritAI EdTech — Generate Course Material PDFs

Creates 3 PDF files in public/course-materials/:
1. data-science-module-1.pdf
2. upsc-polity-notes.pdf
3. fullstack-react-module2.pdf

Requires: pip install reportlab

Run: python -m scripts.seed_pdfs
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
except ImportError:
    print("ERROR: reportlab not installed. Run: pip install reportlab")
    sys.exit(1)

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "storage", "documents", "course-materials")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def add_section(doc, style_heading, style_body, title: str, items: list[str]):
    """Add a section with title and bullet items."""
    doc.append(Paragraph(title, style_heading))
    doc.append(Spacer(1, 6))
    for item in items:
        doc.append(Paragraph(f"• {item}", style_body))
        doc.append(Spacer(1, 4))
    doc.append(Spacer(1, 12))


def create_data_science_pdf():
    """PDF 1: Data Science & ML — Module 1"""
    path = os.path.join(OUTPUT_DIR, "data-science-module-1.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(name="H1", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
    h2 = ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=12, spaceAfter=8)
    body = ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=10, spaceAfter=4)

    story = []
    story.append(Paragraph("Data Science & ML — Module 1: Python for Data Science", h1))
    story.append(Paragraph("Instructor: Dr. Rajesh Kumar | ClaritAI EdTech", body))
    story.append(Spacer(1, 24))

    add_section(story, h2, body, "CHAPTER 1: Introduction to Python", [
        "Why Python for Data Science",
        "Installing Python & Jupyter Notebook",
        "Variables & Data Types: int, float, str, bool, list, dict, tuple",
        "Operators: arithmetic, comparison, logical",
        "Exercise: BMI Calculator Program",
    ])
    add_section(story, h2, body, "CHAPTER 2: NumPy for Numerical Computing", [
        "Arrays: np.array(), np.zeros(), np.arange()",
        "Slicing, reshaping, broadcasting",
        "Stats: mean, median, std, var",
        "Exercise: Analyze student marks with NumPy",
    ])
    add_section(story, h2, body, "CHAPTER 3: Pandas for Data Manipulation", [
        "DataFrames and Series",
        "Loading: read_csv(), read_excel()",
        "Exploring: head(), info(), describe()",
        "Filtering, sorting, grouping",
        "Missing values: dropna(), fillna()",
        "Exercise: Analyze Titanic dataset",
    ])
    add_section(story, h2, body, "CHAPTER 4: Data Visualization", [
        "Matplotlib: line, bar, histogram, scatter",
        "Seaborn: heatmaps and pair plots",
        "Customizing plots",
        "Exercise: Visualize sales trends",
    ])
    add_section(story, h2, body, "CHAPTER 5: Assignment", [
        "Key takeaways",
        "Assignment: EDA on e-commerce dataset",
        "Submit via student portal",
        "Next: Statistics for Data Science",
    ])
    doc.build(story)
    return path


def create_upsc_pdf():
    """PDF 2: UPSC Civil Services — Indian Polity"""
    path = os.path.join(OUTPUT_DIR, "upsc-polity-notes.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(name="H1", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
    h2 = ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=12, spaceAfter=8)
    body = ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=10, spaceAfter=4)

    story = []
    story.append(Paragraph("UPSC Civil Services — Indian Polity Complete Notes", h1))
    story.append(Paragraph("Instructor: Shri Arvind Sharma (Ex-IAS) | ClaritAI EdTech", body))
    story.append(Spacer(1, 24))

    add_section(story, h2, body, "UNIT 1: Constitutional Framework", [
        "Historical Background of Indian Constitution",
        "Making of the Constitution — Constituent Assembly",
        "Salient Features of the Constitution",
        "Preamble — Significance and Key Words",
        "Schedule Overview (1st to 12th)",
    ])
    add_section(story, h2, body, "UNIT 2: Fundamental Rights (Articles 12–35)", [
        "Right to Equality (Art. 14–18)",
        "Right to Freedom (Art. 19–22)",
        "Right Against Exploitation (Art. 23–24)",
        "Right to Freedom of Religion (Art. 25–28)",
        "Cultural & Educational Rights (Art. 29–30)",
        "Right to Constitutional Remedies (Art. 32)",
        "Doctrine of Severability & Eclipse",
    ])
    add_section(story, h2, body, "UNIT 3: Directive Principles & Fundamental Duties", [
        "Nature and Significance of DPSPs",
        "Classification: Socialist, Gandhian, Liberal",
        "Conflict between FRs and DPSPs",
        "42nd and 44th Amendment Implications",
        "Fundamental Duties (Art. 51A)",
    ])
    add_section(story, h2, body, "UNIT 4: Union Executive", [
        "President: Powers, Election, Impeachment",
        "Vice President: Role and Functions",
        "Prime Minister and Council of Ministers",
        "Cabinet vs Council of Ministers",
        "Attorney General of India",
    ])
    add_section(story, h2, body, "UNIT 5: Parliament", [
        "Lok Sabha and Rajya Sabha: Composition",
        "Sessions: Budget, Monsoon, Winter",
        "Legislative Procedures: Ordinary & Money Bills",
        "Parliamentary Committees",
        "Anti-Defection Law (10th Schedule)",
    ])
    story.append(Paragraph("PRACTICE QUESTIONS: 50 MCQs with answers and explanations", h2))
    doc.build(story)
    return path


def create_fullstack_pdf():
    """PDF 3: Full Stack Development — React.js"""
    path = os.path.join(OUTPUT_DIR, "fullstack-react-module2.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(name="H1", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
    h2 = ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=12, spaceAfter=8)
    body = ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=10, spaceAfter=4)

    story = []
    story.append(Paragraph("Full Stack Development — Module 2: React.js Fundamentals", h1))
    story.append(Paragraph("Instructor: Rohan Mehta (Ex-Google Engineer) | ClaritAI EdTech", body))
    story.append(Spacer(1, 24))

    add_section(story, h2, body, "CHAPTER 1: Introduction to React", [
        "What is React and why use it",
        "Virtual DOM explained",
        "Create React App setup",
        "JSX syntax and rules",
        "Components: Functional vs Class",
    ])
    add_section(story, h2, body, "CHAPTER 2: Props and State", [
        "Passing props to components",
        "Default props and prop types",
        "useState Hook — syntax and examples",
        "State lifting between components",
        "Controlled vs Uncontrolled components",
        "Exercise: Build a Todo App",
    ])
    add_section(story, h2, body, "CHAPTER 3: useEffect and Lifecycle", [
        "Side effects in React",
        "useEffect syntax and dependency array",
        "Fetching data with useEffect + Axios",
        "Cleanup functions",
        "Exercise: GitHub Profile Finder",
    ])
    add_section(story, h2, body, "CHAPTER 4: React Router", [
        "Client-side routing",
        "BrowserRouter, Route, Switch",
        "useParams, useHistory, useLocation",
        "Protected Routes",
        "Exercise: Multi-page Portfolio Site",
    ])
    add_section(story, h2, body, "CHAPTER 5: State Management", [
        "Context API — Provider and Consumer",
        "useContext Hook",
        "Introduction to Redux Toolkit",
        "Actions, Reducers, Store",
        "Exercise: Shopping Cart with Redux",
    ])
    add_section(story, h2, body, "CHAPTER 6: Assignment", [
        "Build a full Movie Search App",
        "Use The Movie DB API",
        "Implement search, filter, favorites",
        "Deploy to Vercel",
        "Next Module: Node.js and Express",
    ])
    doc.build(story)
    return path


def main():
    print("\n" + "=" * 50)
    print("  ClaritAI — Generating Course Material PDFs")
    print("=" * 50)
    paths = []
    try:
        paths.append(create_data_science_pdf())
        print(f"  OK Created: data-science-module-1.pdf")
        paths.append(create_upsc_pdf())
        print(f"  OK Created: upsc-polity-notes.pdf")
        paths.append(create_fullstack_pdf())
        print(f"  OK Created: fullstack-react-module2.pdf")
    except Exception as e:
        print(f"\nERROR: PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print(f"\n  PDFs saved to: {OUTPUT_DIR}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
