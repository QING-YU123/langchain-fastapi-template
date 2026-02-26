
运行指令：uvicorn app.main:app --reload --host localhost --port 8000


### 文件夹架构设计

本项目按照领域驱动设计（DDD）或分层架构的思路来组织目录：

```text
my_langserve_app/
├── app/                        # 应用主代码库
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口点 (包含 app 初始化和 uvicorn 运行)
│   ├── api/                    # 接口层 (Controllers)
│   │   ├── __init__.py
│   │   ├── routes.py           # 集中管理所有的 LangServe 路由注册逻辑
│   │   └── dependencies.py     # FastAPI 依赖注入 (如鉴权、数据库连接)
│   ├── chains/                 # 服务层 (Services/Runnables)
│   │   ├── __init__.py
│   │   └── chat_chain.py       # 组装 Prompt + Model + OutputParser 的具体业务链
│   ├── llms/                   # 模型层
│   │   ├── __init__.py
│   │   └── builder.py          # 负责统一实例化模型对象 (如 ChatOpenAI, ChatAnthropic)
│   ├── prompts/                # 提示词层
│   │   ├── __init__.py
│   │   └── chat_prompts.py     # 存放各类 PromptTemplate 模板
│   ├── schemas/                # 数据定义层 (DTOs)
│   │   ├── __init__.py
│   │   └── types.py            # Pydantic 模型，用于定义输入输出的数据结构验证
│   └── core/                   # 核心配置层
│       ├── __init__.py
│       └── config.py           # 环境变量加载、全局配置 (替代零散的 load_dotenv)
├── .env                        # 环境变量文件
├── requirements.txt            # 项目依赖
└── README.md

```

### 架构中各模块的职责划分

1. **`app/core/config.py` (配置管理)**：不要在 `main.py` 里直接调 `load_dotenv()` 和 `os.getenv()`。建议使用 Pydantic 的 `BaseSettings` 来集中管理所有的环境变量，这样自带类型推导和缺失报错。
2. **`app/prompts/` (提示词工程)**：提示词是大模型应用的核心资产。将其独立出来，可以让非开发人员（如产品经理或提示词工程师）更容易参与修改，而不会破坏代码逻辑。
3. **`app/llms/` (模型工厂)**：集中管理模型的初始化。如果未来需要实现“模型路由”（根据任务动态选择用 GPT-4 还是开源模型），只需在这个文件夹里修改逻辑即可。
4. **`app/chains/` (业务逻辑链)**：这里使用 LangChain 的表达式语言 (LCEL) 将 Prompt 和 Model 组装成 `Runnable` 对象。LangServe 真正暴露的就是这些 `Runnable`。
5. **`app/api/` (路由与接口)**：调用 `add_routes` 的地方。保持这里的极简，只负责将 `chains` 暴露为 HTTP 接口。

---