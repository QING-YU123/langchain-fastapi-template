#!/usr/bin/env python
from fastapi import FastAPI
import uvicorn

# 从你的其他模块导入组装好的链路和配置
# from app.core.config import settings
from app.api.routes import setup_routes

def create_app() -> FastAPI:
    app = FastAPI(
        title="LangChain Server",
        version="1.0",
        description="A modular api server using Langchain's Runnable interfaces",
    )

    # 挂载 LangServe 路由
    setup_routes(app)
    
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)