"""
WANDATA ATS Engine - Advanced Resume Scoring System
Pure Python implementation, no external API required
"""
import re
import string
import math
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ─── Keyword Banks ──────────────────────────────────────────────────────────

ACTION_VERBS = [
    'achieved', 'accelerated', 'accomplished', 'acquired', 'administered', 'advanced',
    'analyzed', 'architected', 'automated', 'boosted', 'built', 'championed',
    'coached', 'collaborated', 'consolidated', 'coordinated', 'created', 'cultivated',
    'decreased', 'delivered', 'demonstrated', 'deployed', 'designed', 'developed',
    'directed', 'drove', 'enhanced', 'established', 'executed', 'expanded',
    'facilitated', 'forged', 'generated', 'guided', 'headed', 'identified',
    'implemented', 'improved', 'increased', 'initiated', 'innovated', 'integrated',
    'launched', 'led', 'leveraged', 'managed', 'mentored', 'modernized',
    'negotiated', 'optimized', 'orchestrated', 'oversaw', 'pioneered', 'planned',
    'produced', 'reduced', 'reorganized', 'resolved', 'revamped', 'scaled',
    'shaped', 'simplified', 'spearheaded', 'streamlined', 'strengthened', 'structured',
    'supervised', 'supported', 'trained', 'transformed', 'transitioned', 'unified'
]

SOFT_SKILLS = [
    'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking',
    'adaptability', 'creativity', 'time management', 'collaboration', 'analytical',
    'detail oriented', 'strategic', 'innovation', 'decision making', 'multitasking',
    'self motivated', 'proactive', 'organized', 'flexible', 'interpersonal'
]

TECH_SKILLS = [
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'swift',
    'kotlin', 'php', 'ruby', 'scala', 'r', 'matlab',
    'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring', 'laravel',
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
    'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'terraform',
    'git', 'jenkins', 'ci/cd', 'devops', 'linux', 'bash', 'rest', 'graphql',
    'machine learning', 'deep learning', 'nlp', 'tensorflow', 'pytorch', 'keras',
    'data analysis', 'data science', 'tableau', 'power bi', 'excel', 'spark',
    'html', 'css', 'api', 'microservices', 'agile', 'scrum', 'jira', 'figma'
]

SECTION_PATTERNS = {
    'summary':        r'\b(summary|objective|profile|about me|professional summary|career objective|overview)\b',
    'experience':     r'\b(experience|work experience|employment|career history|work history|professional experience)\b',
    'education':      r'\b(education|academic|qualification|degree|university|college|schooling)\b',
    'skills':         r'\b(skills|technical skills|core competencies|competencies|expertise|technologies|tools & technologies)\b',
    'projects':       r'\b(projects|personal projects|key projects|portfolio|notable projects)\b',
    'certifications': r'\b(certifications?|certificates?|certified|credentials?|licenses?|accreditation)\b',
    'awards':         r'\b(awards?|honors?|achievements?|recognition|accomplishments?)\b',
    'languages':      r'\b(languages?|spoken languages?|language proficiency)\b',
    'publications':   r'\b(publications?|research|papers?|articles?|journals?)\b',
    'volunteer':      r'\b(volunteer|volunteering|community service|social work)\b',
}

CONTACT_PATTERNS = {
    'email':    r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b',
    'phone':    r'(\+?\d[\d\s\-().]{7,}\d)',
    'linkedin': r'linkedin\.com/in/[\w\-]+',
    'github':   r'github\.com/[\w\-]+',
    'website':  r'(https?://|www\.)[^\s]+',
}

DEGREE_KEYWORDS = [
    'bachelor', 'master', 'phd', 'doctorate', 'associate', 'b.sc', 'b.tech',
    'm.sc', 'm.tech', 'mba', 'b.e', 'm.e', 'b.s', 'm.s', 'b.a', 'm.a',
    'diploma', 'certificate', 'engineering', 'science', 'arts', 'commerce',
    'bca', 'mca', 'bba', 'b.com', 'm.com'
]

# ─── Text Extraction ─────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path):
    """Extract text from PDF using pdfplumber"""
    import pdfplumber
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX"""
    from docx import Document
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return text

def extract_text(file_path, filename):
    """Route to correct extractor based on file extension"""
    ext = filename.lower().rsplit('.', 1)[-1]
    if ext == 'pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['doc', 'docx']:
        return extract_text_from_docx(file_path)
    elif ext == 'txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file format: .{ext}")

# ─── Helpers ─────────────────────────────────────────────────────────────────

def clean_text(text):
    return text.lower().strip()

def word_count(text):
    return len(text.split())

def find_numbers_percentages(text):
    """Find quantifiable achievements"""
    patterns = [
        r'\b\d+%',               # percentages
        r'\$[\d,]+',             # dollar amounts
        r'\b\d[\d,]*\s*(users|customers|employees|members|people|projects|clients)',
        r'\b\d+\s*(years?|months?|weeks?)',
        r'increased by \d+',
        r'reduced by \d+',
        r'\b[0-9]{4}\b',        # years
    ]
    matches = []
    for p in patterns:
        matches.extend(re.findall(p, text, re.IGNORECASE))
    return len(matches)

# ─── Scoring Components ───────────────────────────────────────────────────────

def score_contact_info(text):
    """Score: 0-100 (max 10 pts in final) for contact completeness"""
    found = {}
    for key, pattern in CONTACT_PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        found[key] = bool(match)
    
    # Weights
    weights = {'email': 40, 'phone': 30, 'linkedin': 20, 'github': 5, 'website': 5}
    score = sum(weights[k] for k, v in found.items() if v)
    
    missing = [k for k, v in found.items() if not v and k in ['email', 'phone', 'linkedin']]
    tips = []
    if not found['email']:   tips.append("Add your email address")
    if not found['phone']:   tips.append("Add your phone number")
    if not found['linkedin']: tips.append("Add your LinkedIn profile URL")
    if not found['github']:  tips.append("Add GitHub profile (for tech roles)")
    
    return {'score': min(score, 100), 'found': found, 'missing': missing, 'tips': tips}

def score_sections(text):
    """Score: 0-100 (max 25 pts in final) for section completeness"""
    found_sections = {}
    for section, pattern in SECTION_PATTERNS.items():
        found_sections[section] = bool(re.search(pattern, text, re.IGNORECASE))
    
    # Priority sections
    critical   = ['experience', 'education', 'skills']
    important  = ['summary', 'projects', 'certifications']
    bonus      = ['awards', 'languages', 'publications', 'volunteer']
    
    crit_score  = sum(30 for s in critical  if found_sections.get(s, False))  # max 90
    imp_score   = sum(5  for s in important if found_sections.get(s, False))  # max 15
    bon_score   = sum(1  for s in bonus     if found_sections.get(s, False))  # max 4
    raw = min(crit_score + imp_score + bon_score, 100)
    
    missing = [s for s in critical + important if not found_sections.get(s, False)]
    tips = []
    for s in critical:
        if not found_sections[s]:
            tips.append(f"Add a '{s.title()}' section — it is critical for ATS")
    for s in important:
        if not found_sections[s]:
            tips.append(f"Consider adding a '{s.title()}' section")
    
    return {'score': raw, 'found': found_sections, 'missing': missing, 'tips': tips}

def score_action_verbs(text):
    """Score: 0-100 (max 15 pts in final) for strong action verbs"""
    lower = clean_text(text)
    found = [v for v in ACTION_VERBS if re.search(r'\b' + v + r'\b', lower)]
    unique_count = len(set(found))
    
    # 15+ unique verbs = full score
    raw = min(unique_count / 15 * 100, 100)
    
    tips = []
    if unique_count < 5:
        tips.append("Use strong action verbs (led, built, achieved, optimized, etc.)")
    elif unique_count < 10:
        tips.append("Add more varied action verbs to describe your impact")
    
    return {'score': raw, 'count': unique_count, 'found': found[:10], 'tips': tips}

def score_quantifiable(text):
    """Score: 0-100 (max 15 pts in final) for numbers and measurable impact"""
    count = find_numbers_percentages(text)
    raw = min(count / 10 * 100, 100)
    
    tips = []
    if count < 3:
        tips.append("Add quantifiable results (e.g., 'Increased revenue by 30%', 'Managed team of 10')")
    elif count < 6:
        tips.append("Add more specific metrics to demonstrate impact")
    
    return {'score': raw, 'count': count, 'tips': tips}

def score_keywords(text):
    """Score: 0-100 (max 15 pts in final) for professional keywords"""
    lower = clean_text(text)
    tech_found = [k for k in TECH_SKILLS  if re.search(r'\b' + re.escape(k) + r'\b', lower)]
    soft_found = [k for k in SOFT_SKILLS  if re.search(r'\b' + re.escape(k) + r'\b', lower)]
    
    tech_score = min(len(tech_found) / 8 * 70, 70)
    soft_score = min(len(soft_found) / 4 * 30, 30)
    raw = min(tech_score + soft_score, 100)
    
    tips = []
    if len(tech_found) < 3:
        tips.append("Include relevant technical skills and tools")
    if len(soft_found) < 2:
        tips.append("Mention soft skills like leadership, communication, collaboration")
    
    return {
        'score': raw,
        'tech_skills': tech_found[:15],
        'soft_skills': soft_found[:8],
        'tips': tips
    }

def score_length_format(text):
    """Score: 0-100 (max 10 pts in final) for appropriate length"""
    words = word_count(text)
    
    # Ideal: 400-800 words (1-2 pages)
    if 400 <= words <= 800:
        raw = 100
        msg = f"Ideal length ({words} words) — perfect for 1-2 pages"
    elif words < 200:
        raw = 40
        msg = f"Too short ({words} words) — expand with more details"
    elif 200 <= words < 400:
        raw = 75
        msg = f"Slightly short ({words} words) — consider adding more detail"
    elif 800 < words <= 1200:
        raw = 85
        msg = f"Slightly long ({words} words) — consider condensing"
    else:
        raw = 55
        msg = f"Too long ({words} words) — keep resume to 1-2 pages"
    
    tips = [msg] if raw < 100 else []
    return {'score': raw, 'word_count': words, 'message': msg, 'tips': tips}

def score_education(text):
    """Score: 0-100 (max 10 pts in final) for education section quality"""
    lower = clean_text(text)
    degree_found = any(re.search(r'\b' + re.escape(d) + r'\b', lower) for d in DEGREE_KEYWORDS)
    year_found   = bool(re.search(r'\b(19|20)\d{2}\b', text))
    gpa_found    = bool(re.search(r'\b(gpa|cgpa|grade|percentage)\b', lower))
    
    raw = 0
    if degree_found: raw += 60
    if year_found:   raw += 25
    if gpa_found:    raw += 15
    
    tips = []
    if not degree_found: tips.append("Include your degree name and field of study")
    if not year_found:   tips.append("Add graduation year to your education")
    if not gpa_found:    tips.append("Consider adding GPA/CGPA if above average")
    
    return {'score': raw, 'has_degree': degree_found, 'has_year': year_found, 'tips': tips}

def score_ats_formatting(text):
    """Score: 0-100 (max 5 pts in final) for ATS-friendly formatting"""
    issues = []
    # Check for special chars that mess up ATS
    special_ratio = sum(1 for c in text if ord(c) > 127) / max(len(text), 1)
    
    if special_ratio > 0.05:
        issues.append("High number of special characters may confuse ATS")
    
    # Check for very short lines (possible table formatting)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    avg_len = sum(len(l) for l in lines) / max(len(lines), 1)
    if avg_len < 20 and len(lines) > 20:
        issues.append("Possible table/column layout detected — ATS may misread")
    
    raw = max(100 - len(issues) * 40, 20)
    return {'score': raw, 'issues': issues, 'tips': issues}

# ─── General ATS Score ────────────────────────────────────────────────────────

def calculate_general_ats_score(text):
    """Full general ATS analysis, no job description"""
    
    components = {
        'contact':      score_contact_info(text),
        'sections':     score_sections(text),
        'action_verbs': score_action_verbs(text),
        'quantifiable': score_quantifiable(text),
        'keywords':     score_keywords(text),
        'length':       score_length_format(text),
        'education':    score_education(text),
        'formatting':   score_ats_formatting(text),
    }
    
    # Weighted final score
    weights = {
        'contact':      0.10,
        'sections':     0.25,
        'action_verbs': 0.15,
        'quantifiable': 0.15,
        'keywords':     0.15,
        'length':       0.10,
        'education':    0.05,
        'formatting':   0.05,
    }
    
    final_score = sum(components[k]['score'] * weights[k] for k in weights)
    final_score = round(final_score)
    
    # Collect all tips
    all_tips = []
    for comp in components.values():
        all_tips.extend(comp.get('tips', []))
    
    # Grade
    if final_score >= 85:   grade, verdict = 'A', 'Excellent'
    elif final_score >= 70: grade, verdict = 'B', 'Good'
    elif final_score >= 55: grade, verdict = 'C', 'Average'
    elif final_score >= 40: grade, verdict = 'D', 'Needs Work'
    else:                   grade, verdict = 'F', 'Poor'
    
    return {
        'score': final_score,
        'grade': grade,
        'verdict': verdict,
        'components': {
            'Contact Info':           {'score': round(components['contact']['score']),      'weight': '10%', 'details': components['contact']},
            'Resume Sections':        {'score': round(components['sections']['score']),     'weight': '25%', 'details': components['sections']},
            'Action Verbs':           {'score': round(components['action_verbs']['score']), 'weight': '15%', 'details': components['action_verbs']},
            'Quantifiable Impact':    {'score': round(components['quantifiable']['score']), 'weight': '15%', 'details': components['quantifiable']},
            'Keyword Optimization':   {'score': round(components['keywords']['score']),     'weight': '15%', 'details': components['keywords']},
            'Length & Readability':   {'score': round(components['length']['score']),       'weight': '10%', 'details': components['length']},
            'Education Details':      {'score': round(components['education']['score']),    'weight': '5%',  'details': components['education']},
            'ATS Formatting':         {'score': round(components['formatting']['score']),   'weight': '5%',  'details': components['formatting']},
        },
        'tips': all_tips[:10],
        'word_count': word_count(text),
        'tech_skills': components['keywords']['tech_skills'],
        'soft_skills': components['keywords']['soft_skills'],
        'action_verbs_found': components['action_verbs']['found'],
        'sections_found': [k for k, v in components['sections']['found'].items() if v],
    }

# ─── Job-Specific ATS Score ──────────────────────────────────────────────────

def extract_keywords_from_text(text, top_n=30):
    """Extract top keywords using TF-IDF on single doc (against itself)"""
    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=top_n,
            min_df=1
        )
        # For single doc, use character-level trick
        sentences = [s.strip() for s in re.split(r'[.\n]+', text) if len(s.strip()) > 10]
        if len(sentences) < 2:
            sentences = [text]
        
        matrix = vectorizer.fit_transform(sentences)
        scores = matrix.sum(axis=0).A1
        vocab = vectorizer.get_feature_names_out()
        
        pairs = sorted(zip(vocab, scores), key=lambda x: -x[1])
        return [w for w, _ in pairs[:top_n] if len(w) > 2]
    except:
        # Fallback: simple frequency
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        stop = set(['the','and','for','with','that','this','are','you','your',
                    'have','has','will','from','they','been','also','more',
                    'our','their','its','was','were','but','not','use','can',
                    'work','about','which','when','all','who','than','into'])
        filtered = [w for w in words if w not in stop]
        freq = Counter(filtered)
        return [w for w, _ in freq.most_common(top_n)]

def cosine_sim(text1, text2):
    """Compute cosine similarity between two texts"""
    try:
        vec = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
        matrix = vec.fit_transform([text1, text2])
        sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return float(sim)
    except:
        return 0.0

def calculate_job_ats_score(resume_text, job_title, job_description):
    """ATS analysis against a specific job description"""
    
    # ── 1. Keyword Match ──
    jd_keywords = extract_keywords_from_text(job_description, 40)
    resume_lower = clean_text(resume_text)
    jd_lower     = clean_text(job_description)
    
    matched_keywords = []
    missing_keywords = []
    for kw in jd_keywords:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, resume_lower):
            matched_keywords.append(kw)
        else:
            missing_keywords.append(kw)
    
    keyword_match_ratio = len(matched_keywords) / max(len(jd_keywords), 1)
    keyword_score = min(keyword_match_ratio * 100, 100)
    
    # ── 2. TF-IDF Similarity ──
    similarity = cosine_sim(resume_lower, jd_lower)
    similarity_score = min(similarity * 200, 100)  # boost since resumes rarely hit >0.5
    
    # ── 3. Skill Match ──
    jd_tech = [k for k in TECH_SKILLS if re.search(r'\b' + re.escape(k) + r'\b', jd_lower)]
    resume_tech = [k for k in TECH_SKILLS if re.search(r'\b' + re.escape(k) + r'\b', resume_lower)]
    
    matched_skills = list(set(jd_tech) & set(resume_tech))
    missing_skills  = list(set(jd_tech) - set(resume_tech))
    
    skill_score = (len(matched_skills) / max(len(jd_tech), 1)) * 100 if jd_tech else 60
    skill_score = min(skill_score, 100)
    
    # ── 4. Job Title Match ──
    title_words = re.findall(r'\b\w{3,}\b', job_title.lower())
    title_match = sum(1 for w in title_words if re.search(r'\b' + w + r'\b', resume_lower))
    title_score = min((title_match / max(len(title_words), 1)) * 100, 100)
    
    # ── 5. General ATS ──
    general = calculate_general_ats_score(resume_text)
    general_score = general['score']
    
    # ── Weighted Final ──
    weights = {
        'keyword_match':   0.30,
        'tfidf_similarity':0.20,
        'skill_match':     0.25,
        'title_match':     0.10,
        'general_ats':     0.15,
    }
    
    scores = {
        'keyword_match':    keyword_score,
        'tfidf_similarity': similarity_score,
        'skill_match':      skill_score,
        'title_match':      title_score,
        'general_ats':      general_score,
    }
    
    final_score = sum(scores[k] * weights[k] for k in weights)
    final_score = round(final_score)
    
    # Grade
    if final_score >= 85:   grade, verdict = 'A', 'Excellent Match'
    elif final_score >= 70: grade, verdict = 'B', 'Good Match'
    elif final_score >= 55: grade, verdict = 'C', 'Average Match'
    elif final_score >= 40: grade, verdict = 'D', 'Weak Match'
    else:                   grade, verdict = 'F', 'Poor Match'
    
    # Tips
    tips = []
    if missing_skills[:5]:
        tips.append(f"Add these missing skills: {', '.join(missing_skills[:5])}")
    if missing_keywords[:5]:
        tips.append(f"Use these JD keywords in your resume: {', '.join(missing_keywords[:5])}")
    if title_score < 50:
        tips.append(f"Mirror the job title '{job_title}' more explicitly in your summary")
    if keyword_match_ratio < 0.5:
        tips.append("Only half the job description keywords are in your resume — tailor it more")
    if similarity_score < 40:
        tips.append("Your resume language doesn't closely match the job description — rephrase key sections")
    
    tips.extend(general.get('tips', [])[:3])
    
    return {
        'score': final_score,
        'grade': grade,
        'verdict': verdict,
        'job_title': job_title,
        'components': {
            'Keyword Match':       {'score': round(keyword_score),    'weight': '30%'},
            'Content Similarity':  {'score': round(similarity_score), 'weight': '20%'},
            'Skills Alignment':    {'score': round(skill_score),      'weight': '25%'},
            'Job Title Relevance': {'score': round(title_score),      'weight': '10%'},
            'General ATS Score':   {'score': round(general_score),    'weight': '15%'},
        },
        'matched_keywords': matched_keywords[:20],
        'missing_keywords': missing_keywords[:15],
        'matched_skills': matched_skills,
        'missing_skills': missing_skills[:10],
        'jd_keywords': jd_keywords[:20],
        'similarity': round(similarity * 100, 1),
        'keyword_match_pct': round(keyword_match_ratio * 100, 1),
        'tips': tips[:8],
        'general_analysis': general,
    }
