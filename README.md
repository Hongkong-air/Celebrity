# Celebrity
Android app ,talk with ancient people
# Celebrity - 与历史名人对话的AI-Native安卓应用

![Project Banner](https://via.placeholder.com/800x200?text=Celebrity+AI+Historical+Figures)

一个创新的移动应用，让用户能够与孔子、李白等中国古代历史名人进行沉浸式对话。通过结合大语言模型微调和检索增强生成（RAG）技术，重现历史人物的语言风格、知识体系和思想精髓。

## 1. 项目内容

### 核心功能
- **历史人物对话**: 与预设的历史人物（如孔子、李白）进行多轮自然语言对话
- **个性化人格**: 每个历史人物都经过专门的LoRA微调，确保回答符合其历史背景和语言风格
- **知识增强**: 基于RAG技术，从真实历史文献中检索相关信息，确保回答的准确性和权威性
- **跨平台支持**: 支持Android、iOS、Web和桌面平台

### 应用场景
- **教育学习**: 让学生以互动方式学习历史文化知识
- **文化传承**: 数字化重现历史名人的智慧和思想
- **娱乐体验**: 提供独特的AI对话娱乐体验

## 2. 项目工程架构

### 整体架构
采用**客户端-服务器（C/S）架构**，实现前后端分离和微服务化设计：

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Flutter       │    │   FastAPI        │    │   AI Services       │
│   Frontend      │◄──►│   Backend        │◄──►│   (LLM + RAG)       │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
       ▲                          ▲                       ▲
       │                          │                       │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Multi-platform│    │   PostgreSQL     │    │   Qdrant Vector DB  │
│   (Android/iOS) │    │   + Redis        │    │   + Embedding Svc   │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

### 技术栈选择
- **前端**: Flutter (Dart) - 实现一套代码多平台部署
- **后端**: Python + FastAPI - 高性能异步API服务
- **数据库**: 
  - PostgreSQL - 存储用户信息、会话记录等结构化数据
  - Redis - 缓存和会话管理
  - Qdrant - 向量数据库，用于RAG知识检索
- **AI基础设施**: 
  - PyTorch + HuggingFace Transformers - 模型训练和推理
  - Docker - 容器化部署嵌入服务

### 架构优势
- **可扩展性**: 微服务架构便于添加新的人物角色和功能模块
- **性能优化**: 异步处理和缓存机制确保响应速度
- **维护性**: 清晰的分层架构和模块化设计

## 3. AI方法

### 基础模型选择
采用 **Qwen2.5-7B** 作为基础大语言模型，处理文本生成微调数据集，制作RAG数据

### LoRA人格模块微调
使用**低秩适应（LoRA）**技术对Qwen3-4B-rpg-roleplay进行高效微调：

- **微调策略**: 
  - 为每个历史人物创建独立的LoRA适配器
  - 冻结基础模型参数，仅训练低秩矩阵
  - 保持模型的通用能力同时注入特定人格特征

### RAG数据库制作方法
*[此部分由项目维护者自行补充]*

## 快速开始

### 环境要求
- Python 3.10+
- Flutter SDK
- PostgreSQL 14+
- Redis 6+
- Docker (可选，用于嵌入服务)

### 安装步骤
```bash
# 1. 克隆项目
git clone https://github.com/your-username/Celebrity.git
cd Celebrity

# 2. 设置后端环境
conda create -n sages-app python=3.10
conda activate sages-app
cd sages-app/sages-app/backend
pip install -e .

# 3. 设置前端环境  
cd ../frontend
flutter pub get

# 4. 配置环境变量
cp .env.example .env
# 编辑.env文件，配置数据库和AI服务连接信息

# 5. 启动服务
# 终端1: 启动后端
python -m uvicorn app.main:app --reload --port 8000

# 终端2: 启动前端
flutter run
```

## 项目结构
```
Celebrity/
├── multiLORA/           # AI模型训练和数据处理
├── sages-app/
│   ├── backend/         # Python后端服务
│   ├── embedding-service/ # 向量嵌入服务
│   └── frontend/        # Flutter前端应用
└── sages-app-env/       # Python虚拟环境
```

## 贡献指南
欢迎提交Issue和Pull Request！请确保：
- 遵循项目的代码规范
- 添加相应的测试用例
- 更新相关文档

## 许可证
[MIT License](LICENSE)

---

**让历史活起来，与智慧对话！**
