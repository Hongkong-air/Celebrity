import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../services/api_service.dart';
import '../../services/doubao_tts_service.dart';
import '../../widgets/digital_human.dart';
import '../../theme/app_theme.dart';

class ChatScreen extends StatefulWidget {
  final String characterId;
  final String characterName;
  final String characterSlug;

  const ChatScreen({
    super.key,
    required this.characterId,
    required this.characterName,
    required this.characterSlug,
  });

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
  final List<_ChatMessage> _messages = [];
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  final _digitalHumanController = DigitalHumanController();
  final _focusNode = FocusNode();

  bool _isSending = false;
  String? _conversationId;
  bool _isTTSPlaying = false;

  // 豆包 TTS 服务
  DoubaoTtsService? _ttsService;
  TtsPlaybackController? _ttsPlaybackController;

  @override
  void initState() {
    super.initState();
    _initTtsService();
    _addWelcomeMessage();
  }

  /// 初始化豆包 TTS 服务
  void _initTtsService() {
    // 从环境变量或配置读取
    // 实际项目中应从安全存储读取
    const appId = String.fromEnvironment('DOUBAO_TTS_APP_ID');
    const accessToken = String.fromEnvironment('DOUBAO_TTS_ACCESS_TOKEN');

    if (appId.isNotEmpty && accessToken.isNotEmpty) {
      _ttsService = DoubaoTtsService(
        appId: appId,
        accessToken: accessToken,
      );
      // 根据人物选择音色
      _ttsService!.voiceType = VoicePresets.getVoiceForCharacter(widget.characterName);
      _ttsPlaybackController = TtsPlaybackController(_ttsService!);
    }
  }

  void _addWelcomeMessage() {
    setState(() {
      _messages.add(_ChatMessage(
        role: 'assistant',
        content: _getWelcomeText(),
        isStreaming: false,
      ));
    });
  }

  String _getWelcomeText() {
    switch (widget.characterSlug) {
      case 'confucius':
        return '有朋自远方来，不亦乐乎。吾乃孔丘，字仲尼。汝有何疑惑，尽可道来，吾当为汝解惑。';
      case 'libai':
        return '哈哈哈！吾乃李太白，青莲居士。今日有缘相见，当浮一大白！汝有何话想说？';
      default:
        return '你好，我是${widget.characterName}。有什么想问我的吗？';
    }
  }

  Future<void> _sendMessage() async {
    final text = _inputController.text.trim();
    if (text.isEmpty || _isSending) return;

    _inputController.clear();
    _focusNode.unfocus();

    setState(() {
      _messages.add(_ChatMessage(role: 'user', content: text));
      _isSending = true;
    });

    _digitalHumanController.startThinking();
    _scrollToBottom();

    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token');
      final request = http.Request(
        'POST',
        Uri.parse('${ApiService.baseUrl}/api/v1/chat'),
      );
      request.headers.addAll({
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      });
      request.body = jsonEncode({
        'character_id': widget.characterId,
        'message': text,
        if (_conversationId != null) 'conversation_id': _conversationId,
      });

      final client = http.Client();
      final response = await client.send(request);

      if (response.statusCode != 200) {
        throw Exception('请求失败: ${response.statusCode}');
      }

      // 添加空的 AI 消息用于流式填充
      setState(() {
        _messages.add(_ChatMessage(role: 'assistant', content: '', isStreaming: true));
      });

      _digitalHumanController.stopThinking();
      _digitalHumanController.startSpeaking();

      String fullContent = '';
      await for (final chunk in response.stream.transform(utf8.decoder)) {
        final lines = chunk.split('\n');
        for (final line in lines) {
          if (line.startsWith('data: ')) {
            final data = line.substring(6);
            if (data == '[DONE]') continue;
            try {
              final json = jsonDecode(data);
              if (json['type'] == 'token') {
                fullContent += json['content'];
                setState(() {
                  _messages.last = _ChatMessage(
                    role: 'assistant',
                    content: fullContent,
                    isStreaming: true,
                  );
                });
                _scrollToBottom();
              } else if (json['type'] == 'done') {
                _conversationId = json['conversation_id'];
              }
            } catch (_) {}
          }
        }
      }

      client.close();

      setState(() {
        _messages.last = _ChatMessage(
          role: 'assistant',
          content: fullContent,
          isStreaming: false,
        );
        _isSending = false;
      });

      // 停止流式说话动画
      _digitalHumanController.stopSpeaking();

      // 用豆包 TTS 播放完整回复
      _playTTS(fullContent);

    } catch (e) {
      setState(() {
        if (_messages.last.role == 'assistant' && _messages.last.isStreaming) {
          _messages.removeLast();
        }
        _messages.add(_ChatMessage(
          role: 'assistant',
          content: '抱歉，出现了错误：$e',
          isStreaming: false,
        ));
        _isSending = false;
      });
      _digitalHumanController.stopThinking();
      _digitalHumanController.stopSpeaking();
    }

    _scrollToBottom();
  }

  /// 使用豆包 TTS 播放回复
  Future<void> _playTTS(String text) async {
    if (text.isEmpty || _ttsService == null) return;

    setState(() => _isTTSPlaying = true);
    _digitalHumanController.startSpeaking();

    try {
      // 流式逐句合成并播放
      await _ttsService!.streamTextToSpeech(
        text: text,
        onAudioChunk: (audioData, sentenceIndex) {
          // 更新当前播放的句子索引
          debugPrint('[TTS] 句子 $sentenceIndex 合成完成, ${audioData.length} bytes');
          // TODO: 使用 audioplayers 或 just_audio 播放
          // final player = AudioPlayer();
          // await player.play(BytesSource(audioData));
          // await player.onPlayerComplete.first;
        },
        onComplete: () {
          debugPrint('[TTS] 全部播放完成');
        },
      );
    } catch (e) {
      debugPrint('[TTS] 播放失败: $e');
    } finally {
      setState(() => _isTTSPlaying = false);
      _digitalHumanController.stopSpeaking();
      // 播放完成后点个头
      _digitalHumanController.nod();
    }
  }

  /// 停止 TTS 播放
  void _stopTTS() {
    _ttsPlaybackController?.stop();
    _digitalHumanController.stopSpeaking();
    setState(() => _isTTSPlaying = false);
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    _digitalHumanController.dispose();
    _ttsService?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircleAvatar(
              radius: 16,
              backgroundColor: widget.characterSlug == 'libai'
                  ? const Color(0xFF5B4A8A)
                  : const Color(0xFF4A6741),
              child: Text(
                widget.characterName[0],
                style: const TextStyle(color: Colors.white, fontSize: 14),
              ),
            ),
            const SizedBox(width: 8),
            Text(widget.characterName),
            // TTS 播放状态指示
            if (_isTTSPlaying)
              const Padding(
                padding: EdgeInsets.only(left: 8),
                child: SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
          ],
        ),
        actions: [
          // TTS 开关按钮
          IconButton(
            icon: Icon(
              _isTTSPlaying ? Icons.volume_up : Icons.volume_off,
              color: _isTTSPlaying ? AppTheme.primaryColor : Colors.grey,
            ),
            onPressed: _isTTSPlaying ? _stopTTS : null,
            tooltip: _isTTSPlaying ? '停止语音' : '语音未启用',
          ),
        ],
      ),
      body: Column(
        children: [
          // 数字人区域
          _buildDigitalHumanArea(),
          // 消息列表
          Expanded(child: _buildMessageList()),
          // 输入区域
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildDigitalHumanArea() {
    return Container(
      height: 220,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            AppTheme.primaryColor.withOpacity(0.08),
            Colors.transparent,
          ],
        ),
      ),
      child: Center(
        child: Stack(
          alignment: Alignment.center,
          children: [
            // 数字人
            DigitalHumanAvatar(
              controller: _digitalHumanController,
              characterName: widget.characterName,
              size: 180,
            ),
            // 状态标签
            Positioned(
              bottom: 8,
              child: _buildStatusLabel(),
            ),
          ],
        ),
      ),
    );
  }

  /// 状态标签（思考中/说话中/空闲）
  Widget _buildStatusLabel() {
    String label;
    IconData icon;
    Color color;

    if (_isSending && !_digitalHumanController.isSpeaking) {
      label = '思考中...';
      icon = Icons.psychology;
      color = AppTheme.primaryColor.withOpacity(0.7);
    } else if (_digitalHumanController.isSpeaking) {
      label = '说话中';
      icon = Icons.record_voice_over;
      color = AppTheme.primaryColor;
    } else if (_isTTSPlaying) {
      label = '语音播放中';
      icon = Icons.volume_up;
      color = AppTheme.primaryColor;
    } else {
      label = '在线';
      icon = Icons.circle;
      color = Colors.green;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(fontSize: 12, color: color),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageList() {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemCount: _messages.length,
      itemBuilder: (context, index) {
        final msg = _messages[index];
        return _MessageBubble(
          message: msg,
          isLast: index == _messages.length - 1,
        );
      },
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: EdgeInsets.only(
        left: 16,
        right: 8,
        top: 8,
        bottom: MediaQuery.of(context).padding.bottom + 8,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _inputController,
              focusNode: _focusNode,
              decoration: InputDecoration(
                hintText: '向${widget.characterName}提问...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                filled: true,
                fillColor: const Color(0xFFF5F3FF),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 12,
                ),
              ),
              onSubmitted: (_) => _sendMessage(),
              maxLines: null,
              textInputAction: TextInputAction.send,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            decoration: BoxDecoration(
              color: _isSending ? Colors.grey : AppTheme.primaryColor,
              shape: BoxShape.circle,
            ),
            child: IconButton(
              icon: _isSending
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.send, color: Colors.white),
              onPressed: _isSending ? null : _sendMessage,
            ),
          ),
        ],
      ),
    );
  }
}

class _ChatMessage {
  final String role;
  final String content;
  final bool isStreaming;

  _ChatMessage({
    required this.role,
    required this.content,
    this.isStreaming = false,
  });
}

class _MessageBubble extends StatelessWidget {
  final _ChatMessage message;
  final bool isLast;

  const _MessageBubble({required this.message, required this.isLast});

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        decoration: BoxDecoration(
          color: isUser ? AppTheme.chatBubbleUser : AppTheme.chatBubbleAI,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: isUser ? const Radius.circular(16) : Radius.zero,
            bottomRight: isUser ? Radius.zero : const Radius.circular(16),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!isUser)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  '先贤',
                  style: TextStyle(
                    fontSize: 11,
                    color: AppTheme.primaryColor,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            Text(
              message.content,
              style: TextStyle(
                fontSize: 15,
                color: isUser ? Colors.white : AppTheme.textPrimary,
                height: 1.5,
              ),
            ),
            if (message.isStreaming)
              const Padding(
                padding: EdgeInsets.only(top: 4),
                child: SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
