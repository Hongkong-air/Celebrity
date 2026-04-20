# 测试代码与前端升级 - 完成清单

## 一、后端测试文件（6个新增）

### 1. `tests/test_rag/test_retriever.py` — 混合检索器测试
- `TestHybridRetrieverInit`: 初始化默认状态、collection 名称
- `TestHybridRetrieverConnect`: 连接创建、幂等性
- `TestHybridRetrieverEnsureCollection`: collection 自动创建
- `TestHybridRetrieverSearch`: 空结果、正常检索、缺失 payload 处理

### 2. `tests/test_rag/test_reranker.py` — 重排序测试
- `TestRerankEmpty`: 空结果直接返回
- `TestRerankNormal`: 正常重排序、参数验证
- `TestRerankTopK`: top_k 截断、默认 top_k=3

### 3. `tests/test_rag/test_indexer.py` — 索引构建测试
- `TestBuildIndexFileReading`: JSONL 文件读取
- `TestBuildIndexBatchUpsert`: 批量入库
- `TestBuildIndexPayloadDefaults`: 缺失字段默认值

### 4. `tests/test_services/test_user_service.py` — 用户服务测试
- `TestUserServiceRegister`: 注册成功、重复用户名
- `TestUserServiceAuthenticate`: 登录成功、错误密码、不存在用户
- `TestUserServiceGetById`: 查询存在/不存在用户

### 5. `tests/test_services/test_character_service.py` — 人物服务测试
- `TestCharacterServiceGetAll`: active_only 过滤
- `TestCharacterServiceGetById`: 按 ID 查询
- `TestCharacterServiceGetBySlug`: 按 slug 查询
- `TestCharacterServiceCreate`: 创建人物
- `TestCharacterServiceUpdate`: 更新、多字段更新、不存在字段处理

### 6. `tests/test_services/test_conversation_service.py` — 会话服务测试
- `TestConversationServiceCreate`: 创建会话
- `TestConversationServiceGetById`: 按 ID 查询
- `TestConversationServiceGetByUser`: 用户会话列表
- `TestConversationServiceAddMessage`: 添加消息
- `TestConversationServiceGetMessages`: 消息历史、limit、空消息

---

## 二、前端升级

### 1. 数字人动画升级 (`widgets/digital_human.dart`)
新增功能：
- **手势动画**: 左手/右手抬起 (`leftHandRaise`, `rightHandRaise`)
- **点头动画**: `nod()` 方法，说话结束时自动点头
- **表情增强**: 嘴巴宽度 (`mouthWidth`)、眉毛抬起 (`eyebrowRaise`)、脸红 (`cheekBlush`)
- **音频驱动嘴型**: `updateAudioAmplitude()` 方法，接收音频振幅实时驱动嘴巴
- **声波特效**: 说话时从嘴巴位置发出扩散声波
- **思考气泡**: 省略号跳动动画
- **平滑过渡**: 所有参数使用 `lerp` 平滑插值

### 2. 豆包语音 TTS (`services/doubao_tts_service.dart`) — 新文件
核心功能：
- **DoubaoTtsService**: 豆包语音 API 封装
  - `textToSpeech()`: 文本转语音（支持缓存）
  - `streamTextToSpeech()`: 流式逐句合成（实时对话场景）
  - 长文本自动分段合成
  - 音色/语速/音量/音调可调
- **VoicePresets**: 古代人物音色预设
  - 孔子/李白/老子 → 古风男声
  - 李清照 → 古风女声
- **TtsPlaybackController**: 播放状态管理（ChangeNotifier）

### 3. 聊天界面集成 (`screens/chat/chat_screen.dart`)
- 集成 `DoubaoTtsService` 替换旧 TTS
- 集成 `TtsPlaybackController` 管理播放状态
- 数字人区域增大到 220px
- 新增状态标签（思考中/说话中/语音播放中/在线）
- AppBar 新增 TTS 播放/停止按钮
- 播放完成后自动点头动画

### 4. 依赖更新 (`pubspec.yaml`)
- 新增 `audioplayers: ^6.1.0`（音频播放）

---

## 三、运行测试

```bash
cd backend

# 运行全部测试
pytest tests/ -v

# 运行单个模块
pytest tests/test_rag/test_retriever.py -v
pytest tests/test_rag/test_reranker.py -v
pytest tests/test_rag/test_indexer.py -v
pytest tests/test_services/test_user_service.py -v
pytest tests/test_services/test_character_service.py -v
pytest tests/test_services/test_conversation_service.py -v

# 运行已有测试（确认无回归）
pytest tests/test_api/ tests/test_middleware/ tests/test_rag/ tests/test_services/ -v
```

---

## 四、豆包 TTS 配置

在运行前需要配置环境变量：

```bash
# Flutter 编译时传入
flutter build apk --dart-define=DOUBAO_TTS_APP_ID=your_app_id \
                  --dart-define=DOUBAO_TTS_ACCESS_TOKEN=your_token
```

或在代码中直接初始化（开发阶段）：

```dart
final tts = DoubaoTtsService(
  appId: 'YOUR_APP_ID',
  accessToken: 'YOUR_ACCESS_TOKEN',
);
```

### 获取密钥步骤
1. 前往 [火山引擎控制台](https://console.volcengine.com/)
2. 开通「语音合成 TTS」服务
3. 创建应用获取 App ID
4. 获取 Access Token（API Key）
