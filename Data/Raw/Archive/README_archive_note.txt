ARCHIVE NOTE — data quality correction, [date of rebuild]

Master_Dataset_v1_INCORRECT_workforce_jobs_based.csv
This is the original Master_Dataset_v1.csv, archived here before rebuilding.
Its Vacancy_Count column was built from NOMIS_Vacancies_13Jun2026.xlsx, which
was confirmed (verification report, this conversation) to actually contain
"workforce jobs by industry (SIC 2007) - seasonally adjusted" - i.e. total
employment headcount, not open job vacancies. Example: Healthcare 2025-Q1
shows 5,065,645 in this file, versus 135,000 in the correct VACS02 source -
confirming this file measures a fundamentally different, much larger quantity
(people employed) rather than vacancies (open positions).

Kept for the dissertation's data-quality/audit trail, per instruction not to
delete anything.

IMPORTANT - action needed on your own machine:
I do not have the raw file NOMIS_Vacancies_13Jun2026.xlsx itself in my
sandbox (only its pasted contents and this already-built CSV). Please also
archive that raw file yourself, e.g.:
  Data/Raw/NOMIS_Vacancies_13Jun2026.xlsx
  -> Data/Raw/Archive/NOMIS_Vacancies_13Jun2026_INCORRECT_workforce_jobs.xlsx
so the raw source is preserved alongside this derived file.
