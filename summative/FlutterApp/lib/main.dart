import 'package:flutter/material.dart';

import 'prediction_client.dart';

void main() => runApp(const NaraApp());

class NaraApp extends StatelessWidget {
  const NaraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Nara Nutrition Follow-up',
      theme: ThemeData(colorSchemeSeed: const Color(0xFF146B5A)),
      home: const PredictionPage(),
    );
  }
}

enum InputKind { wholeNumber, decimal, text }

const admissionFields = [
  (key: 'adm_age', label: 'Age (months)', kind: InputKind.wholeNumber),
  (key: 'adm_kg', label: 'Weight (kg)', kind: InputKind.decimal),
  (key: 'adm_cm', label: 'Height or length (cm)', kind: InputKind.decimal),
  (
    key: 'adm_muac',
    label: 'Mid-upper arm circumference (mm)',
    kind: InputKind.wholeNumber,
  ),
  (
    key: 'adm_whz06',
    label: 'Weight-for-height z-score (optional)',
    kind: InputKind.decimal,
  ),
  (
    key: 'adm_waz06',
    label: 'Weight-for-age z-score (optional)',
    kind: InputKind.decimal,
  ),
  (
    key: 'adm_haz06',
    label: 'Height-for-age z-score (optional)',
    kind: InputKind.decimal,
  ),
  (key: 'adm_sex', label: 'Sex', kind: InputKind.text),
  (
    key: 'adm_oedema_YN',
    label: 'Oedema (0 = no, 1 = yes)',
    kind: InputKind.wholeNumber,
  ),
  (key: 'adm_referral', label: 'Referral source', kind: InputKind.text),
  (
    key: 'adm_category',
    label: 'Admission category (optional)',
    kind: InputKind.wholeNumber,
  ),
];

class PredictionPage extends StatefulWidget {
  const PredictionPage({super.key});

  @override
  State<PredictionPage> createState() => _PredictionPageState();
}

class _PredictionPageState extends State<PredictionPage> {
  final _controllers = {
    for (final field in admissionFields) field.key: TextEditingController(),
  };
  String _message = 'Enter admission details to get an estimate.';
  bool _hasError = false;
  bool _isLoading = false;

  @override
  void dispose() {
    for (final controller in _controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Map<String, Object?> _readAdmission() {
    final admission = <String, Object?>{};
    for (final field in admissionFields) {
      final value = _controllers[field.key]!.text.trim();
      if (value.isEmpty) {
        if (field.key == 'adm_category') {
          // The earlier fields were parsed before the programme category.
          final muac = admission['adm_muac'] as int;
          final oedema = admission['adm_oedema_YN'] as int;
          admission[field.key] = muac < 115 || oedema == 1 ? 1 : 2;
          continue;
        }
        if (const {'adm_whz06', 'adm_waz06', 'adm_haz06'}.contains(field.key)) {
          admission[field.key] = null;
          continue;
        }
        throw FormatException('Enter ${field.label}.');
      }
      final parsed = switch (field.kind) {
        InputKind.wholeNumber => int.tryParse(value),
        InputKind.decimal => double.tryParse(value),
        InputKind.text => value,
      };
      if (parsed == null || (parsed is double && !parsed.isFinite)) {
        final expected = field.kind == InputKind.wholeNumber
            ? 'a whole number'
            : 'a number';
        throw FormatException('${field.label} must be $expected.');
      }
      admission[field.key] = parsed;
    }
    return admission;
  }

  Future<void> _predict() async {
    FocusScope.of(context).unfocus();
    setState(() {
      _isLoading = true;
      _hasError = false;
      _message = 'Getting an estimate…';
    });

    try {
      final days = await requestPrediction(_readAdmission());
      _showMessage(
        'Estimated time to recovered discharge: ${days.toStringAsFixed(1)} days.',
      );
    } on FormatException catch (error) {
      _showMessage(error.message, isError: true);
    } on PredictionRequestException catch (error) {
      final label = {
        for (final field in admissionFields) field.key: field.label,
      }[error.field];
      _showMessage(
        label == null ? error.message : '$label: ${error.message}',
        isError: true,
      );
    }
  }

  void _showMessage(String message, {bool isError = false}) {
    if (!mounted) return;
    setState(() {
      _isLoading = false;
      _hasError = isError;
      _message = message;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nara Nutrition Follow-up')),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                const Text('Estimate days to recovered discharge.'),
                const SizedBox(height: 16),
                for (final field in admissionFields)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: TextField(
                      controller: _controllers[field.key],
                      keyboardType: switch (field.kind) {
                        InputKind.wholeNumber => TextInputType.number,
                        InputKind.decimal =>
                          const TextInputType.numberWithOptions(
                            decimal: true,
                            signed: true,
                          ),
                        InputKind.text => TextInputType.text,
                      },
                      decoration: InputDecoration(
                        labelText: field.label,
                        helperText: switch (field.key) {
                          'adm_category' =>
                            'Leave blank to derive it from MUAC and oedema',
                          'adm_sex' => 'Female or Male',
                          'adm_referral' =>
                            'CHW - Relais, Family MUAC, Other, or Walk-in',
                          _ => null,
                        },
                        helperMaxLines: 2,
                        border: const OutlineInputBorder(),
                      ),
                    ),
                  ),
                FilledButton(
                  onPressed: _isLoading ? null : _predict,
                  child: const Text('Predict'),
                ),
                const SizedBox(height: 12),
                Semantics(
                  liveRegion: true,
                  child: Text(
                    _message,
                    style: TextStyle(
                      color: _hasError
                          ? Theme.of(context).colorScheme.error
                          : null,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
