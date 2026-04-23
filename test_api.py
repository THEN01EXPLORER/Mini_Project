"""Test the /screen endpoint with a PDF resume."""
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_test_pdf():
    """Create a simple PDF resume for testing."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Add resume content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "SARAH CHEN")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 730, "Senior Software Engineer")
    c.drawString(100, 715, "Email: sarah.chen@email.com | San Francisco, CA")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 685, "PROFESSIONAL SUMMARY")
    c.setFont("Helvetica", 10)
    c.drawString(100, 670, "Experienced software engineer with 6+ years of experience in Python,")
    c.drawString(100, 658, "JavaScript, and cloud technologies. Strong background in building")
    c.drawString(100, 646, "scalable web applications and microservices.")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 616, "TECHNICAL SKILLS")
    c.setFont("Helvetica", 10)
    c.drawString(100, 601, "Languages: Python, JavaScript, TypeScript, Go")
    c.drawString(100, 589, "Frameworks: FastAPI, Django, React, Node.js")
    c.drawString(100, 577, "Cloud: AWS (EC2, S3, Lambda), Docker, Kubernetes")
    c.drawString(100, 565, "Databases: PostgreSQL, MongoDB, Redis")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 535, "WORK EXPERIENCE")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100, 520, "Senior Software Engineer | Tech Corp Inc. | 2020 - Present")
    c.setFont("Helvetica", 10)
    c.drawString(110, 505, "- Led development of microservices architecture serving 1M+ users")
    c.drawString(110, 493, "- Implemented CI/CD pipelines reducing deployment time by 60%")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100, 468, "Software Engineer | StartupXYZ | 2018 - 2020")
    c.setFont("Helvetica", 10)
    c.drawString(110, 453, "- Built RESTful APIs using Python and FastAPI")
    c.drawString(110, 441, "- Developed React frontend for customer dashboard")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 411, "EDUCATION")
    c.setFont("Helvetica", 10)
    c.drawString(100, 396, "Bachelor of Science in Computer Science | UC Berkeley | 2018")
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

API_URL = "http://localhost:8001/api/v1/screen"

job_description = """
Job Title: Senior Backend Engineer

Requirements:
- 5+ years of experience with Python
- Experience with FastAPI or Django
- Strong knowledge of AWS and Docker
- Experience with PostgreSQL
- Good communication skills
"""

print("Creating test PDF resume...")
pdf_content = create_test_pdf()
print(f"PDF created ({len(pdf_content)} bytes)")

print("\nTesting /screen endpoint...")
try:
    files = {"file": ("resume.pdf", pdf_content, "application/pdf")}
    data = {"job_description": job_description}
    
    response = requests.post(API_URL, files=files, data=data, timeout=120)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n" + "="*50)
        print("✅ SUCCESS!")
        print("="*50)
        r = result.get('result', {})
        print(f"Similarity Score: {r.get('similarity_score', 'N/A'):.2%}")
        print(f"Fairness Score: {r.get('fairness_score', 'N/A')}")
        
        extracted = r.get('extracted_data', {})
        print(f"\nCandidate Name: {extracted.get('candidate_name', 'N/A')}")
        print(f"Experience: {extracted.get('total_experience_years', 'N/A')} years")
        print(f"Is Student: {extracted.get('is_student', 'N/A')}")
        
        skills = extracted.get('technical_skills', [])
        print(f"\nTechnical Skills Found ({len(skills)}):")
        for s in skills[:15]:
            print(f"  - {s}")
        
        print(f"\nMatch Analysis: {r.get('match_analysis', 'N/A')[:200]}...")
        print("="*50)
    else:
        print(f"\n❌ FAILED!")
        print(f"Response: {response.text[:2000]}")
        
except Exception as e:
    import traceback
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
