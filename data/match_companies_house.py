"""
match_companies_house.py

This matches my Home Office Sponsors Register against the Companies House
bulk company data, to get a sector for each sponsor company. The Home
Office data never had a sector field at all, so this is the only way to
get one.

I'm reading the Companies House file in chunks instead of all at once,
because it's about 2GB and has 5 million rows - loading the whole thing
into memory at once would be slow and might not even fit.

Run this from the same folder as HO_Sponsors_Clean.csv and the
unzipped BasicCompanyDataAsOneFile-*.csv file.
"""

import pandas as pd

# This is the exact same SIC mapping table I built in Sprint 2 for the
# NOMIS/ASHE cleaning - reusing it here instead of building a new one
sic_mapping = {
    'Technology': [62, 63, 58, 61],
    'Healthcare': [86, 87, 88],
    'Finance': [64, 65, 66],
    'Engineering': [71, 72, 33, 28, 25],
    'Education': [85]
}

# flip the mapping around so I can look up "SIC code 62 -> Technology"
# instead of the other way round
sic_to_sector = {}
for sector, sic_codes in sic_mapping.items():
    for code in sic_codes:
        sic_to_sector[code] = sector

# loading my sponsors register and building a set of company names to
# match against - using a set instead of a list because checking
# membership in a set is much faster when I'm doing it 5 million times
sponsors_df = pd.read_csv("HO_Sponsors_Clean.csv")
sponsor_names = set(sponsors_df["Organisation"].str.upper().str.strip())
print(f"looking for matches against {len(sponsor_names):,} sponsor companies")

# this is the file I just downloaded from Companies House and unzipped -
# change the filename here if yours is named slightly differently
CH_FILENAME = "BasicCompanyDataAsOneFile-2026-07-01.csv"

matches = []
chunk_number = 0

# reading the huge file in chunks of 100,000 rows at a time, rather than
# loading all 5 million rows into memory at once
for chunk in pd.read_csv(CH_FILENAME, chunksize=100_000, low_memory=False):
    chunk_number += 1
    print(f"processing chunk {chunk_number}...")

    chunk["match_name"] = chunk["CompanyName"].str.upper().str.strip()
    chunk_matches = chunk[chunk["match_name"].isin(sponsor_names)]

    if not chunk_matches.empty:
        matches.append(chunk_matches[["CompanyName", "match_name", "SICCode.SicText_1"]])

# putting all the matched chunks together into one dataframe
matched_df = pd.concat(matches, ignore_index=True)
print(f"\nmatched {len(matched_df):,} companies out of {len(sponsor_names):,} sponsors")

# the SIC text looks like "62012 - Business and domestic software
# development" - I just need the first 2 digits to look up the sector
def get_sector(sic_text):
    if pd.isna(sic_text):
        return None
    sic_code_str = str(sic_text).strip()[:2]
    try:
        sic_code = int(sic_code_str)
    except ValueError:
        return None
    return sic_to_sector.get(sic_code)

matched_df["Sector"] = matched_df["SICCode.SicText_1"].apply(get_sector)

# some matched companies will have a SIC code that isn't in my 5 sectors
# at all (e.g. a restaurant, a construction firm) - those are genuine
# non-matches, not an error, so I'm dropping them here
matched_df = matched_df.dropna(subset=["Sector"])
print(f"of those, {len(matched_df):,} fall into one of my 5 sectors")
print(matched_df["Sector"].value_counts())

# saving just the company name and sector - this is what gets merged
# back into HO_Sponsors_Clean.csv next
output = matched_df[["match_name", "Sector"]].drop_duplicates(subset=["match_name"])
output.columns = ["Organisation_Match", "Sector"]
output.to_csv("Sponsors_Sector_Mapping.csv", index=False)
print("\nsaved Sponsors_Sector_Mapping.csv")
