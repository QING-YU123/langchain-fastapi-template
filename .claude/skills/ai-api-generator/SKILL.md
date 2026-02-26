# AI API Generator Skill

基于 LangChain + FastAPI 架构的 AI 相关 API 生成技能，适用于构建 LLM 驱动的后端服务。

## 核心原则

- **遵循项目现有架构**：所有代码应符合项目的 DDD 分层结构和编码风格
- **无需编写测试**：专注于功能实现，不包含单元测试或集成测试
- **新模块需用户同意**：引入新的依赖或技术栈前，必须获得用户明确许可
- **两阶段工作流**：Plan（规划）→ Agent（执行）确保需求清晰

## 执行流程

### Phase 1: Plan - 需求理解与规划

在进入编写代码前，必须完成以下步骤：

#### 1.1 学习项目风格

阅读以下关键文件，理解项目的架构模式和编码约定：

```
app/
├── core/config.py          # Pydantic Settings 配置管理模式
├── llms/builder.py         # 模型工厂模式
├── prompts/                # Prompt 模板管理方式
├── schemas/                # Pydantic 数据模型定义风格
├── workflows/              # LCEL/LangGraph 链路组织方式
├── services/               # 业务逻辑封装模式
├── utils/                  # 工具函数编写方式
└── api/routes.py           # 路由注册和 FastAPI 使用模式
```

**学习要点**：
- 配置如何通过环境变量管理
- LLM 如何实例化和配置
- Prompt 如何与代码分离
- 数据模型如何定义和验证
- 链路如何组装和复用
- 异步任务如何处理
- 路由如何注册和暴露

#### 1.2 理解用户请求

向用户提出以下关键问题，明确需求：

**功能相关**：
1. API 的核心功能是什么？输入什么，输出什么？
2. 是否需要异步处理？是否需要 Webhook 回调？
3. 是否需要状态追踪？是否需要任务队列？
4. 涉及哪些 LLM 操作（文本生成、摘要、提取、对话等）？
5. 是否需要长文本处理？文本切片策略如何？

**技术相关**：
6. 是否需要新的配置项？
7. 是否需要新的工具函数？
8. 是否需要新的数据模型？
9. 是否需要引入新的依赖（如新的 LangChain 组件、数据库等）？

**边界相关**：
10. 哪些功能是 MVP 核心必须实现的？
11. 哪些功能可以延后到 Phase 2？

#### 1.3 制定实施大纲

基于收集的信息，制定清晰的实施计划，包括：

- 文件清单（新增/修改）
- 每个文件的职责
- 数据流设计
- 错误处理策略

**示例大纲**：
```
新增文件：
- app/schemas/xxx.py          # 请求数据模型
- app/prompts/xxx_prompts.py  # Prompt 模板
- app/workflows/lcel/xxx.py   # LCEL 链路
- app/services/xxx.py         # 业务逻辑服务
- app/utils/xxx.py            # 工具函数

修改文件：
- app/core/config.py          # 添加配置项
- app/api/routes.py           # 注册路由
```

获得用户确认后，进入 Agent 阶段。

---

### Phase 2: Agent - 代码实现

#### 2.1 分层架构指南

按照以下分层顺序编写代码，确保依赖方向正确：

```
┌─────────────────────────────────────────┐
│         API Layer (routes)              │  ← 最上层
│  - 路由注册                              │
│  - 请求验证                              │
│  - 响应格式化                            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Service Layer (services)           │
│  - 业务流程编排                          │
│  - 异步任务管理                          │
│  - 错误处理和重试                        │
│  - Webhook 回调                          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│     Workflow Layer (workflows)          │
│  - LCEL 链路组装                         │
│  - LangGraph 状态图（如需要）            │
│  - Prompt 与模型的集成                   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   Supporting Layers (prompts/utils)     │  ← 最底层
│  - Prompt 模板定义                       │
│  - 工具函数                              │
└─────────────────────────────────────────┘
```

#### 2.2 各层实现指南

##### 2.2.1 数据模型层 (`app/schemas/`)

**职责**：定义所有输入输出的数据结构

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

class RequestModel(BaseModel):
    """请求模型"""
    # 字段定义...

class ResponseModel(BaseModel):
    """响应模型"""
    # 字段定义...
```

**关键实践**：
- 使用 Pydantic 进行类型验证
- 添加 Field 描述文档
- 区分必需和可选字段
- 使用合理的默认值

##### 2.2.2 配置层 (`app/core/config.py`)

**职责**：集中管理环境变量配置

```python
class Settings(BaseSettings):
    # 现有配置...

    # 新增配置
    new_feature_enabled: bool = True
    new_feature_timeout: int = 600

    class Config:
        env_file = ".env"
        extra = "ignore"
```

**关键实践**：
- 提供合理的默认值
- 添加配置说明注释
- 遵循命名约定

##### 2.2.3 提示词层 (`app/prompts/`)

**职责**：管理 AI 交互的 Prompt 模板

```python
from langchain_core.prompts import ChatPromptTemplate

feature_prompt = ChatPromptTemplate.from_messages([
    ("system", "系统角色定义..."),
    ("user", "用户指令：{input_var}")
])

def get_feature_prompt():
    return feature_prompt
```

**关键实践**：
- Prompt 与代码分离
- 使用模板变量实现动态性
- 提供清晰的系统角色定义
- 定义明确的输出格式要求

**注意事项**：
- 避免在示例中使用 `{变量}` 格式，会被误认为模板变量
- 使用文字描述替代 JSON 示例

##### 2.2.4 工具层 (`app/utils/`)

**职责**：提供可复用的工具函数

```python
class UtilityClass:
    @staticmethod
    def process_data(input_data):
        # 处理逻辑
        pass

# 便捷函数
def utility_function(input_data):
    return UtilityClass.process_data(input_data)
```

**关键实践**：
- 保持函数纯粹，无副作用
- 添加清晰的文档字符串
- 处理边界情况

##### 2.2.5 工作流层 (`app/workflows/`)

**职责**：组装 LCEL 链路，实现核心 AI 处理逻辑

```python
import logging
from typing import Dict, Any
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class FeatureChain:
    def __init__(self):
        self.model = get_chat_model()
        self.str_parser = StrOutputParser()
        self._build_chains()

    def _build_chains(self):
        # 组装链路
        self.chain = (
            get_feature_prompt()
            | self.model
            | self.str_parser
        )

    async def process(self, input_data: str) -> Dict[str, Any]:
        # 核心处理逻辑
        result = await self.chain.ainvoke({"input_var": input_data})
        return {"result": result}

async def feature_wrapper(input_data: str) -> Dict[str, Any]:
    chain = FeatureChain()
    return await chain.process(input_data)
```

**关键实践**：
- 使用类封装相关链路
- 添加详细的日志记录
- 实现异步方法
- 添加重试和错误处理
- 考虑 API 速率限制，添加请求间延迟

**错误处理模式**：
```python
async def _invoke_with_retry(self, chain, input_data: Dict[str, Any]):
    last_error = None
    delay = 2.0

    for attempt in range(3):
        try:
            return await chain.ainvoke(input_data)
        except RateLimitError:
            await asyncio.sleep(delay)
            delay *= 2

    raise last_error
```

##### 2.2.6 服务层 (`app/services/`)

**职责**：业务流程编排，处理异步任务和外部通知

```python
import logging
from app.core.task_store import update_task_status

logger = logging.getLogger(__name__)

async def process_task(task_id: str, input_data: Any, callback_url: str = None):
    try:
        update_task_status(task_id, "processing")

        # 调用工作流
        result = await feature_chain.process(input_data)

        update_task_status(task_id, "completed", result=result)

        # Webhook 回调
        if callback_url:
            await send_webhook(callback_url, result)

    except Exception as e:
        update_task_status(task_id, "failed", error_message=str(e))
        await handle_failure(task_id, callback_url, str(e))
```

**关键实践**：
- 异常处理要全面
- 状态更新要及时
- Webhook 失败不影响任务状态
- 使用结构化日志

##### 2.2.7 状态存储 (`app/core/task_store.py`)

**职责**：管理异步任务状态（如需要）

```python
class TaskStore:
    def __init__(self):
        self._tasks: Dict[str, Dict] = {}

    def create_task(self, task_id: str, ...):
        self._tasks[task_id] = {...}

    def update_status(self, task_id: str, status: str, ...):
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")
        self._tasks[task_id]["status"] = status

# 全局实例和便捷函数
task_store = TaskStore()

def create_task(...): task_store.create_task(...)
def update_task_status(...): task_store.update_status(...)
```

**关键实践**：
- 提供全局单例
- 提供便捷函数
- 线程安全考虑
- 实现清理机制

##### 2.2.8 路由层 (`app/api/routes.py`)

**职责**：注册 FastAPI 路由，处理 HTTP 请求响应

```python
from fastapi import FastAPI, BackgroundTasks, HTTPException
from app.schemas.xxx import RequestModel, TaskResponse
from app.services.xxx import process_task
from app.core.task_store import create_task

def setup_routes(app: FastAPI):
    @app.post("/api/feature", response_model=TaskResponse, status_code=202)
    async def create_feature_task(
        request: RequestModel,
        background_tasks: BackgroundTasks
    ):
        task_id = str(uuid4())

        # 先创建任务记录
        create_task(task_id, ...)

        # 添加后台任务
        background_tasks.add_task(
            process_task,
            task_id=task_id,
            ...
        )

        return TaskResponse(task_id=task_id, status="pending")

    @app.get("/api/feature/{task_id}")
    async def get_feature_status(task_id: str):
        task_info = get_task_status(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")
        return task_info
```

**关键实践**：
- 返回 202 Accepted 给异步任务
- 先创建任务记录再启动后台任务
- 提供状态查询端点
- 添加详细的 API 文档字符串

#### 2.3 通用技术模式

##### 异步任务模式

```python
# 1. 创建端点
@app.post("/api/task", status_code=202)
async def create_task(..., background_tasks: BackgroundTasks):
    task_id = str(uuid4())
    create_task(task_id, ...)  # 先创建记录
    background_tasks.add_task(process_task, task_id=task_id, ...)
    return {"task_id": task_id, "status": "pending"}

# 2. 处理函数
async def process_task(task_id: str, ...):
    try:
        update_task_status(task_id, "processing")
        result = await do_work(...)
        update_task_status(task_id, "completed", result=result)
    except Exception as e:
        update_task_status(task_id, "failed", error_message=str(e))

# 3. 查询端点
@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    task = task_store.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    return task
```

##### 长文本处理模式

```python
# 1. 文本切片
chunks = text_splitter.split_text(long_content)

# 2. 迭代处理
current_result = await process_first_chunk(chunks[0])
for chunk in chunks[1:]:
    await asyncio.sleep(1.0)  # 避免速率限制
    current_result = await process_with_retry(
        refine_chain,
        {"existing": current_result, "new": chunk}
    )
```

##### 错误处理模式

```python
# 1. 工作流层：可恢复的错误
try:
    result = await chain.ainvoke(input_data)
except RateLimitError:
    # 重试或使用默认值
    return default_value
except Exception as e:
    logger.error(f"处理失败: {e}")
    raise

# 2. 服务层：任务失败不影响状态
try:
    result = await workflow.process(data)
except Exception as e:
    update_task_status(task_id, "failed", error_message=str(e))
    # 继续执行，不重新抛出异常
```

#### 2.4 编码规范

**注释**
文档字符串（Docstrings）

文档字符串是一种特殊的注释，它们出现在模块、函数、类或方法定义的第一行，用三个双引号包围。这些字符串可以通过对象的 __doc__ 属性访问，并且可以被自动化工具用于生成文档。

```python
def fetch_data(source):
"""
从指定数据源获取数据。
Args:
source (str): 数据源的名称或路径。
Returns:
list: 包含数据的列表。
"""
```

实现细节：文档字符串应该简洁明了，提供关于函数或方法的必要信息，包括参数、返回值和可能抛出的异常。

**命名约定**：
- 类名：`PascalCase`（如 `DistillationChain`）
- 函数/变量：`snake_case`（如 `distill_article`）
- 私有方法：`_leading_underscore`（如 `_build_chains`）
- 常量：`UPPER_SNAKE_CASE`（如 `MAX_RETRIES`）

**文档字符串**：
```python
def function(param: type) -> return_type:
    """
    简短描述

    Args:
        param: 参数描述

    Returns:
        返回值描述

    Raises:
        Exception: 异常描述

    注意：
        - 附加说明1
        - 附加说明2
    """
```

**导入顺序**：
1. 标准库
2. 第三方库
3. 本地模块

```python
import asyncio
import logging
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from openai import RateLimitError

from app.core.config import settings
from app.llms.builder import get_chat_model
```

## 文件检查清单

完成实现后，确保以下内容：

- [ ] 所有新增文件符合项目目录结构
- [ ] 配置项已添加到 `config.py`
- [ ] Prompt 模板与代码分离
- [ ] 数据模型使用 Pydantic 验证
- [ ] 工作流使用异步方法
- [ ] 错误处理完善
- [ ] 日志记录清晰
- [ ] 路由注册完整
- [ ] 任务状态管理正确（如需要）
- [ ] 速率限制处理（如涉及 API 调用）
- [ ] 无测试代码

## 依赖管理

如需引入新的 Python 包，必须先获得用户许可。常见新增依赖：

- **文本处理**：`langchain-text-splitters`
- **HTTP 客户端**：`httpx`
- **数据验证**：`pydantic`, `pydantic-settings`
- **任务队列**：`celery`, `redis`（需要明确同意）


## 注意事项

1. **不编写测试**：本 skill 专注于功能实现
2. **遵循现有风格**：保持与项目现有代码一致
3. **模块化设计**：每个文件职责单一，易于维护
4. **错误容错**：核心失败不影响服务运行
5. **日志完善**：便于调试和监控
6. **文档清晰**：代码即文档，通过注释说明意图

## 快速参考

| 层级 | 目录 | 职责 | 主要技术 |
|------|------|------|----------|
| API | `app/api/` | 路由注册 | FastAPI, BackgroundTasks |
| Service | `app/services/` | 业务编排 | asyncio, httpx |
| Workflow | `app/workflows/` | AI 链路 | LangChain LCEL, LangGraph |
| Schema | `app/schemas/` | 数据模型 | Pydantic |
| Prompt | `app/prompts/` | 提示词 | ChatPromptTemplate |
| Core | `app/core/` | 配置/状态 | BaseSettings, TaskStore |
| Utils | `app/utils/` | 工具函数 | 纯 Python |
| LLMs | `app/llms/` | 模型工厂 | ChatOpenAI |
