import 'dart:async';
import 'dart:convert';
import 'dart:io';

final _endpoint = Uri.parse('https://nara-follow-up-api.onrender.com/predict');
const _deadline = Duration(seconds: 60);

class PredictionRequestException implements Exception {
  const PredictionRequestException(this.message, {this.field});

  final String message;
  final String? field;
}

Future<double> requestPrediction(Map<String, Object?> admission) async {
  final client = HttpClient()..connectionTimeout = _deadline;
  try {
    final request = await client.postUrl(_endpoint);
    request.headers.contentType = ContentType.json;
    request.write(jsonEncode(admission));
    final response = await request.close().timeout(_deadline);
    final body = await utf8.decoder.bind(response).join().timeout(_deadline);

    if (response.statusCode == 422) {
      final decoded = jsonDecode(body);
      final issues = decoded is Map ? decoded['detail'] : null;
      if (issues is List && issues.isNotEmpty && issues.first is Map) {
        final issue = issues.first as Map;
        final location = issue['loc'];
        final field = location is List && location.isNotEmpty
            ? location.last
            : null;
        throw PredictionRequestException(
          issue['msg']?.toString() ?? 'Check the value and try again.',
          field: field is String ? field : null,
        );
      }
      throw const PredictionRequestException('Check the values and try again.');
    }
    if (response.statusCode != 200) {
      throw const PredictionRequestException(
        'The prediction service is unavailable. Try again.',
      );
    }

    final decoded = jsonDecode(body);
    final days = decoded is Map ? decoded['predicted_days'] : null;
    if (days is! num || !days.isFinite) {
      throw const FormatException('Invalid prediction response');
    }
    return days.toDouble();
  } on TimeoutException {
    throw const PredictionRequestException(
      'The service took too long to respond. Try again.',
    );
  } on IOException {
    throw const PredictionRequestException(
      'Could not reach the service. Check your connection and try again.',
    );
  } on FormatException {
    throw const PredictionRequestException(
      'The service returned an unreadable response. Try again.',
    );
  } finally {
    client.close(force: true);
  }
}
