from fastapi import FastAPI
from langserve import add_routes
from app.workflows.lcel.basic_chat import simple_chat_chain
# from app.workflows.graph.agent_graph import complex_agent_app

def setup_routes(app: FastAPI):
    # 基础健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "message": "LangServe is running."}

    # 挂载 LCEL 链路 (输入一个 topic 字符串)
    add_routes(
        app,
        simple_chat_chain,
        path="/chat/simple",
    )

    # 2. 挂载复杂的 Agent 服务
    # add_routes(
    #     app,
    #     complex_agent_app, # 编译后的 Graph 同样是一个 Runnable
    #     path="/chat/agent",
    # )