"""
蒸馏服务层

实现异步任务编排、Webhook 回调和错误处理等业务逻辑
"""
import asyncio
import logging
from typing import Optional
from uuid import UUID
import httpx
from app.core.config import settings
from app.core.task_store import update_task_status, get_task_status
from app.workflows.lcel.distillation_chain import distill_article
from app.schemas.distillation import DistillationResult, CoreConcepts


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebhookClient:
    """Webhook 回调客户端"""

    def __init__(self, callback_url: Optional[str] = None):
        """
        初始化 Webhook 客户端

        Args:
            callback_url: 回调 URL，如果为 None 则使用默认配置
        """
        self.callback_url = callback_url or settings.default_webhook_url
        self.timeout = settings.webhook_timeout

    async def send_distillation_result(self, result: DistillationResult) -> bool:
        """
        发送蒸馏结果到 Webhook

        Args:
            result: 蒸馏结果对象

        Returns:
            bool: 发送是否成功

        注意：
        - 使用 httpx 异步客户端
        - 设置超时防止长时间阻塞
        - 失败时记录日志但不影响任务完成状态
        """
        if not self.callback_url:
            logger.warning("Webhook URL 未配置，跳过回调")
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.callback_url,
                    json=result.model_dump(mode='json'),
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code in [200, 201, 202, 204]:
                    logger.info(f"Webhook 回调成功: {self.callback_url}")
                    return True
                else:
                    logger.error(
                        f"Webhook 回调失败: {response.status_code} - "
                        f"{response.text}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error(f"Webhook 回调超时: {self.callback_url}")
            return False

        except httpx.HTTPError as e:
            logger.error(f"Webhook 回调 HTTP 错误: {e}")
            return False

        except Exception as e:
            logger.error(f"Webhook 回调未知错误: {e}")
            return False


async def process_distillation_task(
    task_id: str,
    article_id: str,
    content: str,
    callback_url: Optional[str] = None
) -> None:
    """
    处理蒸馏任务的主函数

    Args:
        task_id: 任务唯一标识符
        article_id: 文章唯一标识符
        content: 待蒸馏的文本内容
        callback_url: 回调 URL（可选）

    执行流程：
    1. 更新任务状态为 processing
    2. 执行蒸馏处理
    3. 更新任务状态为 completed
    4. 发送 Webhook 回调
    5. 处理过程中的任何错误
    """
    try:
        # 1. 更新状态为处理中
        update_task_status(task_id, "processing")
        logger.info(f"开始处理蒸馏任务: {task_id}")

        # 2. 执行蒸馏
        result_data = await distill_article(content)

        # 3. 构建结果对象
        result = DistillationResult(
            article_id=UUID(article_id),
            core_summary=result_data["core_summary"],
            difficulty_level=result_data["difficulty_level"],
            estimated_read_min=result_data["estimated_read_min"],
            core_concepts=CoreConcepts(**result_data["core_concepts"])
        )

        # 4. 更新任务状态为完成
        update_task_status(
            task_id,
            "completed",
            result=result
        )
        logger.info(f"蒸馏任务完成: {task_id}")

        # 5. 发送 Webhook 回调
        webhook_client = WebhookClient(callback_url)
        await webhook_client.send_distillation_result(result)

    except ValueError as e:
        # 处理输入验证错误
        error_msg = f"输入验证失败: {str(e)}"
        logger.error(f"蒸馏任务失败 ({task_id}): {error_msg}")
        update_task_status(task_id, "failed", error_message=error_msg)
        await handle_failure(task_id, article_id, callback_url, error_msg)

    except asyncio.TimeoutError:
        # 处理超时错误
        error_msg = f"处理超时（超过 {settings.task_timeout} 秒）"
        logger.error(f"蒸馏任务超时 ({task_id})")
        update_task_status(task_id, "failed", error_message=error_msg)
        await handle_failure(task_id, article_id, callback_url, error_msg)

    except Exception as e:
        # 处理其他未预期的错误
        error_msg = f"未知错误: {str(e)}"
        logger.exception(f"蒸馏任务异常 ({task_id})")
        update_task_status(task_id, "failed", error_message=error_msg)
        await handle_failure(task_id, article_id, callback_url, error_msg)


async def handle_failure(
    task_id: str,
    article_id: str,
    callback_url: Optional[str],
    error_message: str
) -> None:
    """
    处理任务失败，尝试通知调用方

    Args:
        task_id: 任务唯一标识符
        article_id: 文章唯一标识符
        callback_url: 回调 URL（可选）
        error_message: 错误消息
    """
    if not callback_url:
        return

    try:
        async with httpx.AsyncClient(timeout=settings.webhook_timeout) as client:
            # 发送失败通知
            failure_payload = {
                "article_id": article_id,
                "task_id": task_id,
                "status": "failed",
                "error": error_message
            }

            await client.post(
                callback_url,
                json=failure_payload,
                headers={"Content-Type": "application/json"}
            )

            logger.info(f"已发送失败通知到: {callback_url}")

    except Exception as e:
        # 失败通知本身失败，只记录日志
        logger.error(f"发送失败通知时出错: {e}")


class DistillationService:
    """蒸馏服务类（提供更高层次的封装）"""

    @staticmethod
    async def submit_task(
        task_id: str,
        article_id: str,
        content: str,
        callback_url: Optional[str] = None
    ) -> dict:
        """
        提交蒸馏任务

        Args:
            task_id: 任务唯一标识符
            article_id: 文章唯一标识符
            content: 待蒸馏的文本内容
            callback_url: 回调 URL（可选）

        Returns:
            dict: 任务提交响应
        """
        # 验证输入
        if not content or not content.strip():
            raise ValueError("内容不能为空")

        if len(content) < 50:
            raise ValueError("内容过短，无法进行有效蒸馏")

        # 返回任务信息（任务已在后台启动）
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "蒸馏任务已创建，正在后台处理"
        }

    @staticmethod
    async def get_task_info(task_id: str) -> Optional[dict]:
        """
        获取任务信息

        Args:
            task_id: 任务唯一标识符

        Returns:
            Optional[dict]: 任务信息字典，任务不存在时返回 None
        """
        task_info = get_task_status(task_id)

        if not task_info:
            return None

        # 转换为适合 API 返回的格式
        return {
            "task_id": task_info["task_id"],
            "status": task_info["status"],
            "article_id": task_info.get("article_id"),
            "created_at": task_info["created_at"].isoformat(),
            "updated_at": task_info["updated_at"].isoformat(),
            "error_message": task_info.get("error_message"),
            "result": task_info.get("result")
        }
