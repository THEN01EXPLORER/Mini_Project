
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime

# Resume Data Profiles
PROFILES = [
    {
        "name": "Sarah Jenkins",
        "role": "Senior Python Developer",
        "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "AWS", "Docker", "Kubernetes", "Redis"],
        "exp": 8,
        "summary": "Expert Python developer with 8 years of experience building scalable backend systems.",
        "education": "BS in Computer Science, MIT",
        "rating": "high"  # High match
    },
    {
        "name": "Michael Chen",
        "role": "Full Stack Engineer",
        "skills": ["Python", "Flask", "React", "JavaScript", "Node.js", "MongoDB", "AWS"],
        "exp": 5,
        "summary": "Full stack engineer specializing in modern web applications and cloud architecture.",
        "education": "MS in Software Engineering, Stanford",
        "rating": "high"
    },
    {
        "name": "David Smith",
        "role": "Backend Developer",
        "skills": ["Python", "Django", "SQL", "Git", "Linux", "REST APIs"],
        "exp": 3,
        "summary": "Backend developer focused on API development and database optimization.",
        "education": "BS Computer Science, State University",
        "rating": "medium"
    },
    {
        "name": "Emily Davis",
        "role": "Data Scientist",
        "skills": ["Python", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "SQL"],
        "exp": 4,
        "summary": "Data scientist transitioning into software engineering. Strong Python skills.",
        "education": "PhD in Statistics",
        "rating": "medium"
    },
    {
        "name": "James Wilson",
        "role": "Junior Python Dev",
        "skills": ["Python", "HTML", "CSS", "Basic SQL", "Git"],
        "exp": 1,
        "summary": "Recent graduate passionate about Python development. Fast learner.",
        "education": "Bootcamp Graduate",
        "rating": "low"
    },
    {
        "name": "Robert Taylor",
        "role": "Java Developer",
        "skills": ["Java", "Spring Boot", "Hibernate", "Oracle", "Jenkins", "Maven"],
        "exp": 6,
        "summary": "Experienced Java developer willing to learn Python. Strong OOP background.",
        "education": "BS Computer Engineering",
        "rating": "low"
    },
    {
        "name": "Jennifer Lopez",
        "role": "Marketing Manager",
        "skills": ["SEO", "Content Marketing", "Google Analytics", "Social Media", "Excel"],
        "exp": 7,
        "summary": "Marketing professional with a track record of driving growth.",
        "education": "BA Marketing",
        "rating": "irrelevant"
    },
    {
        "name": "Alex Techie",
        "role": "DevOps Engineer",
        "skills": ["AWS", "Terraform", "Ansible", "Docker", "Python (Scripting)", "Bash"],
        "exp": 5,
        "summary": "DevOps engineer with strong automation skills and cloud experience.",
        "education": "BS Information Technology",
        "rating": "medium"
    },
    {
        "name": "Sam Coder",
        "role": "Software Architect",
        "skills": ["System Design", "Microservices", "Python", "Go", "Kubernetes", "High Availability"],
        "exp": 12,
        "summary": "Software Architect designing high-scale distributed systems.",
        "education": "MS Computer Science",
        "rating": "high"
    },
    {
        "name": "Lisa Web",
        "role": "Frontend Developer",
        "skills": ["React", "Vue", "CSS", "HTML", "JavaScript", "TypeScript"],
        "exp": 4,
        "summary": "Frontend specialist with an eye for design and UX.",
        "education": "BFA Design",
        "rating": "low"
    },
]

OUTPUT_DIR = "sample_resumes"

def create_resume_pdf(profile, filename):
    c = canvas.Canvas(filename, pagesize=LETTER)
    width, height = LETTER
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, profile["name"])
    
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.gray)
    c.drawString(50, height - 75, profile["role"])
    
    # Contact Info (Fake)
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(50, height - 95, f"Email: {profile['name'].lower().replace(' ', '.')}@example.com")
    c.drawString(250, height - 95, "Phone: (555) 123-4567")
    c.drawString(450, height - 95, "Location: San Francisco, CA")
    
    c.line(50, height - 105, width - 50, height - 105)
    
    # Summary
    y = height - 140
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Professional Summary")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y, profile["summary"])
    
    # Skills
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Technical Skills")
    y -= 20
    c.setFont("Helvetica", 12)
    skills_text = ", ".join(profile["skills"])
    c.drawString(50, y, skills_text)
    
    # Experience
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Experience")
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"{profile['role']} - Various Companies")
    c.setFont("Helvetica", 12)
    c.drawString(400, y, f"{2024-profile['exp']} - Present")
    y -= 20
    c.drawString(50, y, f"• Accumulated {profile['exp']} years of professional experience.")
    c.drawString(50, y-15, f"• Worked on challenging projects using {profile['skills'][0]} and {profile['skills'][1]}.")
    
    # Education
    y -= 60
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Education")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y, profile["education"])
    
    # Category tag (hidden visual cue)
    # c.setFont("Helvetica", 8)
    # c.setFillColor(colors.lightgrey)
    # c.drawString(50, 50, f"Profile Type: {profile['rating']}")
    
    c.save()
    print(f"Created: {filename}")

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"Generating {len(PROFILES)} sample resumes in '{OUTPUT_DIR}'...")
    
    for i, profile in enumerate(PROFILES, 1):
        # Create filename: 1_Sarah_Jenkins_Senior_Python.pdf
        safe_name = profile["name"].replace(" ", "_")
        safe_role = profile["role"].replace(" ", "_")
        filename = os.path.join(OUTPUT_DIR, f"{i:02d}_{safe_name}.pdf")
        
        create_resume_pdf(profile, filename)
        
    print("\nDone! Pass the folder path to the user.")
