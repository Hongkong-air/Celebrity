import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

/// 豆包 TTS 服务
/// 使用火山引擎 TTS API 将文本转为语音
class DoubaoTTS {
  // TODO: 替换为你的火山引擎凭证
  static const String _appId = 'YOUR_APP_ID';
  static const String _accessToken = 'YOUR_ACCESS_TOKEN';
  static const String _cluster = 'volcano_tts';

  /// 语音合成 - 返回 PCM 音频数据
  ///
  /// [text] 要合成的文本
  /// [voiceType] 音色类型，如 "zh_female_qingxin", "zh_male_chunhou"
  /// [speed] 语速 0.5~2.0，默认 1.0
  /// [volume] 音量 0.5~2.0，默认 1.0
  static Future<Uint8List> synthesize({
    required String text,
    String voiceType = 'BV700_V2_streaming',  // 豆包默认音色
    double speed = 1.0,
    double volume = 1.0,
  }) async {
    final url = Uri.parse(
      'https://openspeech.bytedance.com/api/v1/tts',
    );

    final body = jsonEncode({
      'app': {
        'appid': _appId,
        'token': 'access_token',
        'cluster': _cluster,
      },
      'user': {
        'uid': 'sages_user',
      },
      'audio': {
        'voice_type': voiceType,
        'encoding': 'mp3',
        'speed_ratio': speed,
        'volume_ratio': volume,
        'pitch_ratio': 1.0,
      },
      'request': {
        'reqid': DateTime.now().millisecondsSinceEpoch.toString(),
        'text': text,
        'text_type': 'plain',
        'operation': 'query',
        'with_header': false,
        'sequence_number': 1,
      },
    });

    final response = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer;$_accessToken',
      },
      body: body,
    );

    if (response.statusCode == 200) {
      // 返回音频二进制数据
      return response.bodyBytes;
    } else {
      throw Exception('TTS 合成失败: ${response.statusCode} ${response.body}');
    }
  }

  /// 流式语音合成 - 返回音频块流
  ///
  /// 适用于长文本，边合成边播放
  static Stream<Uint8List> synthesizeStream({
    required String text,
    String voiceType = 'BV700_V2_streaming',
    double speed = 1.0,
  }) async* {
    // 将长文本按句号分段
    final sentences = _splitSentences(text);
    for (final sentence in sentences) {
      if (sentence.trim().isEmpty) continue;
      final audio = await synthesize(
        text: sentence,
        voiceType: voiceType,
        speed: speed,
      );
      yield audio;
    }
  }

  /// 按标点符号分段
  static List<String> _splitSentences(String text) {
    final buffer = StringBuffer();
    final sentences = <String>[];
    for (final char in text.runes) {
      buffer.write(String.fromCharCode(char));
      if ('。！？；\n'.contains(String.fromCharCode(char))) {
        sentences.add(buffer.toString());
        buffer.clear();
      }
    }
    if (buffer.isNotEmpty) {
      sentences.add(buffer.toString());
    }
    return sentences;
  }

  /// 预设音色列表
  static const Map<String, String> voicePresets = {
    '孔子': 'BV700_V2_streaming',       // 沉稳男声
    '李白': 'BV001_V2_streaming',       // 潇洒男声
    '默认女声': 'BV002_V2_streaming',
    '默认男声': 'BV700_V2_streaming',
    '温柔女声': 'BV003_V2_streaming',
    '磁性男声': 'BV004_V2_streaming',
  };

  /// 根据人物名获取推荐音色
  static String getVoiceForCharacter(String characterName) {
    return voicePresets[characterName] ?? voicePresets['孔子']!;
  }
}
