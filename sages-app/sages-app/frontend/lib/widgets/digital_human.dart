import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';

/// 数字人动画控制器
/// 控制虚拟形象的 idle 动画、说话动画、表情变化、手势动画
class DigitalHumanController extends ChangeNotifier {
  // 动画状态
  bool _isSpeaking = false;
  bool _isThinking = false;
  bool _isBlinking = false;
  bool _isNodding = false;

  // 动画参数
  double _mouthOpenness = 0.0;     // 嘴巴张开程度 0~1
  double _eyeOpenness = 1.0;       // 眼睛张开程度 0~1
  double _headTilt = 0.0;          // 头部倾斜 -1~1
  double _bodySway = 0.0;          // 身体摇摆 -1~1
  double _breathScale = 1.0;       // 呼吸缩放 0.98~1.02
  double _expressionIntensity = 0.0; // 表情强度 0~1
  double _leftHandRaise = 0.0;     // 左手抬起 0~1
  double _rightHandRaise = 0.0;    // 右手抬起 0~1
  double _mouthWidth = 1.0;        // 嘴巴宽度 0.5~1.5
  double _eyebrowRaise = 0.0;      // 眉毛抬起 0~1
  double _cheekBlush = 0.0;        // 脸红程度 0~1

  // 定时器
  Timer? _speakTimer;
  Timer? _blinkTimer;
  Timer? _idleTimer;
  Timer? _thinkTimer;
  Timer? _gestureTimer;

  // 随机数生成器
  final _random = Random();

  // 音频同步相关
  double _audioAmplitude = 0.0;  // 当前音频振幅 0~1
  bool _audioDriven = false;     // 是否由音频驱动嘴型

  bool get isSpeaking => _isSpeaking;
  bool get isThinking => _isThinking;
  double get mouthOpenness => _mouthOpenness;
  double get eyeOpenness => _eyeOpenness;
  double get headTilt => _headTilt;
  double get bodySway => _bodySway;
  double get breathScale => _breathScale;
  double get expressionIntensity => _expressionIntensity;
  double get leftHandRaise => _leftHandRaise;
  double get rightHandRaise => _rightHandRaise;
  double get mouthWidth => _mouthWidth;
  double get eyebrowRaise => _eyebrowRaise;
  double get cheekBlush => _cheekBlush;

  DigitalHumanController() {
    _startIdleAnimation();
    _startBlinkAnimation();
  }

  /// 开始说话动画
  void startSpeaking() {
    if (_isSpeaking) return;
    _isSpeaking = true;
    _isThinking = false;
    _thinkTimer?.cancel();
    notifyListeners();

    // 模拟嘴巴开合（非音频驱动模式）
    if (!_audioDriven) {
      _speakTimer = Timer.periodic(const Duration(milliseconds: 60), (_) {
        // 模拟自然语音的嘴型变化
        final t = DateTime.now().millisecondsSinceEpoch / 1000.0;
        // 用多个正弦波叠加模拟自然嘴型
        final base = sin(t * 8.0) * 0.3 + sin(t * 12.0) * 0.2 + sin(t * 5.0) * 0.15;
        _mouthOpenness = (0.3 + base + _random.nextDouble() * 0.2).clamp(0.0, 1.0);
        _mouthWidth = 0.8 + sin(t * 6.0) * 0.3;
        // 说话时轻微摇头
        _headTilt = sin(t * 2.0) * 0.08 + (_random.nextDouble() - 0.5) * 0.05;
        // 表情更丰富
        _expressionIntensity = 0.5 + _random.nextDouble() * 0.5;
        // 眉毛微动
        _eyebrowRaise = sin(t * 3.0) * 0.2;
        notifyListeners();
      });
    }
  }

  /// 停止说话动画
  void stopSpeaking() {
    _isSpeaking = false;
    _speakTimer?.cancel();
    _speakTimer = null;
    _audioDriven = false;
    _audioAmplitude = 0.0;
    _mouthOpenness = 0.0;
    _mouthWidth = 1.0;
    _headTilt = 0.0;
    _expressionIntensity = 0.3;
    _eyebrowRaise = 0.0;
    _leftHandRaise = 0.0;
    _rightHandRaise = 0.0;
    notifyListeners();
  }

  /// 设置音频振幅（用于音频驱动的嘴型同步）
  void setAudioAmplitude(double amplitude) {
    _audioDriven = true;
    _audioAmplitude = amplitude.clamp(0.0, 1.0);
    if (_isSpeaking) {
      // 平滑过渡嘴型
      _mouthOpenness = _audioAmplitude * 0.8 + 0.1;
      _mouthWidth = 0.7 + _audioAmplitude * 0.5;
      _expressionIntensity = 0.3 + _audioAmplitude * 0.7;
      notifyListeners();
    }
  }

  /// 开始思考动画
  void startThinking() {
    if (_isThinking) return;
    _isThinking = true;
    _isSpeaking = false;
    _speakTimer?.cancel();
    notifyListeners();

    _thinkTimer = Timer.periodic(const Duration(milliseconds: 500), (_) {
      final t = DateTime.now().millisecondsSinceEpoch / 1000.0;
      // 思考时眼睛看向不同方向
      _headTilt = sin(t * 1.5) * 0.08;
      _expressionIntensity = 0.2;
      _eyebrowRaise = 0.3 + sin(t * 2.0) * 0.2;
      notifyListeners();
    });
  }

  /// 停止思考动画
  void stopThinking() {
    _isThinking = false;
    _thinkTimer?.cancel();
    _thinkTimer = null;
    _headTilt = 0.0;
    _eyebrowRaise = 0.0;
    notifyListeners();
  }

  /// 触发点头动画
  void nod() {
    if (_isNodding) return;
    _isNodding = true;
    _headTilt = -0.15;
    notifyListeners();

    // 点头序列：下 -> 上 -> 回中
    Future.delayed(const Duration(milliseconds: 200), () {
      _headTilt = 0.1;
      notifyListeners();
    });
    Future.delayed(const Duration(milliseconds: 400), () {
      _headTilt = -0.05;
      notifyListeners();
    });
    Future.delayed(const Duration(milliseconds: 550), () {
      _headTilt = 0.0;
      _isNodding = false;
      notifyListeners();
    });
  }

  /// 触发手势动画（说话时随机使用）
  void _triggerGesture() {
    if (!_isSpeaking) return;
    final gesture = _random.nextInt(3);
    switch (gesture) {
      case 0: // 左手抬起
        _animateHand(isLeft: true);
        break;
      case 1: // 右手抬起
        _animateHand(isLeft: false);
        break;
      case 2: // 双手微抬
        _animateHand(isLeft: true, isRight: true);
        break;
    }
  }

  /// 手势动画
  void _animateHand({bool isLeft = false, bool isRight = false}) {
    final target = isLeft ? 0.6 : 0.0;
    final target2 = isRight ? 0.6 : 0.0;

    // 渐入
    _leftHandRaise = target;
    _rightHandRaise = target2;
    notifyListeners();

    // 保持一会
    Future.delayed(Duration(milliseconds: 600 + _random.nextInt(400)), () {
      // 渐出
      _leftHandRaise = 0.0;
      _rightHandRaise = 0.0;
      notifyListeners();
    });
  }

  /// 空闲动画 - 呼吸 + 轻微摇摆
  void _startIdleAnimation() {
    _idleTimer = Timer.periodic(const Duration(milliseconds: 50), (_) {
      final t = DateTime.now().millisecondsSinceEpoch / 1000.0;
      // 呼吸效果
      _breathScale = 1.0 + sin(t * 1.5) * 0.015;
      // 轻微身体摇摆
      _bodySway = sin(t * 0.8) * 0.02;
      notifyListeners();
    });
  }

  /// 眨眼动画
  void _startBlinkAnimation() {
    _blinkTimer = Timer.periodic(
      Duration(milliseconds: 2000 + _random.nextInt(3000)),
      (_) {
        _isBlinking = true;
        _eyeOpenness = 0.0;
        notifyListeners();

        // 眨眼持续 150ms
        Future.delayed(const Duration(milliseconds: 150), () {
          _isBlinking = false;
          _eyeOpenness = 1.0;
          notifyListeners();
        });
      },
    );
  }

  @override
  void dispose() {
    _speakTimer?.cancel();
    _blinkTimer?.cancel();
    _idleTimer?.cancel();
    _thinkTimer?.cancel();
    _gestureTimer?.cancel();
    super.dispose();
  }
}

/// 数字人虚拟形象 Widget
class DigitalHumanAvatar extends StatelessWidget {
  final DigitalHumanController controller;
  final String characterName;
  final double size;

  const DigitalHumanAvatar({
    super.key,
    required this.controller,
    required this.characterName,
    this.size = 200,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      listenable: controller,
      builder: (context, child) {
        return Transform(
          alignment: Alignment.center,
          transform: Matrix4.identity()
            ..scale(controller.breathScale)
            ..rotateZ(controller.bodySway),
          child: SizedBox(
            width: size,
            height: size,
            child: CustomPaint(
              painter: _DigitalHumanPainter(
                mouthOpenness: controller.mouthOpenness,
                eyeOpenness: controller.eyeOpenness,
                headTilt: controller.headTilt,
                expressionIntensity: controller.expressionIntensity,
                isSpeaking: controller.isSpeaking,
                isThinking: controller.isThinking,
                characterName: characterName,
                leftHandRaise: controller.leftHandRaise,
                rightHandRaise: controller.rightHandRaise,
                mouthWidth: controller.mouthWidth,
                eyebrowRaise: controller.eyebrowRaise,
                cheekBlush: controller.cheekBlush,
              ),
            ),
          ),
        );
      },
    );
  }
}

/// 简化版 AnimatedBuilder（Flutter 3.24 兼容）
class AnimatedBuilder extends StatelessWidget {
  final Listenable listenable;
  final Widget Function(BuildContext, Widget?) builder;
  final Widget? child;

  const AnimatedBuilder({
    super.key,
    required this.listenable,
    required this.builder,
    this.child,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder2(
      listenable: listenable,
      builder: builder,
      child: child,
    );
  }
}

class AnimatedBuilder2 extends AnimatedWidget {
  final Widget Function(BuildContext, Widget?) builder;
  final Widget? child;

  const AnimatedBuilder2({
    super.key,
    required super.listenable,
    required this.builder,
    this.child,
  }) : super();

  @override
  Widget build(BuildContext context) {
    return builder(context, child);
  }
}

/// 数字人绘制器 - 用 Canvas 绘制一个风格化的古代人物头像
/// 支持：嘴型同步、表情变化、手势动画、呼吸动画、眨眼动画
class _DigitalHumanPainter extends CustomPainter {
  final double mouthOpenness;
  final double eyeOpenness;
  final double headTilt;
  final double expressionIntensity;
  final bool isSpeaking;
  final bool isThinking;
  final String characterName;
  final double leftHandRaise;
  final double rightHandRaise;
  final double mouthWidth;
  final double eyebrowRaise;
  final double cheekBlush;

  _DigitalHumanPainter({
    required this.mouthOpenness,
    required this.eyeOpenness,
    required this.headTilt,
    required this.expressionIntensity,
    required this.isSpeaking,
    required this.isThinking,
    required this.characterName,
    required this.leftHandRaise,
    required this.rightHandRaise,
    required this.mouthWidth,
    required this.eyebrowRaise,
    required this.cheekBlush,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final scale = size.width / 200;
    final t = DateTime.now().millisecondsSinceEpoch / 1000.0;

    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.rotate(headTilt * 0.1);
    canvas.translate(-center.dx, -center.dy);

    // 背景光晕
    if (isSpeaking) {
      final glowPaint = Paint()
        ..color = const Color(0xFF6B5CE7).withOpacity(0.15 + sin(t * 3) * 0.05)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 30);
      canvas.drawCircle(center, 90 * scale, glowPaint);
    }

    // 身体/衣服 + 手势
    _drawBody(canvas, center, scale, t);

    // 脖子
    final neckPaint = Paint()..color = _skinColor;
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(center.dx, center.dy + 45 * scale),
            width: 30 * scale, height: 25 * scale),
        Radius.circular(5 * scale),
      ),
      neckPaint,
    );

    // 头部
    _drawHead(canvas, center, scale);

    // 五官
    _drawFace(canvas, center, scale, t);

    // 头发/帽子
    _drawHair(canvas, center, scale, t);

    // 思考气泡
    if (isThinking) {
      _drawThinkingBubble(canvas, center, scale, t);
    }

    // 说话时的声波效果
    if (isSpeaking) {
      _drawSoundWaves(canvas, center, scale, t);
    }

    canvas.restore();
  }

  void _drawBody(Canvas canvas, Offset center, double scale, double t) {
    final bodyPaint = Paint()..color = _robeColor;
    final path = Path();
    path.moveTo(center.dx - 55 * scale, center.dy + 90 * scale);
    path.quadraticBezierTo(
        center.dx - 65 * scale, center.dy + 60 * scale,
        center.dx - 35 * scale, center.dy + 50 * scale);
    path.lineTo(center.dx + 35 * scale, center.dy + 50 * scale);
    path.quadraticBezierTo(
        center.dx + 65 * scale, center.dy + 60 * scale,
        center.dx + 55 * scale, center.dy + 90 * scale);
    path.quadraticBezierTo(
        center.dx, center.dy + 95 * scale,
        center.dx - 55 * scale, center.dy + 90 * scale);
    canvas.drawPath(path, bodyPaint);

    // 衣领
    final collarPaint = Paint()..color = _robeColor.withOpacity(0.8);
    final collarPath = Path();
    collarPath.moveTo(center.dx - 15 * scale, center.dy + 50 * scale);
    collarPath.lineTo(center.dx, center.dy + 75 * scale);
    collarPath.lineTo(center.dx + 15 * scale, center.dy + 50 * scale);
    canvas.drawPath(collarPath, collarPaint);

    // 左手
    if (leftHandRaise > 0.01) {
      _drawHand(canvas, center, scale, t, isLeft: true, raise: leftHandRaise);
    }

    // 右手
    if (rightHandRaise > 0.01) {
      _drawHand(canvas, center, scale, t, isLeft: false, raise: rightHandRaise);
    }
  }

  void _drawHand(Canvas canvas, Offset center, double scale, double t,
      {required bool isLeft, required double raise}) {
    final handPaint = Paint()
      ..color = _skinColor
      ..strokeWidth = 8 * scale
      ..strokeCap = StrokeCap.round;

    final xDir = isLeft ? -1.0 : 1.0;
    final startX = center.dx + xDir * 40 * scale;
    final startY = center.dy + 65 * scale;
    final endX = startX + xDir * 25 * scale * raise;
    final endY = startY - 35 * scale * raise;

    // 手臂
    canvas.drawLine(
      Offset(startX, startY),
      Offset(endX, endY),
      handPaint,
    );

    // 手掌
    final palmPaint = Paint()..color = _skinColor;
    canvas.drawCircle(Offset(endX, endY), 6 * scale, palmPaint);

    // 手指（简单的线条）
    final fingerPaint = Paint()
      ..color = _skinColor
      ..strokeWidth = 2.5 * scale
      ..strokeCap = StrokeCap.round;
    for (int i = -1; i <= 1; i++) {
      canvas.drawLine(
        Offset(endX, endY),
        Offset(endX + i * 4 * scale, endY - 8 * scale * raise),
        fingerPaint,
      );
    }
  }

  void _drawHead(Canvas canvas, Offset center, double scale) {
    final headPaint = Paint()..color = _skinColor;
    canvas.drawCircle(
        Offset(center.dx, center.dy + 10 * scale), 42 * scale, headPaint);

    // 耳朵
    canvas.drawOval(
      Rect.fromCenter(
          center: Offset(center.dx - 42 * scale, center.dy + 10 * scale),
          width: 12 * scale,
          height: 18 * scale),
      headPaint,
    );
    canvas.drawOval(
      Rect.fromCenter(
          center: Offset(center.dx + 42 * scale, center.dy + 10 * scale),
          width: 12 * scale,
          height: 18 * scale),
      headPaint,
    );
  }

  void _drawFace(Canvas canvas, Offset center, double scale, double t) {
    // 脸红效果
    if (cheekBlush > 0.01) {
      final blushPaint = Paint()
        ..color = const Color(0xFFFF9999).withOpacity(cheekBlush * 0.3)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8);
      canvas.drawCircle(
        Offset(center.dx - 25 * scale, center.dy + 12 * scale),
        10 * scale, blushPaint,
      );
      canvas.drawCircle(
        Offset(center.dx + 25 * scale, center.dy + 12 * scale),
        10 * scale, blushPaint,
      );
    }

    // 眉毛（支持抬起）
    final browPaint = Paint()
      ..color = _hairColor
      ..strokeWidth = 2.5 * scale
      ..strokeCap = StrokeCap.round;

    final browOffset = -eyebrowRaise * 5 * scale;

    // 左眉
    canvas.drawLine(
      Offset(center.dx - 22 * scale, center.dy - 8 * scale + browOffset),
      Offset(center.dx - 8 * scale, center.dy - 12 * scale + browOffset),
      browPaint,
    );
    // 右眉
    canvas.drawLine(
      Offset(center.dx + 8 * scale, center.dy - 12 * scale + browOffset),
      Offset(center.dx + 22 * scale, center.dy - 8 * scale + browOffset),
      browPaint,
    );

    // 眼睛
    _drawEyes(canvas, center, scale, t);

    // 鼻子
    final nosePaint = Paint()
      ..color = _skinColor.withOpacity(0.6)
      ..strokeWidth = 1.5 * scale
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(
      Offset(center.dx, center.dy - 2 * scale),
      Offset(center.dx - 3 * scale, center.dy + 8 * scale),
      nosePaint,
    );

    // 嘴巴（支持宽度变化）
    _drawMouth(canvas, center, scale);

    // 胡须（孔子）
    if (characterName == '孔子') {
      _drawBeard(canvas, center, scale, t);
    }
  }

  void _drawEyes(Canvas canvas, Offset center, double scale, double t) {
    final eyeY = center.dy - 2 * scale;
    final eyeWidth = 10 * scale;
    final eyeHeight = eyeOpenness * 6 * scale;

    // 眼白
    final eyeWhitePaint = Paint()..color = Colors.white;
    canvas.drawOval(
      Rect.fromCenter(
          center: Offset(center.dx - 15 * scale, eyeY),
          width: eyeWidth * 2,
          height: max(eyeHeight * 2, 2 * scale)),
      eyeWhitePaint,
    );
    canvas.drawOval(
      Rect.fromCenter(
          center: Offset(center.dx + 15 * scale, eyeY),
          width: eyeWidth * 2,
          height: max(eyeHeight * 2, 2 * scale)),
      eyeWhitePaint,
    );

    if (eyeOpenness > 0.1) {
      // 瞳孔（说话时瞳孔会轻微跟随头部方向）
      final pupilOffset = headTilt * 2 * scale;
      final pupilPaint = Paint()..color = const Color(0xFF1A1A2E);
      canvas.drawCircle(
          Offset(center.dx - 15 * scale + pupilOffset, eyeY),
          4 * scale * eyeOpenness, pupilPaint);
      canvas.drawCircle(
          Offset(center.dx + 15 * scale + pupilOffset, eyeY),
          4 * scale * eyeOpenness, pupilPaint);

      // 高光
      final highlightPaint = Paint()..color = Colors.white;
      canvas.drawCircle(
          Offset(center.dx - 13 * scale, eyeY - 1.5 * scale),
          1.5 * scale * eyeOpenness,
          highlightPaint,
      );
      canvas.drawCircle(
          Offset(center.dx + 17 * scale, eyeY - 1.5 * scale),
          1.5 * scale * eyeOpenness,
          highlightPaint,
      );
    }
  }

  void _drawMouth(Canvas canvas, Offset center, double scale) {
    final mouthY = center.dy + 18 * scale;
    final baseMouthWidth = 14 * scale;
    final currentMouthWidth = baseMouthWidth * mouthWidth;

    if (mouthOpenness > 0.1) {
      // 说话时嘴巴张开 - 椭圆形
      final mouthPaint = Paint()..color = const Color(0xFF8B4040);
      canvas.drawOval(
        Rect.fromCenter(
            center: Offset(center.dx, mouthY + mouthOpenness * 3 * scale),
            width: currentMouthWidth,
            height: mouthOpenness * 12 * scale),
        mouthPaint,
      );

      // 舌头（嘴巴张开较大时可见）
      if (mouthOpenness > 0.4) {
        final tonguePaint = Paint()..color = const Color(0xFFCC6666);
        canvas.drawOval(
          Rect.fromCenter(
              center: Offset(center.dx, mouthY + mouthOpenness * 5 * scale),
              width: currentMouthWidth * 0.5,
              height: mouthOpenness * 4 * scale),
          tonguePaint,
        );
      }

      // 上排牙齿
      if (mouthOpenness > 0.3) {
        final teethPaint = Paint()..color = Colors.white;
        canvas.drawRect(
          Rect.fromCenter(
              center: Offset(center.dx, mouthY + mouthOpenness * 1 * scale),
              width: currentMouthWidth * 0.8,
              height: mouthOpenness * 2.5 * scale),
          teethPaint,
        );
      }
    } else {
      // 微笑
      final smilePaint = Paint()
        ..color = const Color(0xFF8B4040)
        ..strokeWidth = 2 * scale
        ..strokeCap = StrokeCap.round;
      final smileWidth = currentMouthWidth * (0.6 + expressionIntensity * 0.4);
      canvas.drawArc(
        Rect.fromCenter(
            center: Offset(center.dx, mouthY),
            width: smileWidth * 2,
            height: 8 * scale),
        0,
        pi,
        false,
        smilePaint,
      );
    }
  }

  void _drawBeard(Canvas canvas, Offset center, double scale, double t) {
    final beardPaint = Paint()
      ..color = _hairColor.withOpacity(0.7)
      ..strokeWidth = 1.2 * scale
      ..strokeCap = StrokeCap.round;

    for (int i = -3; i <= 3; i++) {
      final startX = center.dx + i * 5 * scale;
      final startY = center.dy + 24 * scale;
      final length = (15 + (3 - i.abs()) * 3) * scale;
      // 说话时胡须轻微摆动
      final sway = isSpeaking ? sin(t * 5.0 + i) * 2 : 0;
      canvas.drawLine(
        Offset(startX, startY),
        Offset(startX + sway, startY + length),
        beardPaint,
      );
    }
  }

  void _drawHair(Canvas canvas, Offset center, double scale, double t) {
    final hairPaint = Paint()..color = _hairColor;

    if (characterName == '孔子') {
      // 孔子 - 方巾帽
      final hatPath = Path();
      hatPath.moveTo(center.dx - 48 * scale, center.dy - 15 * scale);
      hatPath.quadraticBezierTo(
          center.dx - 50 * scale, center.dy - 45 * scale,
          center.dx, center.dy - 50 * scale);
      hatPath.quadraticBezierTo(
          center.dx + 50 * scale, center.dy - 45 * scale,
          center.dx + 48 * scale, center.dy - 15 * scale);
      hatPath.lineTo(center.dx - 48 * scale, center.dy - 15 * scale);
      canvas.drawPath(hatPath, hairPaint);

      // 帽子装饰带
      final bandPaint = Paint()..color = const Color(0xFF4A3CD7);
      canvas.drawRect(
        Rect.fromCenter(
            center: Offset(center.dx, center.dy - 18 * scale),
            width: 96 * scale,
            height: 6 * scale),
        bandPaint,
      );
    } else {
      // 李白 - 飘逸长发
      final hairPath = Path();
      hairPath.moveTo(center.dx - 44 * scale, center.dy - 5 * scale);
      hairPath.quadraticBezierTo(
          center.dx - 50 * scale, center.dy - 40 * scale,
          center.dx, center.dy - 48 * scale);
      hairPath.quadraticBezierTo(
          center.dx + 50 * scale, center.dy - 40 * scale,
          center.dx + 44 * scale, center.dy - 5 * scale);
      canvas.drawPath(hairPath, hairPaint);

      // 飘逸的发尾（说话时摆动更明显）
      final sway = isSpeaking
          ? sin(t * 4.0) * 5
          : sin(t * 1.5) * 3;
      canvas.drawLine(
        Offset(center.dx - 44 * scale, center.dy - 5 * scale),
        Offset(center.dx - 50 * scale + sway, center.dy + 20 * scale),
        Paint()..color = _hairColor..strokeWidth = 8 * scale..strokeCap = StrokeCap.round,
      );
      canvas.drawLine(
        Offset(center.dx + 44 * scale, center.dy - 5 * scale),
        Offset(center.dx + 50 * scale - sway, center.dy + 20 * scale),
        Paint()..color = _hairColor..strokeWidth = 8 * scale..strokeCap = StrokeCap.round,
      );
    }
  }

  void _drawThinkingBubble(Canvas canvas, Offset center, double scale, double t) {
    final bubblePaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;
    final borderPaint = Paint()
      ..color = const Color(0xFF6B5CE7)
      ..strokeWidth = 1.5 * scale
      ..style = PaintingStyle.stroke;

    // 小圆点（脉动效果）
    final dotScale = 1.0 + sin(t * 4.0) * 0.2;
    canvas.drawCircle(
      Offset(center.dx + 50 * scale, center.dy - 20 * scale),
      4 * scale * dotScale, bubblePaint,
    );
    canvas.drawCircle(
      Offset(center.dx + 50 * scale, center.dy - 20 * scale),
      4 * scale * dotScale, borderPaint,
    );

    // 气泡
    final bubbleRect = RRect.fromRectAndRadius(
      Rect.fromCenter(
          center: Offset(center.dx + 65 * scale, center.dy - 40 * scale),
          width: 30 * scale,
          height: 20 * scale),
      Radius.circular(10 * scale),
    );
    canvas.drawRRect(bubbleRect, bubblePaint);
    canvas.drawRRect(bubbleRect, borderPaint);

    // 省略号（依次跳动）
    final dotPaint = Paint()..color = const Color(0xFF6B5CE7);
    for (int i = 0; i < 3; i++) {
      final dotY = center.dy - 40 * scale + sin(t * 5.0 + i * 1.2) * 2 * scale;
      canvas.drawCircle(
        Offset(center.dx + 57 * scale + i * 8 * scale, dotY),
        2 * scale,
        dotPaint,
      );
    }
  }

  void _drawSoundWaves(Canvas canvas, Offset center, double scale, double t) {
    // 说话时从嘴巴位置发出声波
    final wavePaint = Paint()
      ..color = const Color(0xFF6B5CE7).withOpacity(0.15)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5 * scale;

    for (int i = 0; i < 3; i++) {
      final phase = (t * 2.0 + i * 0.7) % 2.0;
      final radius = (20 + phase * 30) * scale;
      final opacity = max(0, 1.0 - phase / 2.0) * 0.3;

      wavePaint.color = const Color(0xFF6B5CE7).withOpacity(opacity);
      canvas.drawCircle(
        Offset(center.dx, center.dy + 18 * scale),
        radius,
        wavePaint,
      );
    }
  }

  Color get _skinColor => const Color(0xFFFDEBD0);
  Color get _hairColor => const Color(0xFF2C2C2C);
  Color get _robeColor {
    if (characterName == '孔子') return const Color(0xFF4A6741); // 儒家绿袍
    if (characterName == '李白') return const Color(0xFF5B4A8A); // 仙气紫袍
    return const Color(0xFF4A6741);
  }

  @override
  bool shouldRepaint(covariant _DigitalHumanPainter oldDelegate) => true;
}
