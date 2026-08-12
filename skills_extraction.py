"""
skills_extraction.py

This pulls out the most common skills mentioned in Adzuna job postings,
per sector. spaCy doesn't have a built-in "skill" category the way it
has "person" or "organisation", so this uses spaCy for the text
cleaning (lowercasing, lemmatising) and then matches against a curated
list of skills relevant to my 5 sectors - this is the normal way skill
extraction is done without training a custom model, which would be a
lot more work than this project needs.

Originally planned as "per sector per year", but the Adzuna data is a
one-time snapshot collection (see Methodology/Sprint 1), so almost all
of it falls in 2026 - only 42 rows are from 2025, spread across all 5
sectors. That's too little to break down by year as well as sector, so
this only splits by sector, where each one has a reasonable ~250
postings to work with.
"""

import re
import spacy
import pandas as pd
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

nlp = spacy.load("en_core_web_sm")

# A curated list of skills relevant to my 5 sectors, plus some general
# skills that show up across all of them. Not exhaustive, but broad
# enough to be a fair test of the approach.
SKILL_VOCABULARY = {
    "Technology": [
        "python", "java", "javascript", "sql", "aws", "azure", "docker",
        "kubernetes", "react", "machine learning", "data analysis",
        "cloud computing", "devops", "agile", "git", "linux", "c++",
        ".net", "api", "cybersecurity", "software development",
    ],
    "Healthcare": [
        "nursing", "patient care", "clinical", "nmc registration",
        "dbs check", "first aid", "care planning", "medication administration",
        "cpr", "healthcare assistant", "nhs", "safeguarding",
        "infection control", "compassion",
    ],
    "Finance": [
        "excel", "financial analysis", "accounting", "bookkeeping",
        "audit", "tax", "budgeting", "forecasting", "risk management",
        "compliance", "sap", "quickbooks", "financial modelling",
        "investment", "reconciliation",
    ],
    "Engineering": [
        "autocad", "solidworks", "project management", "cad",
        "mechanical engineering", "electrical engineering",
        "civil engineering", "manufacturing", "quality control",
        "six sigma", "cnc", "structural analysis", "matlab",
        "plumbing", "health and safety",
    ],
    "Education": [
        "teaching", "teacher", "lesson planning", "curriculum development",
        "classroom management", "sen", "safeguarding", "tutoring",
        "assessment", "pgce", "qts", "pastoral care",
    ],
    "General": [
        "communication", "leadership", "teamwork", "problem solving",
        "time management", "customer service", "organisational skills",
        "attention to detail", "microsoft office", "project management",
    ],
}

# flattening this into one list to search against, since a job posting
# in one sector might genuinely mention a skill listed under another
ALL_SKILLS = sorted(set(skill for skills in SKILL_VOCABULARY.values() for skill in skills))


def extract_skills_from_text(text):
    """Runs spaCy over one job description and returns which skills
    from the vocabulary actually appear in it. Using spaCy's lemmatiser
    so small variations (e.g. "managing" vs "manage") still match.

    Matching with word boundaries on both the raw and lemmatised text -
    without the word boundaries, short skill names like "sen" or "api"
    end up matching inside completely unrelated words ("sense",
    "essential", "presentation" all contain "sen"), which I caught by
    checking the actual output before trusting it."""
    if not isinstance(text, str):
        return []

    doc = nlp(text.lower())
    lemmatised_text = " ".join(token.lemma_ for token in doc)
    raw_text = text.lower()

    found_skills = []
    for skill in ALL_SKILLS:
        skill_pattern = rf"\b{re.escape(skill)}\b"
        if re.search(skill_pattern, raw_text) or re.search(skill_pattern, lemmatised_text):
            found_skills.append(skill)

    return found_skills


def get_top_skills_by_sector(adzuna_df, top_n=10):
    """Works out the top skills mentioned per sector, using how many job
    postings in that sector mention each skill."""
    results = {}
    for sector in adzuna_df["sector"].unique():
        sector_postings = adzuna_df[adzuna_df["sector"] == sector]
        skill_counter = Counter()
        for description in sector_postings["description"]:
            skills_found = extract_skills_from_text(description)
            skill_counter.update(set(skills_found))  # counting each skill once per posting, not once per mention

        top_skills = skill_counter.most_common(top_n)
        results[sector] = pd.DataFrame(top_skills, columns=["Skill", "Postings_Mentioning"])

    return results


def get_top_skills_tfidf(adzuna_df, top_n=10):
    """A fallback approach using TF-IDF instead of the curated
    vocabulary - picks out the words/phrases that are distinctively
    common in each sector's postings, rather than matching against a
    fixed list. Used if the vocabulary approach's precision comes out
    too low."""
    results = {}
    for sector in adzuna_df["sector"].unique():
        sector_postings = adzuna_df[adzuna_df["sector"] == sector]["description"].fillna("")

        vectoriser = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=200)
        tfidf_matrix = vectoriser.fit_transform(sector_postings)

        scores = tfidf_matrix.sum(axis=0).A1
        terms = vectoriser.get_feature_names_out()
        term_scores = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)[:top_n]

        results[sector] = pd.DataFrame(term_scores, columns=["Skill", "TFIDF_Score"])

    return results


# Running the extraction once here, when the app starts up, since this
# takes around 18 seconds over ~1,250 postings - same reasoning as the
# SARIMA models and the sponsorship classifier not being recomputed on
# every page visit. Cached to disk for the same cold-start reason.
from startup_cache import load_or_compute


def _compute_top_skills():
    adzuna_df = pd.read_csv("data/Adzuna_Clean.csv")
    return get_top_skills_by_sector(adzuna_df)


TOP_SKILLS_BY_SECTOR = load_or_compute("skills_by_sector", _compute_top_skills)
print(f"skills extraction ready for {len(TOP_SKILLS_BY_SECTOR)} sectors")
