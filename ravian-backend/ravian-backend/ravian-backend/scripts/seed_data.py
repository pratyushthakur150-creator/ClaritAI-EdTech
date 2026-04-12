#!/usr/bin/env python3
"""
ClaritAI / Ravian EdTech Platform - MEGA Data Seeding Script

Seeds ALL modules with realistic B2B Indian EdTech data:
- Courses (15)
- Leads (45)
- Students (30)
- Demos (24)
- Calls (30)
- Enrollments (30)
- Chatbot Sessions (24)

Run from project root: python -m scripts.seed_data
Or: cd ravian-backend/ravian-backend/ravian-backend && python scripts/seed_data.py
"""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_session, session_scope
from app.core.auth import hash_password
from app.models import (
    Tenant, User, UserRole, SubscriptionPlan,
    Lead, LeadStatus, LeadSource, UrgencyLevel, ChatbotSession,
    CallLog, Demo, CallDirection, CallOutcome, SentimentScore,
    Enrollment, Student, PaymentStatus, RiskLevel,
    Course,
)

# Date helpers - all relative to now
TODAY = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def days_ago(n: int) -> datetime:
    return TODAY - timedelta(days=n)


def days_ahead(n: int) -> datetime:
    return TODAY + timedelta(days=n)


# ============== COURSES DATA (15) ==============
COURSES_DATA = [
    {
        "name": "UPSC Civil Services Complete Prep 2025",
        "price": "₹29,999",
        "duration_weeks": 52,
        "category": "Government Exams",
        "description": "Comprehensive UPSC CSE preparation covering all GS papers, Essay, and Optional subjects.",
        "modules": ["Indian Polity", "History", "Geography", "Economics", "Science & Tech", "Current Affairs", "Essay Writing", "Answer Writing", "CSAT"],
    },
    {
        "name": "SSC CGL Tier 1 & 2 Crash Course",
        "price": "₹8,999",
        "duration_weeks": 12,
        "category": "Government Exams",
        "description": "Fast-track SSC CGL preparation with topic-wise practice and 100 mock tests.",
        "modules": ["Quantitative Aptitude", "English Language", "General Intelligence", "General Awareness"],
    },
    {
        "name": "Data Science & Machine Learning Bootcamp",
        "price": "₹45,000",
        "duration_weeks": 26,
        "category": "Tech Skills",
        "description": "Industry-ready program covering Python, ML, deep learning, and real-world projects.",
        "modules": ["Python Fundamentals", "Statistics", "Machine Learning", "Deep Learning", "NLP", "Capstone Project"],
    },
    {
        "name": "CAT MBA Entrance Masterclass",
        "price": "₹18,999",
        "duration_weeks": 35,
        "category": "MBA Entrance",
        "description": "Complete CAT preparation with mock CATs, GD/PI training and IIM alumni mentors.",
        "modules": ["Quantitative Ability", "Verbal Ability", "Data Interpretation", "Logical Reasoning", "GD/PI Prep"],
    },
    {
        "name": "Full Stack Web Development with React & Node",
        "price": "₹35,000",
        "duration_weeks": 22,
        "category": "Tech Skills",
        "description": "End-to-end web dev from HTML to deploying production apps with React, Node.js, MongoDB.",
        "modules": ["HTML/CSS", "JavaScript", "React.js", "Node.js", "MongoDB", "REST APIs", "AWS Deployment"],
    },
    {
        "name": "GATE Computer Science 2025",
        "price": "₹12,999",
        "duration_weeks": 26,
        "category": "Government Exams",
        "description": "Structured GATE CS preparation covering all core subjects with PYQ analysis and mock tests.",
        "modules": ["Data Structures", "Algorithms", "DBMS", "Operating Systems", "Computer Networks", "TOC", "Compiler Design"],
    },
    {
        "name": "Digital Marketing Mastery",
        "price": "₹14,999",
        "duration_weeks": 12,
        "category": "Marketing",
        "description": "Hands-on digital marketing course with Google Ads, SEO, Social Media, and Analytics.",
        "modules": ["SEO & SEM", "Google Ads", "Social Media Marketing", "Email Marketing", "Analytics", "Content Strategy"],
    },
    {
        "name": "AWS Cloud Practitioner + Solutions Architect",
        "price": "₹22,000",
        "duration_weeks": 17,
        "category": "Tech Skills",
        "description": "Complete AWS certification prep with hands-on labs, exam strategies and live projects.",
        "modules": ["Cloud Fundamentals", "EC2 & S3", "VPC & Networking", "RDS & DynamoDB", "Lambda & Serverless", "Mock Exams"],
    },
    {
        "name": "IELTS Academic 7+ Band Course",
        "price": "₹6,999",
        "duration_weeks": 8,
        "category": "Language",
        "description": "Targeted IELTS prep with band-specific strategies for all four sections.",
        "modules": ["Listening", "Reading", "Writing Task 1 & 2", "Speaking", "Mock Tests", "Vocabulary Building"],
    },
    {
        "name": "Product Management Bootcamp",
        "price": "₹39,999",
        "duration_weeks": 17,
        "category": "Business",
        "description": "PM fundamentals to advanced roadmap planning, agile workflows and stakeholder management.",
        "modules": ["PM Fundamentals", "User Research", "Product Strategy", "Agile & Scrum", "Analytics", "Case Studies", "Interview Prep"],
    },
    {
        "name": "Stock Market & Options Trading",
        "price": "₹9,999",
        "duration_weeks": 8,
        "category": "Finance",
        "description": "Learn technical analysis, options strategies and risk management for Indian markets.",
        "modules": ["Market Basics", "Technical Analysis", "Fundamental Analysis", "Options Strategies", "Risk Management", "Live Trading Sessions"],
    },
    {
        "name": "Python Programming Zero to Hero",
        "price": "₹7,999",
        "duration_weeks": 8,
        "category": "Tech Skills",
        "description": "Complete Python programming from beginner to advanced with 50+ real projects.",
        "modules": ["Python Basics", "OOP", "File Handling", "APIs", "Web Scraping", "Django Intro", "Projects"],
    },
    {
        "name": "NEET Biology & Chemistry Intensive",
        "price": "₹24,999",
        "duration_weeks": 39,
        "category": "Medical Entrance",
        "description": "Focused NEET prep for Biology and Chemistry with NCERT deep dives and 200+ mocks.",
        "modules": ["Cell Biology", "Genetics", "Human Physiology", "Ecology", "Organic Chemistry", "Inorganic Chemistry", "Physical Chemistry"],
    },
    {
        "name": "UI/UX Design Fundamentals to Advanced",
        "price": "₹19,999",
        "duration_weeks": 12,
        "category": "Design",
        "description": "Master Figma, design thinking, user research and build a professional portfolio.",
        "modules": ["Design Thinking", "Figma Basics", "Wireframing", "Prototyping", "User Research", "Usability Testing", "Portfolio Projects"],
    },
    {
        "name": "Spoken English & Business Communication",
        "price": "₹4,999",
        "duration_weeks": 6,
        "category": "Language",
        "description": "Build confidence in spoken English for interviews, presentations and workplace communication.",
        "modules": ["Grammar Foundations", "Pronunciation", "Interview Skills", "Email Writing", "Presentation Skills", "Group Discussion"],
    },
]

# ============== LEADS DATA (45) ==============
LEAD_SOURCE_MAP = {
    "website": LeadSource.WEBSITE,
    "referral": LeadSource.REFERRAL,
    "linkedin": LeadSource.SOCIAL_MEDIA,
    "google_ads": LeadSource.ADVERTISING,
    "chatbot": LeadSource.CHATBOT,
    "instagram": LeadSource.SOCIAL_MEDIA,
}
LEAD_STATUS_MAP = {
    "new": LeadStatus.NEW,
    "contacted": LeadStatus.CONTACTED,
    "demo": LeadStatus.DEMO_SCHEDULED,
    "enrolled": LeadStatus.ENROLLED,
}
URGENCY_MAP = {
    "low": UrgencyLevel.LOW,
    "medium": UrgencyLevel.MEDIUM,
    "high": UrgencyLevel.HIGH,
    "critical": UrgencyLevel.CRITICAL,
}

LEADS_DATA = [
    ("Priya Sharma", "priya.sharma@infosys.com", "+91-9876543210", "new", "website", "Data Science & Machine Learning Bootcamp", "Infosys", "high"),
    ("Rahul Verma", "rahul.v@tcs.com", "+91-9823456789", "contacted", "referral", "Full Stack Web Development with React & Node", "TCS", "medium"),
    ("Ananya Krishnan", "ananya.k@wipro.com", "+91-9712345678", "demo", "linkedin", "Data Science & Machine Learning Bootcamp", "Wipro", "high"),
    ("Vikram Singh", "vikram.singh@hcl.com", "+91-9645678901", "new", "google_ads", "UPSC Civil Services Complete Prep 2025", "HCL", "low"),
    ("Deepika Nair", "deepika.nair@accenture.com", "+91-9534567890", "enrolled", "referral", "CAT MBA Entrance Masterclass", "Accenture", "critical"),
    ("Arjun Mehta", "arjun.mehta@cognizant.com", "+91-9423456789", "contacted", "chatbot", "SSC CGL Tier 1 & 2 Crash Course", "Cognizant", "medium"),
    ("Sunita Rao", "sunita.rao@deloitte.com", "+91-9312345678", "demo", "website", "Data Science & Machine Learning Bootcamp", "Deloitte", "high"),
    ("Karthik Iyer", "karthik.i@amazon.in", "+91-9201234567", "new", "instagram", "Full Stack Web Development with React & Node", "Amazon", "medium"),
    ("Meera Joshi", "meera.joshi@microsoft.com", "+91-9190123456", "contacted", "linkedin", "Data Science & Machine Learning Bootcamp", "Microsoft", "high"),
    ("Rohit Gupta", "rohit.gupta@swiggy.com", "+91-9089012345", "enrolled", "referral", "Full Stack Web Development with React & Node", "Swiggy", "low"),
    ("Nisha Patel", "nisha.patel@byju.com", "+91-8978901234", "demo", "google_ads", "CAT MBA Entrance Masterclass", "Byju's", "critical"),
    ("Amit Dubey", "amit.dubey@zepto.com", "+91-8867890123", "new", "website", "UPSC Civil Services Complete Prep 2025", "Zepto", "medium"),
    ("Kavya Reddy", "kavya.reddy@flipkart.com", "+91-8756789012", "contacted", "referral", "SSC CGL Tier 1 & 2 Crash Course", "Flipkart", "low"),
    ("Saurabh Tiwari", "saurabh.t@zomato.com", "+91-8645678901", "new", "chatbot", "Data Science & Machine Learning Bootcamp", "Zomato", "high"),
    ("Pooja Banerjee", "pooja.b@razorpay.com", "+91-8534567890", "demo", "linkedin", "Full Stack Web Development with React & Node", "Razorpay", "critical"),
    ("Aditya Kapoor", "aditya.k@paytm.com", "+91-8423456789", "new", "google_ads", "AWS Cloud Practitioner + Solutions Architect", "Paytm", "high"),
    ("Shreya Malhotra", "shreya.m@phonepe.com", "+91-8312345678", "contacted", "website", "Product Management Bootcamp", "PhonePe", "medium"),
    ("Nitin Aggarwal", "nitin.a@ola.com", "+91-8201234567", "demo", "referral", "Data Science & Machine Learning Bootcamp", "Ola", "high"),
    ("Ritu Saxena", "ritu.s@nykaa.com", "+91-8190123456", "new", "instagram", "Digital Marketing Mastery", "Nykaa", "medium"),
    ("Varun Khanna", "varun.k@meesho.com", "+91-8089012345", "contacted", "linkedin", "Full Stack Web Development with React & Node", "Meesho", "high"),
    ("Pallavi Desai", "pallavi.d@cred.club", "+91-7978901234", "new", "website", "Product Management Bootcamp", "CRED", "critical"),
    ("Siddharth Nair", "siddharth.n@groww.in", "+91-7867890123", "demo", "referral", "Stock Market & Options Trading", "Groww", "high"),
    ("Ishita Bose", "ishita.b@zerodha.com", "+91-7756789012", "contacted", "chatbot", "Stock Market & Options Trading", "Zerodha", "medium"),
    ("Mayank Tomar", "mayank.t@upstox.com", "+91-7645678901", "new", "google_ads", "Stock Market & Options Trading", "Upstox", "low"),
    ("Ankita Jain", "ankita.j@lenskart.com", "+91-7534567890", "contacted", "website", "Digital Marketing Mastery", "Lenskart", "medium"),
    ("Harsh Pandey", "harsh.p@cars24.com", "+91-7423456789", "new", "instagram", "Full Stack Web Development with React & Node", "Cars24", "high"),
    ("Divya Kumar", "divya.k@urban.company", "+91-7312345678", "demo", "linkedin", "UI/UX Design Fundamentals to Advanced", "UrbanCompany", "critical"),
    ("Rohini Shetty", "rohini.s@myntra.com", "+91-7201234567", "new", "referral", "Digital Marketing Mastery", "Myntra", "medium"),
    ("Gaurav Tripathi", "gaurav.t@policyb.com", "+91-7190123456", "contacted", "google_ads", "Data Science & Machine Learning Bootcamp", "PolicyBazaar", "high"),
    ("Sneha Pillai", "sneha.p@makemy.com", "+91-7089012345", "new", "chatbot", "Python Programming Zero to Hero", "MakeMyTrip", "low"),
    ("Tarun Bhatt", "tarun.b@cleartrip.com", "+91-6978901234", "demo", "website", "Full Stack Web Development with React & Node", "Cleartrip", "medium"),
    ("Monika Yadav", "monika.y@indmart.com", "+91-6867890123", "new", "linkedin", "Spoken English & Business Communication", "IndiaMART", "high"),
    ("Ajay Rawat", "ajay.r@justdial.com", "+91-6756789012", "contacted", "referral", "Digital Marketing Mastery", "JustDial", "medium"),
    ("Farida Sheikh", "farida.s@quikr.com", "+91-6645678901", "new", "instagram", "UI/UX Design Fundamentals to Advanced", "Quikr", "low"),
    ("Sandeep Mishra", "sandeep.m@olx.in", "+91-6534567890", "contacted", "google_ads", "Product Management Bootcamp", "OLX", "high"),
    ("Kavitha Nambiar", "kavitha.n@freshworks.com", "+91-6423456789", "demo", "linkedin", "Data Science & Machine Learning Bootcamp", "Freshworks", "critical"),
    ("Rohan Choudhary", "rohan.c@zoho.com", "+91-6312345678", "new", "website", "Python Programming Zero to Hero", "Zoho", "medium"),
    ("Preethi Menon", "preethi.m@infysoft.com", "+91-6201234567", "contacted", "chatbot", "AWS Cloud Practitioner + Solutions Architect", "Infosys BPM", "high"),
    ("Abhijit Ghosh", "abhijit.g@tatacon.com", "+91-6190123456", "new", "referral", "GATE Computer Science 2025", "Tata Consultancy", "medium"),
    ("Lavanya Krishnan", "lavanya.k@wiptech.com", "+91-6089012345", "demo", "google_ads", "GATE Computer Science 2025", "Wipro Digital", "high"),
    ("Sameer Saxena", "sameer.s@relia.com", "+91-5978901234", "new", "instagram", "UPSC Civil Services Complete Prep 2025", "Reliance Jio", "low"),
    ("Divyanshu Agarwal", "divyanshu.a@bajaj.com", "+91-5867890123", "contacted", "linkedin", "Stock Market & Options Trading", "Bajaj Finserv", "medium"),
    ("Sudha Ramachandran", "sudha.r@hdfcbank.com", "+91-5756789012", "new", "website", "Spoken English & Business Communication", "HDFC Bank", "high"),
    ("Manish Verma", "manish.v@icicibank.com", "+91-5645678901", "demo", "referral", "Product Management Bootcamp", "ICICI Bank", "critical"),
    ("Tanmay Kulkarni", "tanmay.k@yesbank.com", "+91-5534567890", "contacted", "chatbot", "Data Science & Machine Learning Bootcamp", "Yes Bank", "medium"),
]

# Course name -> Course object lookup (populated after seeding courses)
COURSE_BY_NAME: dict[str, Course] = {}
LEAD_BY_EMAIL: dict[str, Lead] = {}


def seed_tenant_and_user(session: Session) -> tuple[Tenant, User]:
    """Create or get ClaritAI tenant and seed admin user."""
    tenant = session.query(Tenant).filter(Tenant.domain == "claritai.ravian.com").first()
    if not tenant:
        tenant = Tenant(
            name="ClaritAI EdTech",
            domain="claritai.ravian.com",
            subscription_plan=SubscriptionPlan.GROWTH,
            credits_remaining=5000,
        )
        session.add(tenant)
        session.flush()
        print("  Created tenant: ClaritAI EdTech")
    else:
        print("  Using existing tenant: ClaritAI EdTech")

    admin_email = "admin@claritai.com"
    user = session.query(User).filter(User.email == admin_email, User.tenant_id == tenant.id).first()
    if not user:
        user = User(
            tenant_id=tenant.id,
            email=admin_email,
            password_hash=hash_password("Admin@123"),
            first_name="John",
            last_name="Doe",
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(user)
        session.flush()
        print("  Created admin user: John Doe (admin@claritai.com)")
    else:
        print("  Using existing admin user: John Doe")
    return tenant, user


def seed_courses(session: Session, tenant: Tenant) -> int:
    """Seed 15 courses. Upsert by name."""
    count = 0
    for c in COURSES_DATA:
        existing = session.query(Course).filter(
            Course.tenant_id == tenant.id,
            Course.name == c["name"],
        ).first()
        if existing:
            COURSE_BY_NAME[c["name"]] = existing
            continue
        course = Course(
            tenant_id=tenant.id,
            name=c["name"],
            description=c["description"],
            price=c["price"],
            duration_weeks=c["duration_weeks"],
            category=c["category"],
            modules=c["modules"],
            is_active="true",
            is_published="true",
        )
        session.add(course)
        session.flush()
        COURSE_BY_NAME[c["name"]] = course
        count += 1
    return count


def seed_leads(session: Session, tenant: Tenant, admin_user: User) -> int:
    """Seed 45 leads. Upsert by email."""
    count = 0
    for name, email, phone, status, source, course_name, company, urgency in LEADS_DATA:
        existing = session.query(Lead).filter(
            Lead.tenant_id == tenant.id,
            Lead.email == email,
        ).first()
        if existing:
            LEAD_BY_EMAIL[email] = existing
            continue
        lead = Lead(
            tenant_id=tenant.id,
            created_by=admin_user.id,
            name=name,
            email=email,
            phone=phone,
            source=LEAD_SOURCE_MAP.get(source, LeadSource.WEBSITE),
            status=LEAD_STATUS_MAP.get(status, LeadStatus.NEW),
            intent=course_name,
            interested_courses=[course_name] if course_name else None,
            urgency=URGENCY_MAP.get(urgency, UrgencyLevel.MEDIUM),
            notes=f"Company: {company}",
        )
        session.add(lead)
        session.flush()
        LEAD_BY_EMAIL[email] = lead
        count += 1
    return count


def seed_demos(session: Session, tenant: Tenant, admin_user: User) -> int:
    """Seed 24 demos (12 upcoming, 12 past)."""
    demos_spec = [
        # Upcoming (TODAY+1d to TODAY+10d)
        ("Ananya Krishnan", "Data Science & Machine Learning Bootcamp", 2, "11:00", "scheduled", "https://meet.google.com/abc-defg-hij", "Wipro wants 20-employee batch. Budget ₹9L approved."),
        ("Sunita Rao", "Data Science & Machine Learning Bootcamp", 3, "15:00", "scheduled", "https://meet.google.com/xyz-uvwx-yz1", "Senior manager at Deloitte. Team upskilling initiative."),
        ("Nisha Patel", "CAT MBA Entrance Masterclass", 5, "10:00", "scheduled", "https://zoom.us/j/123456789", "Weekend batch preferred. 2 colleagues also interested."),
        ("Pooja Banerjee", "Full Stack Web Development with React & Node", 7, "16:00", "scheduled", "https://meet.google.com/pqr-stuv-wx2", "Razorpay sponsoring fees. Strong conversion."),
        ("Nitin Aggarwal", "Data Science & Machine Learning Bootcamp", 1, "14:00", "scheduled", "https://zoom.us/j/987654321", "Ola data team needs 5 analysts upskilled urgently."),
        ("Kavitha Nambiar", "Data Science & Machine Learning Bootcamp", 4, "11:30", "scheduled", "https://meet.google.com/lmn-opqr-st3", "Freshworks L&D. 15 employees. Needs custom curriculum."),
        ("Divya Kumar", "UI/UX Design Fundamentals to Advanced", 2, "17:00", "scheduled", "https://zoom.us/j/456789123", "UrbanCompany design team needs 8 seats."),
        ("Manish Verma", "Product Management Bootcamp", 6, "12:00", "scheduled", "https://meet.google.com/uvw-xyza-bc4", "ICICI Bank PM team. 10 manager-level employees."),
        ("Siddharth Nair", "Stock Market & Options Trading", 3, "18:00", "scheduled", "https://zoom.us/j/789012345", "Groww employee. Personal enrollment + 2 friends."),
        ("Shreya Malhotra", "Product Management Bootcamp", 8, "10:30", "scheduled", "https://meet.google.com/def-ghij-kl5", "PhonePe mid-level PMs. Corporate invoice needed."),
        ("Lavanya Krishnan", "GATE Computer Science 2025", 9, "15:30", "scheduled", "https://zoom.us/j/321654987", "Wipro Digital freshers batch. 25 employees."),
        ("Pallavi Desai", "Product Management Bootcamp", 10, "14:30", "scheduled", "https://meet.google.com/mno-pqrs-tu6", "CRED product team. Very high urgency. Big budget."),
        # Past
        ("Vikram Singh", "UPSC Civil Services Complete Prep 2025", -10, "14:00", "completed", None, "Good session. Sent study materials. Needs 1 week to decide."),
        ("Arjun Mehta", "SSC CGL Tier 1 & 2 Crash Course", -7, "11:30", "completed", None, "Engaged well. Offered EMI option. Following up."),
        ("Karthik Iyer", "Full Stack Web Development with React & Node", -5, "17:00", "completed", None, "Amazon L&D reimbursement. Group of 5. Negotiating."),
        ("Meera Joshi", "Data Science & Machine Learning Bootcamp", -3, "12:00", "no_show", None, "Did not attend. WhatsApp follow-up sent."),
        ("Aditya Kapoor", "AWS Cloud Practitioner + Solutions Architect", -8, "16:00", "completed", None, "Paytm cloud team. Very impressed. Wants 10 seats."),
        ("Rohini Shetty", "Digital Marketing Mastery", -6, "11:00", "completed", None, "Myntra marketing intern. Self-funded. Signed up after demo."),
        ("Gaurav Tripathi", "Data Science & Machine Learning Bootcamp", -4, "15:00", "completed", None, "PolicyBazaar analytics team. Requested detailed syllabus."),
        ("Sandeep Mishra", "Product Management Bootcamp", -9, "14:00", "completed", None, "OLX PM team. 6 attendees on call. Very positive response."),
        ("Tarun Bhatt", "Full Stack Web Development with React & Node", -2, "17:30", "completed", None, "Cleartrip tech team. Asked about placement support."),
        ("Ajay Rawat", "Digital Marketing Mastery", -11, "10:00", "cancelled", None, "Cancelled 1 hour before. Reschedule requested."),
        ("Rohan Choudhary", "Python Programming Zero to Hero", -14, "16:30", "completed", None, "Zoho developer. Wants advanced Python. Enrolled same day."),
        ("Preethi Menon", "AWS Cloud Practitioner + Solutions Architect", -12, "13:00", "completed", None, "Infosys BPM. 8 cloud engineers. Exploring certification path."),
    ]
    count = 0
    for lead_name, course_name, day_offset, time_str, outcome, meeting_link, notes in demos_spec:
        lead = session.query(Lead).join(Lead.tenant).filter(
            Lead.tenant_id == tenant.id,
            Lead.name == lead_name,
        ).first()
        if not lead:
            continue
        course = COURSE_BY_NAME.get(course_name)
        when = days_ahead(day_offset) if day_offset > 0 else days_ago(-day_offset)
        hour, minute = map(int, time_str.split(":"))
        when = when.replace(hour=hour, minute=minute, second=0, microsecond=0)
        existing = session.query(Demo).filter(
            Demo.lead_id == lead.id,
            Demo.scheduled_at == when,
        ).first()
        if existing:
            continue
        demo = Demo(
            tenant_id=tenant.id,
            lead_id=lead.id,
            mentor_id=admin_user.id,
            course_id=course.id if course else None,
            scheduled_at=when,
            duration_minutes=60,
            completed=(outcome in ("completed", "no_show", "cancelled")),
            attended=(outcome == "completed"),
            outcome=outcome,
            notes=notes,
            meeting_link=meeting_link,
            platform="Zoom" if meeting_link and "zoom" in (meeting_link or "") else "Google Meet",
        )
        session.add(demo)
        count += 1
    return count


def seed_calls(session: Session, tenant: Tenant, admin_user: User) -> int:
    """Seed 30 call logs."""
    calls_spec = [
        ("Priya Sharma", 512, "completed", 1, "Discussed curriculum. Very interested. Wants brochure sent.", "follow_up"),
        ("Rahul Verma", 310, "completed", 2, "TCS L&D considering bulk for 10 devs. Escalating internally.", "demo_scheduled"),
        ("Vikram Singh", 765, "completed", 3, "Long call. UPSC strategy discussion. Will call back in a week.", "follow_up"),
        ("Arjun Mehta", 260, "completed", 4, "Intro call done. Sent course details on WhatsApp.", "interested"),
        ("Saurabh Tiwari", 0, "no_answer", 1, "No answer. Left voicemail. Retry tomorrow.", "retry"),
        ("Kavya Reddy", 415, "completed", 5, "Comparing with Unacademy. Highlighted our smaller batch sizes.", "follow_up"),
        ("Amit Dubey", 552, "completed", 2, "Wants UPSC + offline tests. Delhi centre confirmed.", "interested"),
        ("Meera Joshi", 220, "completed", 6, "Confirmed demo, later no-show. Rescheduling.", "reschedule"),
        ("Karthik Iyer", 690, "completed", 4, "Amazon group pricing. 5 seats. Corporate invoice needed.", "negotiating"),
        ("Pooja Banerjee", 470, "completed", 1, "Very excited. Demo booked. Razorpay to reimburse fees.", "demo_scheduled"),
        ("Aditya Kapoor", 360, "completed", 3, "Paytm cloud infra team. Needs AWS certs. 10 seats confirmed.", "enrolled"),
        ("Shreya Malhotra", 495, "completed", 5, "PhonePe PM role. Weekend batch needed. Shortlisted us.", "demo_scheduled"),
        ("Nitin Aggarwal", 860, "completed", 2, "Ola data team. Urgent upskilling. Director on call too.", "demo_scheduled"),
        ("Ritu Saxena", 345, "completed", 4, "Nykaa growth team. Wants social media + SEO focus.", "interested"),
        ("Varun Khanna", 190, "no_answer", 1, "Busy signal. Try evening.", "retry"),
        ("Pallavi Desai", 600, "completed", 3, "CRED product team. High intent. Escalated to director.", "demo_scheduled"),
        ("Siddharth Nair", 450, "completed", 2, "Groww employee. Personal + 2 friends. Group discount shared.", "demo_scheduled"),
        ("Ishita Bose", 295, "completed", 6, "Zerodha. Interested in trading course. Sent syllabus.", "interested"),
        ("Mayank Tomar", 0, "no_answer", 2, "No answer. Left SMS.", "retry"),
        ("Ankita Jain", 520, "completed", 5, "Lenskart marketing. Strong interest. Checking with manager.", "follow_up"),
        ("Harsh Pandey", 380, "completed", 3, "Cars24 backend team. Full Stack course. Self-funded.", "interested"),
        ("Divya Kumar", 540, "completed", 1, "UrbanCompany design team. 8 seats confirmed. Invoice requested.", "enrolled"),
        ("Rohini Shetty", 315, "completed", 7, "Myntra. Self-enrollment post demo. Paid via UPI.", "enrolled"),
        ("Gaurav Tripathi", 705, "completed", 4, "PolicyBazaar analytics. 12 employees. Wants pilot of 3 first.", "negotiating"),
        ("Sneha Pillai", 210, "completed", 6, "MakeMyTrip. Python basics for data cleaning. Budget approved.", "interested"),
        ("Tarun Bhatt", 420, "completed", 2, "Cleartrip. Wants placement assurance clause. Reviewing contract.", "negotiating"),
        ("Monika Yadav", 405, "completed", 5, "IndiaMART. English course for customer support team. 20 seats.", "demo_scheduled"),
        ("Kavitha Nambiar", 730, "completed", 3, "Freshworks. Custom curriculum request. Sharing RFQ.", "demo_scheduled"),
        ("Lavanya Krishnan", 535, "completed", 1, "Wipro Digital. 25 fresh graduates for GATE prep. Director approved.", "demo_scheduled"),
        ("Manish Verma", 570, "completed", 2, "ICICI Bank. PM training for 10. Compliance sign-off in progress.", "demo_scheduled"),
    ]
    count = 0
    for lead_name, duration_sec, call_status, day_offset, notes, _ in calls_spec:
        lead = session.query(Lead).filter(
            Lead.tenant_id == tenant.id,
            Lead.name == lead_name,
        ).first()
        if not lead:
            continue
        when = days_ago(day_offset)
        outcome = CallOutcome.NO_ANSWER if call_status == "no_answer" else CallOutcome.CONNECTED
        call = CallLog(
            tenant_id=tenant.id,
            lead_id=lead.id,
            agent_id=admin_user.id,
            call_direction=CallDirection.OUTBOUND,
            duration=duration_sec,
            outcome=outcome,
            notes=notes,
        )
        session.add(call)
        count += 1
    return count


def seed_enrollments_and_students(
    session: Session, tenant: Tenant, admin_user: User
) -> tuple[int, int]:
    """Seed 30 enrollments and 30 students. Student data from prompt."""
    students_spec = [
        ("Deepika Nair", "CAT MBA Entrance Masterclass", 18999, "paid", "UPI", 45, "active", 45),
        ("Rohit Gupta", "Full Stack Web Development with React & Node", 35000, "paid", "credit_card", 60, "active", 78),
        ("Tanvi Kulkarni", "UPSC Civil Services Complete Prep 2025", 29999, "paid", "net_banking", 20, "active", 30),
        ("Harish Menon", "Data Science & Machine Learning Bootcamp", 45000, "emi", "EMI 3x", 55, "active", 55),
        ("Sneha Agarwal", "SSC CGL Tier 1 & 2 Crash Course", 8999, "paid", "UPI", 80, "active", 90),
        ("Ravi Kumar", "Full Stack Web Development with React & Node", 35000, "emi", "EMI 6x", 30, "active", 15),
        ("Preethi Suresh", "CAT MBA Entrance Masterclass", 18999, "paid", "debit_card", 70, "active", 68),
        ("Nikhil Sharma", "Data Science & Machine Learning Bootcamp", 45000, "paid", "credit_card", 25, "active", 22),
        ("Anjali Mishra", "UPSC Civil Services Complete Prep 2025", 29999, "paid", "UPI", 90, "active", 60),
        ("Vivek Pandey", "SSC CGL Tier 1 & 2 Crash Course", 8999, "paid", "net_banking", 75, "active", 85),
        ("Akash Joshi", "Python Programming Zero to Hero", 7999, "paid", "UPI", 100, "completed", 100),
        ("Swati Prabhu", "Digital Marketing Mastery", 14999, "paid", "credit_card", 40, "active", 72),
        ("Roshan D'Souza", "AWS Cloud Practitioner + Solutions Architect", 22000, "emi", "EMI 3x", 50, "active", 48),
        ("Poonam Gupta", "IELTS Academic 7+ Band Course", 6999, "paid", "UPI", 55, "active", 95),
        ("Sanjay Negi", "Stock Market & Options Trading", 9999, "paid", "debit_card", 35, "active", 63),
        ("Meghna Roy", "UI/UX Design Fundamentals to Advanced", 19999, "emi", "EMI 6x", 15, "active", 38),
        ("Alok Srivastava", "GATE Computer Science 2025", 12999, "paid", "net_banking", 65, "active", 52),
        ("Poornima Iyer", "Product Management Bootcamp", 39999, "emi", "EMI 3x", 85, "active", 80),
        ("Dhruv Malhotra", "Full Stack Web Development with React & Node", 35000, "paid", "credit_card", 22, "active", 40),
        ("Kritika Saxena", "CAT MBA Entrance Masterclass", 18999, "paid", "UPI", 18, "active", 25),
        ("Brijesh Tiwari", "UPSC Civil Services Complete Prep 2025", 29999, "paid", "net_banking", 95, "active", 70),
        ("Chaitanya Rao", "Data Science & Machine Learning Bootcamp", 45000, "paid", "credit_card", 110, "active", 88),
        ("Falguni Shah", "Spoken English & Business Communication", 4999, "paid", "UPI", 42, "completed", 100),
        ("Girish Kumar", "Python Programming Zero to Hero", 7999, "paid", "debit_card", 28, "active", 60),
        ("Hemant Jha", "NEET Biology & Chemistry Intensive", 24999, "emi", "EMI 6x", 33, "active", 44),
        ("Indira Pillai", "Digital Marketing Mastery", 14999, "paid", "credit_card", 78, "active", 92),
        ("Jayesh Patil", "AWS Cloud Practitioner + Solutions Architect", 22000, "paid", "UPI", 20, "active", 33),
        ("Komal Chaudhary", "SSC CGL Tier 1 & 2 Crash Course", 8999, "paid", "net_banking", 68, "active", 77),
        ("Lalit Mishra", "Stock Market & Options Trading", 9999, "paid", "UPI", 48, "active", 55),
        ("Madhuri Deshpande", "UI/UX Design Fundamentals to Advanced", 19999, "emi", "EMI 3x", 12, "active", 18),
    ]
    # Need to create leads for students who may not exist (e.g. Tanvi Kulkarni, Harish Menon)
    student_emails = {
        "Deepika Nair": "deepika.nair@accenture.com",
        "Rohit Gupta": "rohit.gupta@swiggy.com",
        "Tanvi Kulkarni": "tanvi.k@gmail.com",
        "Harish Menon": "harish.m@outlook.com",
        "Sneha Agarwal": "sneha.ag@yahoo.com",
        "Ravi Kumar": "ravi.kumar@gmail.com",
        "Preethi Suresh": "preethi.s@gmail.com",
        "Nikhil Sharma": "nikhil.sh@outlook.com",
        "Anjali Mishra": "anjali.m@gmail.com",
        "Vivek Pandey": "vivek.p@gmail.com",
        "Akash Joshi": "akash.j@hotmail.com",
        "Swati Prabhu": "swati.p@gmail.com",
        "Roshan D'Souza": "roshan.d@gmail.com",
        "Poonam Gupta": "poonam.g@rediffmail.com",
        "Sanjay Negi": "sanjay.n@gmail.com",
        "Meghna Roy": "meghna.r@gmail.com",
        "Alok Srivastava": "alok.s@outlook.com",
        "Poornima Iyer": "poornima.i@gmail.com",
        "Dhruv Malhotra": "dhruv.m@gmail.com",
        "Kritika Saxena": "kritika.s@gmail.com",
        "Brijesh Tiwari": "brijesh.t@gmail.com",
        "Chaitanya Rao": "chaitanya.r@hotmail.com",
        "Falguni Shah": "falguni.s@gmail.com",
        "Girish Kumar": "girish.k@gmail.com",
        "Hemant Jha": "hemant.j@gmail.com",
        "Indira Pillai": "indira.p@gmail.com",
        "Jayesh Patil": "jayesh.pt@outlook.com",
        "Komal Chaudhary": "komal.c@gmail.com",
        "Lalit Mishra": "lalit.m@gmail.com",
        "Madhuri Deshpande": "madhuri.d@gmail.com",
    }
    enroll_count = 0
    student_count = 0
    for name, course_name, amount, pay_type, pay_method, days_ago_val, status, completion_pct in students_spec:
        email = student_emails.get(name)
        lead = session.query(Lead).filter(
            Lead.tenant_id == tenant.id,
            Lead.email == email,
        ).first() if email else None
        if not lead:
            lead = session.query(Lead).filter(
                Lead.tenant_id == tenant.id,
                Lead.name == name,
            ).first()
        if not lead:
            lead = Lead(
                tenant_id=tenant.id,
                created_by=admin_user.id,
                name=name,
                email=email or f"{name.lower().replace(' ', '.')}@student.com",
                source=LeadSource.REFERRAL,
                status=LeadStatus.ENROLLED,
            )
            session.add(lead)
            session.flush()
        course = COURSE_BY_NAME.get(course_name)
        if not course:
            continue
        enrolled_at = days_ago(days_ago_val)
        payment_status = PaymentStatus.PAID if pay_type == "paid" else PaymentStatus.PARTIAL
        enrollment = Enrollment(
            tenant_id=tenant.id,
            lead_id=lead.id,
            course_id=course.id,
            enrolled_at=enrolled_at,
            start_date=enrolled_at,
            payment_status=payment_status,
            total_amount=Decimal(str(amount)),
            amount_paid=Decimal(str(amount)) if pay_type == "paid" else Decimal("0"),
            currency="INR",
            payment_plan=pay_method,
        )
        session.add(enrollment)
        session.flush()
        risk_level = RiskLevel.LOW
        if completion_pct < 25 and status == "active":
            risk_level = RiskLevel.HIGH
        elif completion_pct < 40 and status == "active":
            risk_level = RiskLevel.MEDIUM
        student = Student(
            lead_id=lead.id,
            tenant_id=tenant.id,
            enrollment_id=enrollment.id,
            completion_percentage=Decimal(str(completion_pct)),
            last_active=days_ago(min(days_ago_val // 3, 5)),
            risk_level=risk_level,
            modules_completed=int(completion_pct / 10) if completion_pct < 100 else 10,
            modules_total=10,
        )
        session.add(student)
        enroll_count += 1
        student_count += 1
    return enroll_count, student_count


def seed_chatbot_sessions(session: Session, tenant: Tenant) -> int:
    """Seed 24 chatbot sessions with conversations."""
    sessions_spec = [
        (1, "Priya Sharma", True, 9, 240),
        (2, "Saurabh Tiwari", True, 5, 120),
        (3, None, False, 11, 360),
        (4, "Amit Dubey", True, 7, 180),
        (5, "Kavya Reddy", True, 8, 300),
        (6, None, False, 3, 60),
        (7, "Karthik Iyer", True, 13, 420),
        (8, "Pooja Banerjee", True, 9, 240),
        (9, "Aditya Kapoor", True, 10, 300),
        (10, "Ritu Saxena", True, 6, 180),
        (11, "Nitin Aggarwal", True, 15, 480),
        (12, None, False, 4, 120),
        (13, "Pallavi Desai", True, 12, 360),
        (14, "Varun Khanna", True, 8, 240),
        (15, None, False, 5, 180),
        (16, "Gaurav Tripathi", True, 14, 540),
        (17, None, False, 4, 120),
        (18, "Ankita Jain", True, 9, 300),
        (19, "Harsh Pandey", True, 7, 240),
        (20, "Divya Kumar", True, 11, 360),
        (21, "Sneha Pillai", True, 6, 180),
        (22, "Monika Yadav", True, 12, 420),
        (23, "Abhijit Ghosh", True, 9, 300),
        (24, "Sameer Saxena", True, 7, 240),
    ]
    count = 0
    for day_offset, lead_name, lead_captured, msg_count, duration_sec in sessions_spec:
        lead = None
        if lead_name:
            lead = session.query(Lead).filter(
                Lead.tenant_id == tenant.id,
                Lead.name == lead_name,
            ).first()
        created = days_ago(day_offset)
        conv = [
            {"sender": "user", "message": "Hi, I want to know about Data Science course", "timestamp": created.isoformat()},
            {"sender": "bot", "message": "Welcome to ClaritAI! Our Data Science & ML Bootcamp is a 6-month program.", "timestamp": created.isoformat()},
        ]
        if msg_count > 2:
            for i in range(msg_count - 2):
                conv.append({"sender": "user" if i % 2 == 0 else "bot", "message": f"Message {i+1}", "timestamp": created.isoformat()})
        session_id = str(uuid.uuid4())
        cs = ChatbotSession(
            tenant_id=tenant.id,
            lead_id=lead.id if lead else None,
            session_id=session_id,
            conversation=conv,
            message_count=msg_count,
            duration_seconds=duration_sec,
            lead_captured="true" if lead_captured else "false",
            engagement_score=min(msg_count * 10, 100),
        )
        session.add(cs)
        if lead and lead_captured:
            session.flush()
            lead.chatbot_session_id = cs.id
        count += 1
    return count


def run_seed():
    """Main seed runner."""
    print("\n" + "=" * 60)
    print("  ClaritAI / Ravian EdTech — MEGA Data Seeding")
    print("=" * 60)
    try:
        with session_scope() as session:
            tenant, admin_user = seed_tenant_and_user(session)
            print("\n[COURSES] Seeding Courses...")
            c = seed_courses(session, tenant)
            print(f"  OK Courses: {c} new, {len(COURSES_DATA)} total")

            print("\n[LEADS] Seeding Leads...")
            l = seed_leads(session, tenant, admin_user)
            print(f"  OK Leads: {l} new, {len(LEADS_DATA)} total")

            print("\n[DEMOS] Seeding Demos...")
            d = seed_demos(session, tenant, admin_user)
            print(f"  OK Demos: {d}")

            print("\n[CALLS] Seeding Calls...")
            cl = seed_calls(session, tenant, admin_user)
            print(f"  OK Calls: {cl}")

            print("\n[ENROLLMENTS] Seeding Enrollments & Students...")
            en, st = seed_enrollments_and_students(session, tenant, admin_user)
            print(f"  OK Enrollments: {en}, Students: {st}")

            print("\n[CHATBOT] Seeding Chatbot Sessions...")
            cb = seed_chatbot_sessions(session, tenant)
            print(f"  OK Chatbot Sessions: {cb}")

        print("\n" + "=" * 60)
        print("  ClaritAI MEGA seed complete!")
        print("  Total: 15 courses, 45 leads, 24 demos, 30 calls, 30 enrollments, 24 chatbot sessions")
        print("  Visit: http://localhost:3000/dashboard")
        print("  Login: admin@claritai.com / Admin@123")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\nERROR: Seed failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_seed()
