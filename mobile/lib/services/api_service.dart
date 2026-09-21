import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Thin REST client for the PARAKH FastAPI backend. The mobile app NEVER
/// talks to PostgreSQL directly - every operation goes through this HTTP
/// layer, matching the documented API surface exactly.
class ApiService {
  ApiService({String? baseUrl}) : baseUrl = baseUrl ?? _defaultBaseUrl();

  final String baseUrl;
  final _storage = const FlutterSecureStorage();
  static const _tokenKey = 'parakh_jwt_token';

  static String _defaultBaseUrl() {
    // Android emulator maps host loopback to 10.0.2.2; iOS simulator/physical
    // devices should point this at the real backend host in production.
    if (Platform.isAndroid) return 'http://10.0.2.2:8000';
    return 'http://localhost:8000';
  }

  Future<void> _saveToken(String token) => _storage.write(key: _tokenKey, value: token);
  Future<String?> getToken() => _storage.read(key: _tokenKey);
  Future<void> clearToken() => _storage.delete(key: _tokenKey);

  Future<Map<String, String>> _authHeaders({bool json = true}) async {
    final token = await getToken();
    return {
      if (json) 'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  dynamic _decode(http.Response res) {
    if (res.statusCode == 401) {
      clearToken();
      throw ApiException('Session expired. Please log in again.', 401);
    }
    final body = res.body.isNotEmpty ? jsonDecode(res.body) : null;
    if (res.statusCode < 200 || res.statusCode >= 300) {
      final detail = (body is Map && body['detail'] != null) ? body['detail'] : 'Request failed (${res.statusCode})';
      throw ApiException(detail.toString(), res.statusCode);
    }
    return body;
  }

  // ---------------- Auth ----------------

  Future<Map<String, dynamic>> login(String officerId, String password) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'officer_id': officerId, 'password': password}),
    );
    final data = _decode(res);
    await _saveToken(data['access_token']);
    return data;
  }

  Future<Map<String, dynamic>> me() async {
    final res = await http.get(Uri.parse('$baseUrl/api/auth/me'), headers: await _authHeaders());
    return _decode(res);
  }

  // ---------------- Dashboard ----------------

  Future<Map<String, dynamic>> dashboardStats() async {
    final res = await http.get(Uri.parse('$baseUrl/api/dashboard/stats'), headers: await _authHeaders());
    return _decode(res);
  }

  // ---------------- Inspections ----------------

  Future<List<dynamic>> listInspections({Map<String, String>? query}) async {
    final uri = Uri.parse('$baseUrl/api/inspections').replace(queryParameters: query);
    final res = await http.get(uri, headers: await _authHeaders());
    return _decode(res);
  }

  Future<Map<String, dynamic>> getInspection(int id) async {
    final res = await http.get(Uri.parse('$baseUrl/api/inspections/$id'), headers: await _authHeaders());
    return _decode(res);
  }

  Future<Map<String, dynamic>> createInspection(Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/inspections'),
      headers: await _authHeaders(),
      body: jsonEncode(payload),
    );
    return _decode(res);
  }

  Future<void> uploadImages(int inspectionId, List<StagedImage> images) async {
    final uri = Uri.parse('$baseUrl/api/inspections/$inspectionId/images');
    final request = http.MultipartRequest('POST', uri);
    final token = await getToken();
    if (token != null) request.headers['Authorization'] = 'Bearer $token';
    for (final img in images) {
      request.files.add(await http.MultipartFile.fromPath('files', img.filePath));
      // `categories` must appear once per file, in the same order as `files`.
      // http.MultipartRequest.fields is a Map (one value per key), so a
      // repeated field has to be added as a file-less MultipartFile part.
      request.files.add(http.MultipartFile.fromString('categories', img.category));
    }
    final streamed = await request.send();
    final res = await http.Response.fromStream(streamed);
    _decode(res);
  }

  Future<Map<String, dynamic>> analyzeInspection(int id) async {
    final res = await http.post(Uri.parse('$baseUrl/api/inspections/$id/analyze'), headers: await _authHeaders());
    return _decode(res);
  }

  Future<Map<String, dynamic>> getResults(int id) async {
    final res = await http.get(Uri.parse('$baseUrl/api/inspections/$id/results'), headers: await _authHeaders());
    return _decode(res);
  }

  Future<List<dynamic>> getFindings(int id) async {
    final res = await http.get(Uri.parse('$baseUrl/api/inspections/$id/findings'), headers: await _authHeaders());
    return _decode(res);
  }

  Future<List<dynamic>> getEvidence(int id) async {
    final res = await http.get(Uri.parse('$baseUrl/api/inspections/$id/evidence'), headers: await _authHeaders());
    return _decode(res);
  }

  // ---------------- Findings / Verification ----------------

  Future<Map<String, dynamic>> verifyFinding(int findingId, Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/findings/$findingId/verify'),
      headers: await _authHeaders(),
      body: jsonEncode(payload),
    );
    return _decode(res);
  }

  // ---------------- Reports ----------------

  Future<Map<String, dynamic>> generateReport(int inspectionId) async {
    final res = await http.post(Uri.parse('$baseUrl/api/reports/$inspectionId/generate'), headers: await _authHeaders());
    return _decode(res);
  }

  String downloadReportUrl(int reportId) => '$baseUrl/api/reports/$reportId/download';

  String resolveImageUrl(String originalPath) {
    const marker = 'uploads/';
    final idx = originalPath.indexOf(marker);
    final rel = idx >= 0 ? originalPath.substring(idx + marker.length) : originalPath;
    return '$baseUrl/uploads/$rel';
  }

  // ---------------- Demo mode ----------------

  Future<Map<String, dynamic>> demoCases() async {
    final res = await http.get(Uri.parse('$baseUrl/api/demo/cases'), headers: await _authHeaders());
    return _decode(res);
  }

  Future<Map<String, dynamic>> runDemoCase(String key) async {
    final res = await http.post(Uri.parse('$baseUrl/api/demo/$key/run'), headers: await _authHeaders());
    return _decode(res);
  }
}

class ApiException implements Exception {
  ApiException(this.message, this.statusCode);
  final String message;
  final int statusCode;
  @override
  String toString() => message;
}

class StagedImage {
  StagedImage({required this.filePath, required this.category});
  final String filePath;
  final String category; // FRONT / BACK / SIDE / TOP / BOTTOM / OTHER
}
