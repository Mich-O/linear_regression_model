# Linear Regression Project

**Overall mission · Healthcare GCGO** — My mission is to use my software engineering skills to turn African healthcare data into evidence that governments, NGOs, and researchers can use.<br>
**Problem** — I want to help decision-makers understand where the burden of care is greatest and where funding could improve services.<br>
**This project** — I’m starting in Nara, Mali, where I use admission data to estimate how long children who recover from acute malnutrition stay in the programme.<br>
**Connection** — This gives me a local view of follow-up needs in Nara. In future, data from other districts and discharge outcomes build a fuller picture of care needs and inform wider nutrition funding decisions.

## Dataset

The Nara acute malnutrition treatment cohort contains 27,800 records from Mali. It pairs admission measurements with treatment outcomes. This project uses health-centre records for children discharged as recovered and estimates elapsed days from admission to that discharge.

Data by Suvi T. Kangas, Bethany Marron, Zachary Tausanovitch, Elizabeth Radin, Josiane Andrianarisoa, Salimou Dembele, Césaire Ouedraogo, Issa Niamanto Coulibaly, Marie Biotteau, Bareye Ouologuem, Soumaila Daou, Fatoumata Traoré, Issiaka Traoré, Marc Nene, and Jeanette Bailey. [Zenodo dataset](https://doi.org/10.5281/zenodo.7343363) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [Companion study](https://doi.org/10.3390/nu14224923)

## Swagger UI

[Open the public Swagger UI](https://nara-follow-up-api.onrender.com/docs) to try `POST /predict` or upload a labelled CSV to `POST /retrain`.

## YouTube demo

[Watch the project demo on YouTube](https://youtu.be/wAlAog4zdKU)

## Run the mobile app

1. Install the Flutter SDK and Android tooling. The project requires Dart 3.13.5 or later within the 3.x series. Use `flutter --version` to check your Dart version and `flutter doctor -v` to check the Android toolchain. If Android licenses are pending, run `flutter doctor --android-licenses`. [Flutter Android setup](https://docs.flutter.dev/platform-integration/android/setup)
2. Start an Android emulator or connect a phone.

   - **Emulator.** Open **Device Manager** in Android Studio. Create a virtual device if needed, then start it and wait for Android to boot.
   - **Phone.** Enable USB debugging, connect and unlock the phone, and accept the debugging prompt. If the phone does not appear, check that the cable supports data.

   Run `flutter devices` and copy the ID listed for your Android device or emulator.
3. Get the app source. If you already have the repository on the same system as your Flutter and Android SDKs, open a terminal in `summative/FlutterApp`. With Windows SDKs and a WSL checkout, copy `summative/FlutterApp` to a Windows folder and open PowerShell in that copy, or clone the repository directly into a Windows folder.

   To get a fresh copy, run:

   ```sh
   git clone https://github.com/Mich-O/linear_regression_model.git
   cd linear_regression_model/summative/FlutterApp
   ```

4. From the Flutter app directory, which contains `pubspec.yaml`, run the commands below. Replace `DEVICE_ID` with the Android device or emulator ID from step 2.

   ```sh
   flutter pub get
   flutter run -d DEVICE_ID
   ```

5. Enter the admission details and tap **Predict**. The app calls the hosted API and needs an internet connection.

### Enter admission details

| App field | Swagger key | Format |
| --- | --- | --- |
| Age | `adm_age` | Whole months |
| Weight | `adm_kg` | Kilograms |
| Height or length | `adm_cm` | Centimetres |
| Mid-upper arm circumference (MUAC) | `adm_muac` | Whole millimetres |
| Weight-for-height z-score | `adm_whz06` | Number if known |
| Weight-for-age z-score | `adm_waz06` | Number if known |
| Height-for-age z-score | `adm_haz06` | Number if known |
| Sex | `adm_sex` | `Female` or `Male` |
| Oedema | `adm_oedema_YN` | `0` for no or `1` for yes |
| Referral source | `adm_referral` | `CHW - Relais`, `Family MUAC`, `Other`, or `Walk-in` |
| Admission category | `adm_category` | `1` if MUAC is below 115 mm or oedema is present, otherwise `2` |

Leave unavailable z-scores blank in the app and send `null` for them in Swagger. The app calculates the admission category if you leave it blank. Include it explicitly in Swagger.

## Reproduce the notebook

1. Install uv. Download `Mali_Cohort_Study.csv` from the dataset link above and place it in `summative/data/`, creating the folder if needed. [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)
2. From the repository root, set up the locked Python environment and verify the downloaded CSV:

   ```sh
   cd summative
   uv sync --locked
   uv run --locked python audit_cohort.py data/Mali_Cohort_Study.csv
   ```

3. Open [multivariate.ipynb](summative/linear_regression/multivariate.ipynb) in VS Code with the Python and Jupyter extensions. Select the Python kernel from `summative/.venv` and run the notebook from top to bottom.

The notebook documents cohort selection, missing-value handling, and model evaluation. Its final cells export the fitted pipeline, the original training rows, and a separate labelled CSV for trying retraining. The exports come from the same Zenodo data and license. Git ignores the original dataset and the separate retraining CSV.

## Run the API locally

From the repository root, start the API with the included model and training data:

```sh
cd summative/API
uv run --locked uvicorn prediction:app
```

Open [local Swagger](http://127.0.0.1:8000/docs). To try a model update, run the notebook through its last cell, then upload `summative/data/retraining_batch.csv` to `POST /retrain`. The update lasts for the current server session. Restarting the server reloads the original model.
