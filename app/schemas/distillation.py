"""
蒸馏服务数据模型

定义知识蒸馏相关的请求、响应和结果数据结构
"""
from typing import Optional, List, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class DistillationRequest(BaseModel):
    """蒸馏任务请求模型"""
    article_id: UUID = Field(..., description="文章唯一标识符")
    content: str = Field(..., min_length=1, description="需要蒸馏的长文本内容")
    callback_url: Optional[str] = Field(None, description="回调URL，处理完成后通知")
    metadata: Optional[Dict] = Field(default_factory=dict, description="额外的元数据信息")


class CoreConcepts(BaseModel):
    """核心概念和术语提取结果"""
    concepts: List[str] = Field(default_factory=list, description="核心概念列表")
    terms: List[Dict[str, str]] = Field(default_factory=list, description="关键术语及定义")


class DistillationResult(BaseModel):
    """蒸馏结果模型"""
    article_id: UUID = Field(..., description="文章唯一标识符")
    core_summary: str = Field(..., description="脱水后的逻辑骨架")
    difficulty_level: int = Field(..., ge=1, le=5, description="难度等级（1-5）")
    estimated_read_min: int = Field(..., ge=0, description="预估阅读时间（分钟）")
    core_concepts: CoreConcepts = Field(default_factory=CoreConcepts, description="核心概念和术语")
    processed_at: datetime = Field(default_factory=datetime.now, description="处理时间戳")


class TaskResponse(BaseModel):
    """任务提交响应模型"""
    task_id: str = Field(..., description="任务唯一标识符")
    status: str = Field(..., description="任务状态：pending/processing/completed/failed")
    message: str = Field(..., description="状态消息")


class TaskStatus(BaseModel):
    """任务状态查询响应"""
    task_id: str = Field(..., description="任务唯一标识符")
    status: str = Field(..., description="任务状态")
    article_id: Optional[str] = Field(None, description="关联的文章ID")
    created_at: datetime = Field(..., description="任务创建时间")
    updated_at: datetime = Field(..., description="任务最后更新时间")
    error_message: Optional[str] = Field(None, description="错误信息（如果有）")
    result: Optional[DistillationResult] = Field(None, description="蒸馏结果（完成时）")
