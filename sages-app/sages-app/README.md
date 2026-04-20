# 人类群星闪耀时 - Sages App

AI 驱动的古人对话应用，通过人格微调大模型 + RAG 检索增强，实现沉浸式对话体验。

## 架构

- **后端**: Python / FastAPI
- **前端**: Flutter (Android)
- **向量数据库**: Qdrant (混合检索)
- **Embedding**: bge-m3 (dense + sparse)
- **重排序**: bge-reranker-v2-m3
- **LLM**: vLLM 本地部署微调模型
- **数据库**: PostgreSQL + Redis

## 快速开始

```bash
# 1. 安装后端依赖
cd backend
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env

# 3. 启动开发服务器
uvicorn app.main:app --reload --port 8000

# 4. 访问 API 文档
# http://localhost:8000/docs
```

## 项目结构

详见 [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)

## 模块实施进度

- [x] 阶段1: 项目骨架 + 后端基础
- [ ] 阶段2: 数据层 (PostgreSQL + ORM)
- [ ] 阶段3: 用户认证 (JWT)
- [ ] 阶段4: 人物管理
- [ ] 阶段5: 会话与消息
- [ ] 阶段6: Embedding 微服务
- [ ] 阶段7: RAG 核心
- [ ] 阶段8: LLM 服务
- [ ] 阶段9: 对话编排
- [ ] 阶段10: Flutter 前端
- [ ] 阶段11: Docker 部署
