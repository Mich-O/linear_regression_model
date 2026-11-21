# Linear Regression Project

**Overall mission · Healthcare GCGO** — My mission is to use my software engineering skills to turn African healthcare data into evidence that governments, NGOs, and researchers can use.<br>
**Problem** — I want to help decision-makers understand where the burden of care is greatest and where funding could improve services.<br>
**This project** — I’m starting in Nara, Mali, where I use admission data to estimate how long children who recover from acute malnutrition stay in the programme.<br>
**Connection** — This gives me a local view of follow-up needs in Nara. In future, data from other districts and discharge outcomes build a fuller picture of care needs and inform wider nutrition funding decisions.

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

4. Enter the sample values below and tap **Predict**. Expect about **39.5 days** with the saved model. Change age to **90** and tap **Predict** again to check that the app shows a readable validation error.

| Label in the Android app | Key in Swagger | Sample value |
| --- | --- | --- |
| Age (months) | `adm_age` | `18` |
| Weight (kg) | `adm_kg` | `7.2` |
| Height or length (cm) | `adm_cm` | `73` |
| Mid-upper arm circumference (mm) | `adm_muac` | `115` |
| Weight-for-height z-score (optional) | `adm_whz06` | Leave blank in the app. Use `null` in Swagger. |
| Weight-for-age z-score (optional) | `adm_waz06` | Leave blank in the app. Use `null` in Swagger. |
| Height-for-age z-score (optional) | `adm_haz06` | Leave blank in the app. Use `null` in Swagger. |
| Sex | `adm_sex` | `Female` |
| Oedema (0 = no, 1 = yes) | `adm_oedema_YN` | `0` |
| Referral source | `adm_referral` | `Family MUAC` |
| Admission category (optional) | `adm_category` | Leave blank to calculate it in the app. Use `2` in Swagger for these inputs. |

Enter just the values on the phone. In Swagger, enter the keys and values as a JSON object. The admission category is 1 when MUAC is below 115 mm or oedema is present, and 2 otherwise.

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

In the earlier coverage check, 566 of the 20,002 rows with all seven shared inputs and WHZ had a transfer flag. The final modeling cohort keeps 20,057 rows and imputes missing z-scores.

### Eleven admission inputs

The model uses the seven shared inputs, three growth z-scores, and the programme admission category. The notebook compares eight and eleven inputs on the same five training-side folds. It treats z-scores outside the WHO/UNICEF plausibility limits as missing and fits imputation only on training rows. Z-scores can be omitted on the phone or sent as `null` in Swagger. [WHO/UNICEF anthropometry guidance](https://data.unicef.org/wp-content/uploads/2019/05/Anthropometry-children-under-5-guidance-English_2019.pdf)

## Reproduce an API model update

Run the notebook through **Export rows for the retraining demo** to generate `summative/data/retraining_batch.csv`. The repository's `summative/API/training_rows.csv.gz` comes from the same Zenodo dataset and license. Both files contain only eleven admission inputs and the measured duration after the notebook filters and splits the source. The demo file contains reserved historical cases and is kept locally.

To rehearse locally, start the API from `summative/API` with `uv run --locked uvicorn prediction:app`. The prediction and retraining routes are accessible through Swagger.

In Swagger, upload the demo file once to `POST /retrain`. On a fresh service, the response should show **2,006 uploaded rows** and **16,045 training rows**. Repeat the exact same `/predict` request and compare the full decimals. The service refits LinearRegression on the combined data and uses the updated pipeline immediately. The service rejects a repeat of the same file during that session. A restart loads the original saved pipeline and training rows.
