import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000'; // Android emulator → host

  static Map<String, String> _headers({String? token}) {
    final headers = {'Content-Type': 'application/json'};
    if (token != null) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  // === Auth ===
  static Future<Map<String, dynamic>> register(String username, String password) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/api/v1/users/register'),
      headers: _headers(),
      body: jsonEncode({'username': username, 'password': password}),
    );
    return _handleResponse(resp);
  }

  static Future<Map<String, dynamic>> login(String username, String password) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/api/v1/users/login'),
      headers: _headers(),
      body: jsonEncode({'username': username, 'password': password}),
    );
    return _handleResponse(resp);
  }

  // === Characters ===
  static Future<List<dynamic>> getCharacters() async {
    final token = await _getToken();
    final resp = await http.get(
      Uri.parse('$baseUrl/api/v1/characters'),
      headers: _headers(token: token),
    );
    final data = _handleResponse(resp);
    if (data is List) return data;
    return [];
  }

  // === Chat (SSE) ===
  static Future<http.StreamedResponse> chatStream({
    required String characterId,
    required String message,
    String? conversationId,
  }) async {
    final token = await _getToken();
    final body = {
      'character_id': characterId,
      'message': message,
    };
    if (conversationId != null) {
      body['conversation_id'] = conversationId;
    }
    final req = http.Request('POST', Uri.parse('$baseUrl/api/v1/chat'));
    req.headers.addAll(_headers(token: token));
    req.body = jsonEncode(body);
    return await req.send();
  }

  // === Conversations ===
  static Future<List<dynamic>> getConversations() async {
    final token = await _getToken();
    final resp = await http.get(
      Uri.parse('$baseUrl/api/v1/conversations'),
      headers: _headers(token: token),
    );
    final data = _handleResponse(resp);
    if (data is List) return data;
    return [];
  }

  static Future<Map<String, dynamic>> getConversationMessages(String id) async {
    final token = await _getToken();
    final resp = await http.get(
      Uri.parse('$baseUrl/api/v1/conversations/$id/messages'),
      headers: _headers(token: token),
    );
    return _handleResponse(resp);
  }

  // === Token Storage ===
  static Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', token);
  }

  static Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
  }

  static Future<bool> isLoggedIn() async {
    return await _getToken() != null;
  }

  static dynamic _handleResponse(http.Response resp) {
    final data = jsonDecode(resp.body);
    if (resp.statusCode >= 400) {
      throw ApiException(data['detail'] ?? '请求失败', resp.statusCode);
    }
    return data;
  }
}

class ApiException implements Exception {
  final String message;
  final int statusCode;
  ApiException(this.message, this.statusCode);
  @override
  String toString() => 'ApiException($statusCode): $message';
}
