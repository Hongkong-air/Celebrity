import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';

/// 豆包语音 TTS 服务
/// 使用火山引擎 TTS API（豆包语音）将文本转为语音
///
/// 使用前需要配置：
/// 1. 在火山引擎控制台开通 TTS 服务
/// 2. 获取 Access Key ID 和 Access Key Secret
/// 3. 创建 TTS 应用获取 App ID
class DoubaoTtsService {
  static const String _defaultApiUrl =
      'https://openspeech.bytedance.com/api/v1/tts';

  final String _appId;
  final String _accessToken;
  final String _cluster;
  final String _apiUrl;

  // 语音参数
  String _voiceType = 'BV001_streaming'; // 默认音色：通用女声
  double _speed = 1.0;                   // 语速 0.5~2.0
  double _volume = 1.0;                  // 音量 0.5~2.0
  double _pitch = 1.0;                   // 音调 0.5~2.0

  // 音频格式
  String _audioFormat = 'mp3'; // mp3, wav, pcm

  // HTTP 客户端
  final http.Client _httpClient;

  // 缓存已生成的音频
  final Map<String, Uint8List> _audioCache = {};

  /// 创建豆包 TTS 服务实例
  ///
  /// [appId] - 火山引擎 TTS 应用 ID
  /// [accessToken] - 访问令牌（Access Token）
  /// [cluster] - 集群标识，默认 'volcano_tts'
  /// [apiUrl] - API 地址，默认使用火山引擎官方地址
  DoubaoTtsService({
    required String appId,
    required String accessToken,
    String cluster = 'volcano_tts',
    String? apiUrl,
    http.Client? httpClient,
  })  : _appId = appId,
        _accessToken = accessToken,
        _cluster = cluster,
        _apiUrl = apiUrl ?? _defaultApiUrl,
        _httpClient = httpClient ?? http.Client();

  /// 音色类型
  ///
  /// 常用音色：
  /// - BV001_streaming: 通用女声（默认）
  /// - BV002_streaming: 通用男声
  /// - BV003_streaming: 知性女声
  /// - BV004_streaming: 沉稳男声
  /// - BV700_streaming: 热情女声
  /// - BV710_streaming: 温柔男声
  /// - BV401_streaming: 古风女声（适合古代人物）
  /// - BV402_streaming: 古风男声（适合古代人物）
  set voiceType(String value) => _voiceType = value;
  String get voiceType => _voiceType;

  /// 语速 (0.5 ~ 2.0, 默认 1.0)
  set speed(double value) => _speed = value.clamp(0.5, 2.0);
  double get speed => _speed;

  /// 音量 (0.5 ~ 2.0, 默认 1.0)
  set volume(double value) => _volume = value.clamp(0.5, 2.0);
  double get volume => _volume;

  /// 音调 (0.5 ~ 2.0, 默认 1.0)
  set pitch(double value) => _pitch = value.clamp(0.5, 2.0);
  double get pitch => _pitch;

  /// 音频格式 (mp3, wav, pcm)
  set audioFormat(String value) => _audioFormat = value;
  String get audioFormat => _audioFormat;

  /// 文本转语音 - 返回音频字节数据
  ///
  /// [text] 要转换的文本
  /// [useCache] 是否使用缓存（默认 true）
  Future<Uint8List> textToSpeech(String text, {bool useCache = true}) async {
    // 检查缓存
    final cacheKey = '${_voiceType}_$_speed_$_pitch_${text.hashCode}';
    if (useCache && _audioCache.containsKey(cacheKey)) {
      debugPrint('[DoubaoTTS] 命中缓存: ${text.substring(0, min(20, text.length))}...');
      return _audioCache[cacheKey]!;
    }

    try {
      // 分段处理长文本（豆包 TTS 单次最大约 1024 字符）
      if (text.length > 1024) {
        return await _synthesizeLongText(text, cacheKey);
      }

      final audioData = await _callTtsApi(text);
      _audioCache[cacheKey] = audioData;
      return audioData;
    } catch (e) {
      debugPrint('[DoubaoTTS] TTS 合成失败: $e');
      rethrow;
    }
  }

  /// 流式文本转语音 - 逐句合成并回调
  ///
  /// 适用于实时对话场景：AI 回复逐句到达时立即播放
  /// [text] 完整文本
  /// [onAudioChunk] 每句音频的回调
  /// [onComplete] 全部完成时的回调
  Future<void> streamTextToSpeech({
    required String text,
    required void Function(Uint8List audioData, int sentenceIndex) onAudioChunk,
    void Function()? onComplete,
  }) async {
    // 按标点符号分句
    final sentences = _splitSentences(text);
    debugPrint('[DoubaoTTS] 流式合成: 共 ${sentences.length} 句');

    for (int i = 0; i < sentences.length; i++) {
      if (sentences[i].trim().isEmpty) continue;
      try {
        final audioData = await textToSpeech(sentences[i].trim());
        onAudioChunk(audioData, i);
      } catch (e) {
        debugPrint('[DoubaoTTS] 第 $i 句合成失败: $e');
      }
    }

    onComplete?.call();
  }

  /// 调用豆包 TTS API
  Future<Uint8List> _callTtsApi(String text) async {
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer;$_accessToken',
    };

    final body = jsonEncode({
      'app': {
        'appid': _appId,
        'cluster': _cluster,
      },
      'user': {
        'uid': 'sages_app_user',
      },
      'audio': {
        'voice_type': _voiceType,
        'encoding': _audioFormat,
        'speed_ratio': _speed,
        'volume_ratio': _volume,
        'pitch_ratio': _pitch,
      },
      'request': {
        'reqid': '${DateTime.now().millisecondsSinceEpoch}',
        'text': text,
        'text_type': 'plain',
        'operation': 'query',
        'with_frontend': 1,
        'frontend_type': 'unitTTS',
      },
    });

    debugPrint('[DoubaoTTS] 请求 TTS: ${text.substring(0, min(50, text.length))}...');

    final response = await _httpClient.post(
      Uri.parse(_apiUrl),
      headers: headers,
      body: body,
    );

    if (response.statusCode == 200) {
      final contentType = response.headers['content-type'] ?? '';
      if (contentType.contains('audio') || contentType.contains('octet-stream')) {
        // 直接返回音频二进制数据
        return response.bodyBytes;
      } else {
        // JSON 响应，解析 base64 音频
        final json = jsonDecode(utf8.decode(response.bodyBytes));
        if (json['code'] == 3000) {
          // 成功
          final audioBase64 = json['data'];
          return base64Decode(audioBase64);
        } else {
          throw DoubaoTtsException(
            code: json['code'] ?? -1,
            message: json['message'] ?? 'TTS 合成失败',
          );
        }
      }
    } else {
      throw DoubaoTtsException(
        code: response.statusCode,
        message: 'HTTP ${response.statusCode}: ${response.reasonPhrase}',
      );
    }
  }

  /// 合成长文本（分段合成后拼接）
  Future<Uint8List> _synthesizeLongText(String text, String cacheKey) async {
    final chunks = <String>[];
    final chunkSize = 900; // 留出余量

    // 按标点分段
    String current = '';
    for (int i = 0; i < text.length; i++) {
      current += text[i];
      if (current.length >= chunkSize) {
        // 找最近的标点断句
        final lastPunct = current.lastIndexOf(RegExp(r'[。！？，；、\n]'));
        if (lastPunct > chunkSize ~/ 2) {
          chunks.add(current.substring(0, lastPunct + 1));
          current = current.substring(lastPunct + 1);
        } else {
          chunks.add(current);
          current = '';
        }
      }
    }
    if (current.isNotEmpty) {
      chunks.add(current);
    }

    debugPrint('[DoubaoTTS] 长文本分段: ${chunks.length} 段');

    // 逐段合成
    final audioChunks = <Uint8List>[];
    for (final chunk in chunks) {
      final audio = await _callTtsApi(chunk);
      audioChunks.add(audio);
    }

    // 简单拼接（MP3 格式可以直接拼接）
    final totalLength = audioChunks.fold<int>(0, (sum, c) => sum + c.length);
    final result = Uint8List(totalLength);
    int offset = 0;
    for (final chunk in audioChunks) {
      result.setRange(offset, offset + chunk.length, chunk);
      offset += chunk.length;
    }

    _audioCache[cacheKey] = result;
    return result;
  }

  /// 按标点分句
  List<String> _splitSentences(String text) {
    final sentences = <String>[];
    final buffer = StringBuffer();

    for (int i = 0; i < text.length; i++) {
      buffer.write(text[i]);
      final char = text[i];
      // 中英文标点分句
      if (char == '。' || char == '！' || char == '？' ||
          char == '.' || char == '!' || char == '?' ||
          char == '\n') {
        sentences.add(buffer.toString());
        buffer.clear();
      }
      // 逗号也分句（短句），但保持更自然的节奏
      else if (char == '，' || char == '；' || char == ',' || char == ';') {
        if (buffer.length > 10) {
          sentences.add(buffer.toString());
          buffer.clear();
        }
      }
    }

    if (buffer.isNotEmpty) {
      sentences.add(buffer.toString());
    }

    return sentences;
  }

  /// 清除缓存
  void clearCache() {
    _audioCache.clear();
    debugPrint('[DoubaoTTS] 缓存已清除');
  }

  /// 释放资源
  void dispose() {
    _audioCache.clear();
    _httpClient.close();
  }
}

/// 豆包 TTS 异常
class DoubaoTtsException implements Exception {
  final int code;
  final String message;

  const DoubaoTtsException({required this.code, required this.message});

  @override
  String toString() => 'DoubaoTtsException(code: $code, message: $message)';
}

/// 预设音色配置
///
/// 根据人物角色选择合适的音色
class VoicePresets {
  /// 古代人物音色映射
  static const Map<String, String> ancientCharacterVoices = {
    '孔子': 'BV402_streaming', // 古风男声 - 沉稳
    '李白': 'BV402_streaming', // 古风男声 - 潇洒
    '老子': 'BV004_streaming', // 沉稳男声 - 深沉
    '庄子': 'BV402_streaming', // 古风男声 - 逍遥
    '孟子': 'BV402_streaming', // 古风男声 - 正气
    '苏轼': 'BV402_streaming', // 古风男声 - 豪放
    '李清照': 'BV401_streaming', // 古风女声 - 婉约
    '王维': 'BV402_streaming', // 古风男声 - 禅意
  };

  /// 获取人物对应的音色
  static String getVoiceForCharacter(String characterName) {
    return ancientCharacterVoices[characterName] ?? 'BV001_streaming';
  }

  /// 通用音色列表
  static const Map<String, String> generalVoices = {
    '通用女声': 'BV001_streaming',
    '通用男声': 'BV002_streaming',
    '知性女声': 'BV003_streaming',
    '沉稳男声': 'BV004_streaming',
    '热情女声': 'BV700_streaming',
    '温柔男声': 'BV710_streaming',
    '古风女声': 'BV401_streaming',
    '古风男声': 'BV402_streaming',
  };
}

/// TTS 播放状态管理
class TtsPlaybackController extends ChangeNotifier {
  final DoubaoTtsService _ttsService;

  bool _isPlaying = false;
  String? _currentText;
  int _currentSentenceIndex = 0;
  int _totalSentences = 0;
  String? _errorMessage;

  bool get isPlaying => _isPlaying;
  String? get currentText => _currentText;
  int get currentSentenceIndex => _currentSentenceIndex;
  int get totalSentences => _totalSentences;
  String? get errorMessage => _errorMessage;

  TtsPlaybackController(this._ttsService);

  /// 播放文本
  Future<void> speak(String text) async {
    if (_isPlaying) {
      await stop();
    }

    _isPlaying = true;
    _currentText = text;
    _errorMessage = null;
    notifyListeners();

    try {
      await _ttsService.streamTextToSpeech(
        text: text,
        onAudioChunk: (audioData, index) {
          _currentSentenceIndex = index;
          notifyListeners();
          // TODO: 将 audioData 传给音频播放器播放
          // 例如: await _audioPlayer.play(BytesSource(audioData));
        },
        onComplete: () {
          _isPlaying = false;
          _currentSentenceIndex = 0;
          notifyListeners();
        },
      );
    } catch (e) {
      _isPlaying = false;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  /// 停止播放
  Future<void> stop() async {
    _isPlaying = false;
    _currentText = null;
    _currentSentenceIndex = 0;
    _totalSentences = 0;
    notifyListeners();
  }

  /// 设置音色
  void setVoice(String voiceType) {
    _ttsService.voiceType = voiceType;
  }

  /// 设置语速
  void setSpeed(double speed) {
    _ttsService.speed = speed;
  }
}
