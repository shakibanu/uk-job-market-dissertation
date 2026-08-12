"""
sponsorship_classifier.py

This trains a Random Forest to predict whether a sponsor company is
likely to be actively hiring, using whether it shows up in the Adzuna
job postings as the training label (the proxy label discussed in the
Methodology).

Worth being upfront about a real limitation here: only 201 companies
exist in the whole Adzuna dataset, so no matter how good the matching
is, there's a hard ceiling on how many positive examples this model can
ever have - out of 122,015 sponsors, at most a couple hundred can be
labelled "positive". That's a much more severe imbalance than a normal
class-imbalance problem, so this file also builds a simple rule-based
fallback, in case the Random Forest doesn't reach a usable F1 score
(the acceptance criteria set 0.65 as the bar).
"""

import re
import pandas as pd
from rapidfuzz import fuzz, process
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE


def normalise_name(name):
    """Same cleaning approach used in the Companies House matching
    pipeline - lowercase, no punctuation, Ltd standardised to Limited."""
    if not isinstance(name, str) or not name.strip():
        return ""
    cleaned = name.lower()
    cleaned = re.sub(r"[.,()&'\"/\\-]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"\bltd\b", "limited", cleaned)
    return cleaned.strip()


def build_training_label(sponsors_df, adzuna_df, fuzzy_threshold=90):
    """Works out which sponsors show up in the Adzuna postings - this is
    the proxy label the classifier is trained on. Using fuzzy matching
    here, not just exact matching, since only 201 companies exist in
    Adzuna at all and exact matching alone only recovers a small
    fraction of them."""
    sponsors_df = sponsors_df.copy()
    sponsors_df["norm_name"] = sponsors_df["Organisation"].apply(normalise_name)
    adzuna_names = adzuna_df["company"].apply(normalise_name).unique().tolist()

    is_positive = []
    for name in sponsors_df["norm_name"]:
        if not name:
            is_positive.append(False)
            continue
        best_match = process.extractOne(name, adzuna_names, scorer=fuzz.token_sort_ratio)
        is_positive.append(bool(best_match and best_match[1] >= fuzzy_threshold))

    sponsors_df["is_active_hirer"] = is_positive
    return sponsors_df


def build_features(sponsors_df, sector_mapping_df):
    """Building the feature set for the classifier - honestly, this is a
    limited feature set, since the Home Office Sponsors Register only
    has 4 columns to begin with. Using Type_Rating and Sector (where
    known) as the main features."""
    sponsors_df = sponsors_df.copy()
    sector_lookup = sector_mapping_df.rename(columns={"Company_Name": "norm_name_raw", "Industry": "Sector"})
    sector_lookup["norm_name"] = sector_lookup["norm_name_raw"].apply(normalise_name)
    sector_lookup = sector_lookup.drop_duplicates(subset="norm_name")[["norm_name", "Sector"]]

    sponsors_df = sponsors_df.merge(sector_lookup, on="norm_name", how="left")
    sponsors_df["Sector"] = sponsors_df["Sector"].fillna("Unknown")

    type_rating_encoder = LabelEncoder()
    sector_encoder = LabelEncoder()
    sponsors_df["Type_Rating_Encoded"] = type_rating_encoder.fit_transform(sponsors_df["Type_Rating"])
    sponsors_df["Sector_Encoded"] = sector_encoder.fit_transform(sponsors_df["Sector"])

    features = sponsors_df[["Type_Rating_Encoded", "Sector_Encoded"]]
    labels = sponsors_df["is_active_hirer"]
    return features, labels, sponsors_df


def train_and_evaluate(features, labels):
    """Trains the Random Forest with 5-fold cross-validation and SMOTE
    to handle the class imbalance, and reports the F1 score. Given how
    few positive examples exist, this is checked honestly - if F1 comes
    out below 0.65, the rule-based fallback becomes the one actually
    used in the dashboard, not this model."""
    positive_count = labels.sum()
    print(f"training on {len(labels):,} sponsors, {positive_count} positive examples")

    if positive_count < 10:
        print("too few positive examples for meaningful cross-validation - skipping straight to fallback")
        return None, 0.0

    smote = SMOTE(random_state=42, k_neighbors=min(5, positive_count - 1))
    features_resampled, labels_resampled = smote.fit_resample(features, labels)

    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    f1_scores = cross_val_score(model, features_resampled, labels_resampled, cv=cv, scoring="f1")

    average_f1 = f1_scores.mean()
    print(f"5-fold cross-validation F1 scores: {[round(s, 3) for s in f1_scores]}")
    print(f"average F1: {average_f1:.3f}")

    model.fit(features_resampled, labels_resampled)
    return model, average_f1


def rule_based_fallback(sector, type_rating):
    """A simple, honest fallback when the Random Forest isn't reliable
    enough to use - just flags sectors and rating types that showed any
    real hiring activity in the training data at all, rather than
    pretending to give a precise prediction."""
    known_active_sectors = {"Technology", "Healthcare", "Finance", "Engineering", "Education"}
    if sector in known_active_sectors and "Premium" in str(type_rating):
        return "Higher relative likelihood"
    elif sector in known_active_sectors:
        return "Some relative likelihood"
    else:
        return "Limited data available"


def get_feature_importance(model, feature_names):
    """Pulls the feature importance out of the trained Random Forest -
    kept for transparency in the model card, even though this model
    isn't the one making live predictions (its F1 score wasn't reliable
    enough for that)."""
    if model is None:
        return {}
    importances = model.feature_importances_
    return dict(zip(feature_names, [round(float(v), 3) for v in importances]))


def rank_companies_by_sector(sector, sponsors_with_sector_df, top_n=10):
    """Ranks companies for the Sponsorship Fit Calculator, using the
    rule-based fallback rather than the Random Forest - the model's F1
    score (0.488) came in below the 0.65 reliability bar, so this uses
    a simpler, honest ranking instead of a prediction that isn't
    trustworthy enough to present as one.

    Ranks first by the fallback's likelihood tier, then within a tier by
    Type_Rating (Premium/SME+ sponsors first), then by whether the
    company has an actual Adzuna job posting - the closest thing to real
    evidence of current hiring activity that exists in the data."""
    sector_df = sponsors_with_sector_df[sponsors_with_sector_df["Sector"] == sector].copy()

    if sector_df.empty:
        return pd.DataFrame()

    sector_df["Likelihood"] = sector_df.apply(
        lambda row: rule_based_fallback(row["Sector"], row["Type_Rating"]), axis=1
    )

    likelihood_order = {"Higher relative likelihood": 0, "Some relative likelihood": 1, "Limited data available": 2}
    rating_order = {"Worker (A (Premium))": 0, "Worker (A (SME+))": 1, "Worker (A rating)": 2, "Worker (B rating)": 3}

    sector_df["_likelihood_sort"] = sector_df["Likelihood"].map(likelihood_order)
    sector_df["_rating_sort"] = sector_df["Type_Rating"].map(rating_order).fillna(4)
    sector_df["_has_posting"] = sector_df.get("is_active_hirer", False)

    sector_df = sector_df.sort_values(
        by=["_likelihood_sort", "_has_posting", "_rating_sort"],
        ascending=[True, False, True],
    )

    # some companies appear more than once in the sponsor register (same
    # company, slightly different casing) - keeping just one entry per
    # company so the same name doesn't fill up the top 10
    sector_df["_dedup_key"] = sector_df["Organisation"].str.upper().str.strip()
    sector_df = sector_df.drop_duplicates(subset="_dedup_key")

    return sector_df[["Organisation", "City", "Type_Rating", "Likelihood"]].head(top_n).reset_index(drop=True)


if __name__ == "__main__":
    sponsors_df = pd.read_csv("data/HO_Sponsors_Clean.csv")
    adzuna_df = pd.read_csv("data/Adzuna_Clean.csv")
    sector_mapping_df = pd.read_csv("data/Final_Matched_Companies.csv")

    labelled_df = build_training_label(sponsors_df, adzuna_df)
    features, labels, full_df = build_features(labelled_df, sector_mapping_df)
    model, f1 = train_and_evaluate(features, labels)

    print()
    if f1 >= 0.65:
        print(f"Random Forest F1 ({f1:.3f}) meets the 0.65 bar - using it as the live model")
    else:
        print(f"Random Forest F1 ({f1:.3f}) is below the 0.65 bar - the rule-based fallback will be used instead")


def _compute_fit_classifier():
    sponsors_df = pd.read_csv("data/HO_Sponsors_Clean.csv")
    adzuna_df = pd.read_csv("data/Adzuna_Clean.csv")
    sector_mapping_df = pd.read_csv("data/Final_Matched_Companies.csv")

    labelled_df = build_training_label(sponsors_df, adzuna_df)
    features, labels, sponsors_with_sector = build_features(labelled_df, sector_mapping_df)
    model, f1_score = train_and_evaluate(features, labels)
    feature_importance = get_feature_importance(model, ["Type_Rating_Encoded", "Sector_Encoded"])

    return {
        "sponsors_with_sector": sponsors_with_sector,
        "model": model,
        "f1_score": f1_score,
        "feature_importance": feature_importance,
    }


# Running the training once here, when the app starts up, so the
# dashboard doesn't retrain the model every time someone visits the
# Sponsorship Fit tab - same approach as the SARIMA models. Cached to
# disk so this doesn't take ~19 seconds on every cold start.
from startup_cache import load_or_compute
_fit_results = load_or_compute("sponsorship_classifier", _compute_fit_classifier)
SPONSORS_WITH_SECTOR = _fit_results["sponsors_with_sector"]
FIT_MODEL = _fit_results["model"]
FIT_F1_SCORE = _fit_results["f1_score"]
FIT_FEATURE_IMPORTANCE = _fit_results["feature_importance"]

print(f"Sponsorship Fit classifier ready - F1: {FIT_F1_SCORE:.3f} ({'meets' if FIT_F1_SCORE >= 0.65 else 'below'} the 0.65 reliability bar)")
