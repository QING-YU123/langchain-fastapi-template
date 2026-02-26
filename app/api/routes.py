from fastapi import FastAPI, BackgroundTasks, HTTPException
from typing import Optional
from uuid import uuid4
from langserve import add_routes
from app.workflows.lcel.basic_chat import simple_chat_chain
from app.schemas.distillation import DistillationRequest, TaskResponse
from app.services.distillation_service import process_distillation_task, DistillationService
from app.core.task_store import get_task_status, create_task
# from app.workflows.graph.agent_graph import complex_agent_app


def setup_routes(app: FastAPI):
    # 基础健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "message": "LangServe is running."}

    # ==================== 蒸馏服务端点 ====================

    @app.post("/ai/distill", response_model=TaskResponse, status_code=202)
    async def create_distillation_task(
        request: DistillationRequest,
        background_tasks: BackgroundTasks
    ):
        """
        创建知识蒸馏任务

        提交长文本进行 AI 知识蒸馏，返回 202 Accepted 表示任务已接收。

        **请求参数**：
        - article_id: 文章唯一标识符（UUID）
        - content: 待蒸馏的长文本内容
        - callback_url: 可选的回调 URL，完成后会通知此地址

        **返回**：
        - task_id: 任务唯一标识符
        - status: 任务状态（pending）
        - message: 状态消息

        **处理流程**：
        1. 接收请求后立即返回 202 Accepted
        2. 在后台异步执行蒸馏任务
        3. 完成后通过 Webhook 回调通知结果
        """
        task_id = str(uuid4())

        # 先在 task_store 中创建任务记录
        create_task(
            task_id=task_id,
            article_id=str(request.article_id),
            callback_url=request.callback_url
        )

        # 添加后台任务
        background_tasks.add_task(
            process_distillation_task,
            task_id=task_id,
            article_id=str(request.article_id),
            content=request.content,
            callback_url=request.callback_url
        )

        return TaskResponse(
            task_id=task_id,
            status="pending",
            message="蒸馏任务已创建，正在后台处理"
        )

    @app.get("/ai/distill/{task_id}")
    async def get_distillation_task_status(task_id: str):
        """
        查询蒸馏任务状态

        **路径参数**：
        - task_id: 任务唯一标识符

        **返回**：
        - task_id: 任务唯一标识符
        - status: 任务状态（pending/processing/completed/failed）
        - article_id: 关联的文章ID
        - created_at: 任务创建时间
        - updated_at: 任务最后更新时间
        - error_message: 错误信息（如果有）
        - result: 蒸馏结果（完成时）

        **状态说明**：
        - pending: 任务已创建，等待处理
        - processing: 任务正在处理中
        - completed: 任务已完成，result 字段包含蒸馏结果
        - failed: 任务失败，error_message 字段包含错误信息
        """
        task_info = await DistillationService.get_task_info(task_id)

        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")

        return task_info

    # ==================== LangServe 链路挂载 ====================

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