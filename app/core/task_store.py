"""
内存任务状态存储

提供简单的内存任务状态管理，用于 MVP 阶段的异步任务追踪
"""
from typing import Optional, Dict, Any
from datetime import datetime
from app.schemas.distillation import DistillationResult


class TaskStore:
    """内存任务存储"""

    def __init__(self):
        """初始化任务存储"""
        self._tasks: Dict[str, Dict[str, Any]] = {}

    def create_task(
        self,
        task_id: str,
        article_id: str,
        callback_url: Optional[str] = None
    ) -> None:
        """
        创建新任务

        Args:
            task_id: 任务唯一标识符
            article_id: 文章ID
            callback_url: 回调URL
        """
        self._tasks[task_id] = {
            "task_id": task_id,
            "article_id": article_id,
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "callback_url": callback_url,
            "error_message": None,
            "result": None
        }

    def update_status(
        self,
        task_id: str,
        status: str,
        error_message: Optional[str] = None,
        result: Optional[DistillationResult] = None
    ) -> None:
        """
        更新任务状态

        Args:
            task_id: 任务唯一标识符
            status: 新状态 (pending/processing/completed/failed)
            error_message: 错误信息（如果有）
            result: 蒸馏结果（完成时）
        """
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")

        self._tasks[task_id]["status"] = status
        self._tasks[task_id]["updated_at"] = datetime.now()

        if error_message:
            self._tasks[task_id]["error_message"] = error_message

        if result:
            self._tasks[task_id]["result"] = result

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息

        Args:
            task_id: 任务唯一标识符

        Returns:
            任务信息字典，如果任务不存在则返回 None
        """
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有任务

        Returns:
            所有任务的字典
        """
        return self._tasks.copy()

    def delete_task(self, task_id: str) -> None:
        """
        删除任务

        Args:
            task_id: 任务唯一标识符
        """
        if task_id in self._tasks:
            del self._tasks[task_id]

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        清理旧任务（超过指定小时数的已完成或失败任务）

        Args:
            max_age_hours: 任务最大保留小时数

        Returns:
            清理的任务数量
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        tasks_to_delete = []

        for task_id, task in self._tasks.items():
            if task["status"] in ["completed", "failed"]:
                if task["updated_at"] < cutoff_time:
                    tasks_to_delete.append(task_id)

        for task_id in tasks_to_delete:
            self.delete_task(task_id)

        return len(tasks_to_delete)


# 全局单例实例
task_store = TaskStore()


# 便捷函数
def create_task(
    task_id: str,
    article_id: str,
    callback_url: Optional[str] = None
) -> None:
    """创建新任务"""
    task_store.create_task(task_id, article_id, callback_url)


def update_task_status(
    task_id: str,
    status: str,
    error_message: Optional[str] = None,
    result: Optional[DistillationResult] = None
) -> None:
    """更新任务状态"""
    task_store.update_status(task_id, status, error_message, result)


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """获取任务状态"""
    return task_store.get_task(task_id)
