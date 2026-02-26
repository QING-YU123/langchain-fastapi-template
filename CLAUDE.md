# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于 **LangChain + LangServe + FastAPI** 构建的模块化 AI 聊天服务，采用领域驱动设计（DDD）分层架构。

## 开发命令

### 启动服务
```bash
uvicorn app.main:app --reload --host localhost --port 8000
```

### 依赖安装
```bash
pip install -r requirements.txt
```
> 注意：当前 `requirements.txt` 为空，需根据实际使用添加依赖（如 `langchain`, `langserve`, `fastapi`, `uvicorn`, `pydantic-settings`, `langchain-openai` 等）

## 架构设计

### 分层结构
```
app/
├── main.py              # FastAPI 应用入口
├── core/                # 核心配置层 - Pydantic Settings 环境变量管理
├── llms/                # 模型层 - 统一实例化 LLM（ChatOpenAI 等）
├── prompts/             # 提示词层 - PromptTemplate 管理
├── schemas/             # 数据定义层 - Pydantic DTOs
├── workflows/           # 业务逻辑层 - LCEL 链路和 LangGraph 应用
│   ├── lcel/           # LCEL 表达式语言链路
│   └── graph/          # LangGraph 状态图应用（预留）
└── api/                # 接口层 - LangServe 路由注册
```

### 关键设计原则

1. **配置集中化**：所有环境变量通过 `app/core/config.py` 的 `Settings` 类管理，使用 Pydantic `BaseSettings`
   - 必需变量：`OPENAI_API_KEY`, `OPENAI_API_BASE`, `MODEL_NAME`
   - 配置文件：`.env`

2. **模型工厂模式**：`app/llms/builder.py` 中的 `get_chat_model()` 统一实例化模型，便于未来扩展模型路由

3. **提示词独立管理**：将 PromptTemplate 放在 `app/prompts/` 目录，便于非开发人员修改

4. **业务逻辑封装**：`app/workflows/` 中使用 LCEL 组装 `Runnable` 对象，这是 LangServe 暴露的核心单元

5. **路由极简原则**：`app/api/routes.py` 只负责调用 `add_routes` 将 workflows 暴露为 HTTP 接口

## LangServe 接口规范

### 挂载链路
```python
from langserve import add_routes

add_routes(
    app,
    chain,  # Runnable 对象
    path="/chat/endpoint"
)
```

### 标准请求格式
```json
{
  "input": {
    "参数名": "值"
  },
  "config": {
    "temperature": 0.7
  }
}
```

### LangServe 自动生成的端点
- `POST /path` - 标准 invoke 调用
- `POST /path/invoke` - 直接调用
- `POST /path/batch` - 批量调用
- `POST /path/stream` - 流式输出
- `GET /path/config` - 获取配置
- `GET /path/playground/{trace_id}` - 获取追踪信息

## OpenAPI 文档

OpenAPI 规范文件存放在 `OpenAPI/` 目录，使用中文描述接口定义。

## doc 项目开发文档

项目的开发设计文档放在 `doc/` 目录，使用中文md文档描述了本项目的设计。

## 工作流类型

### LCEL (LangChain Expression Language)
位于 `app/workflows/lcel/`，用于构建简单的线性链路：
```python
chain = prompt | model | StrOutputParser()
```

### LangGraph
位于 `app/workflows/graph/`，用于构建复杂的多步骤、有状态的应用（目前为预留目录）。

## 环境变量示例

```bash
OPENAI_API_KEY="sk-xxx"
OPENAI_API_BASE="https://api.openai.com/v1"
MODEL_NAME="gpt-4"
```
