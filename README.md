# Linear Regression Project

Our mission is to help district nutrition coordinators in Nara, Mali plan outpatient follow-up capacity. The prototype estimates elapsed days from admission to discharge as recovered using information available at admission. Full caseload planning also accounts for other outcomes.

## Dataset

The Nara acute malnutrition treatment cohort contains 27,800 records with admission measurements and treatment outcomes. This project studies recovered health-centre cases. The duration is recorded in whole days and modeled as a quantitative elapsed duration.

Data by Suvi T. Kangas, Bethany Marron, Zachary Tausanovitch, Elizabeth Radin, Josiane Andrianarisoa, Salimou Dembele, Césaire Ouedraogo, Issa Niamanto Coulibaly, Marie Biotteau, Bareye Ouologuem, Soumaila Daou, Fatoumata Traoré, Issiaka Traoré, Marc Nene, and Jeanette Bailey. [Zenodo dataset](https://doi.org/10.5281/zenodo.7343363) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [Companion study](https://doi.org/10.3390/nu14224923)

## Swagger UI

[Open the public Swagger UI](https://nara-follow-up-api.onrender.com/docs) to try prediction and CSV retraining.

## YouTube demo

Pending recording and upload.

## Run the mobile app

1. Install Flutter and the Android toolchain. Run `flutter doctor` to check the Android setup.
2. Enable USB debugging on the phone, connect it, and accept the debugging prompt.
3. From the repository root, open a terminal on the same system as your Flutter and Android SDKs. On Windows, build from a Windows folder. If your checkout is inside WSL, copy `summative/FlutterApp` to a Windows folder and run the Flutter commands there.

   ```sh
   cd summative/FlutterApp
   flutter pub get
   flutter devices
   flutter run -d <device-id>
   ```

   In a standalone copy, start inside `FlutterApp` and skip the first command. Replace `<device-id>` with the ID printed for your Android phone.

4. Enter the sample values below and tap **Predict**. Expect about **40.9 days** with the original model. Change age to **90** and tap **Predict** again to check that the app shows a readable validation error.

| Label in the Android app | Key in Swagger | Sample value |
| --- | --- | --- |
| Age (months) | `adm_age` | `18` |
| Weight (kg) | `adm_kg` | `7.2` |
| Height or length (cm) | `adm_cm` | `73` |
| Mid-upper arm circumference (mm) | `adm_muac` | `115` |
| Weight-for-height z-score (optional) | `adm_whz06` | Leave blank in the app. Use `null` in Swagger. |
| Sex | `adm_sex` | `Female` |
| Oedema (0 = no, 1 = yes) | `adm_oedema_YN` | `0` |
| Referral source | `adm_referral` | `Family MUAC` |

Enter just the values on the phone. In Swagger, enter the keys and values as a JSON object. Verified on a physical Android 12 phone with a valid prediction and an out-of-range age.

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

### Inpatient transfers

The study followed cases that transferred to inpatient care until programme discharge. Median recorded duration was 70 days for the 590 recovered health-centre cases with a transfer and 35 days for the 19,894 without one. Both groups belong in the primary cohort because the estimate covers elapsed time through recovered discharge. Keep the transfer flag out of the inputs because it is recorded during treatment. Report errors by transfer status as a sensitivity check. Elapsed days alone cannot tell the coordinator how many outpatient visits to staff. [Companion study, section 2.6](https://www.mdpi.com/2072-6643/14/22/4923)

Of the 20,002 complete rows, 566 had a transfer flag, leaving 19,436 in the subgroup without transfers.

### Weight-for-height z-score

Compare models with and without z-score on the same rows and splits. Confirm that coordinators can provide it at admission before making it a required input.
