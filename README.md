# Linear Regression Project

Our mission is to help district nutrition coordinators in Nara, Mali plan outpatient follow-up capacity. The prototype estimates elapsed days from admission to discharge as recovered using information available at admission. Full caseload planning also accounts for other outcomes.

## Dataset

The Nara acute malnutrition treatment cohort contains 27,800 records with admission measurements and treatment outcomes. This project studies recovered health-centre cases. The duration is recorded in whole days and modeled as a quantitative elapsed duration.

Data by Suvi T. Kangas, Bethany Marron, Zachary Tausanovitch, Elizabeth Radin, Josiane Andrianarisoa, Salimou Dembele, Césaire Ouedraogo, Issa Niamanto Coulibaly, Marie Biotteau, Bareye Ouologuem, Soumaila Daou, Fatoumata Traoré, Issiaka Traoré, Marc Nene, and Jeanette Bailey. [Zenodo dataset](https://doi.org/10.5281/zenodo.7343363) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [Companion study](https://doi.org/10.3390/nu14224923)

## Swagger UI

Pending Render deployment.

## YouTube demo

Pending recording and upload.

## Run the mobile app

Instructions will be added with the Flutter app and public API.

## Reproduce the cohort audit

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Download `Mali_Cohort_Study.csv` from Zenodo and place it in `summative/data/`. Git ignores that directory.
3. From a terminal at the repository root, run:

   ```sh
   cd summative
   uv run --locked python audit_cohort.py data/Mali_Cohort_Study.csv
   ```

   You can also pass the path to your existing CSV. In WSL, quote a Windows download path such as `"/mnt/c/Users/yourname/Downloads/Mali_Cohort_Study.csv"`.

The audit verifies the published MD5 and prints aggregate counts. It reads the original data without writing a transformed CSV.

The original has 27,800 rows, 58 columns, and 27,800 unique anonymous IDs. The audit selects `adm_site = Health Center`, `cured = 1`, and positive `recovered_los`. It treats blanks, periods, and `NA` as missing for coverage checks, with no imputation. All 20,484 recovered health-centre records have positive whole-day durations, ranging from 10 to 112 days. The CSV lacks an admission date for a time-based split.

Height is missing in 427 of 20,484 recovered health-centre cases and 4,108 of 4,201 recovered ASC cases. Replacing the constant site field with `adm_whz06` reduces complete rows from 20,057 to 20,002. Height and z-score are the only candidate fields with missing values, at 427 and 482 respectively. Oedema is recorded in 18 cases. The smallest referral group, Other, has 608.

Of the 20,484 eligible records, 590 have an inpatient transfer flag. Of the 20,002 complete rows, 566 have that flag, leaving 19,436 if transfers are excluded. The audit keeps transfers visible while the cohort definition is provisional. For modeling, compare the same rows and splits with and without z-score. Confirm that coordinators can provide it at admission before making it a required input. Review transfers against the outpatient planning use case before freezing the cohort.
