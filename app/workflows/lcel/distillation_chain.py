"""
蒸馏链路实现

实现核心的 Refine 模式文本蒸馏链路，包括逻辑骨架提取、难度评估等功能
"""
import asyncio
import logging
import json
import re
from typing import Dict, Any
from langchain_core.output_parsers import StrOutputParser
from openai import RateLimitError
from app.llms.builder import get_chat_model
from app.prompts.distillation_prompts import (
    get_summary_initial_prompt,
    get_summary_refine_prompt,
    get_difficulty_assessment_prompt,
    get_concepts_extraction_prompt
)
from app.utils.text_splitter import split_text_for_distillation
from app.core.config import settings


# 配置日志
logger = logging.getLogger(__name__)


class DistillationChain:
    """蒸馏链路核心类"""

    def __init__(self):
        """初始化蒸馏链路"""
        self.model = get_chat_model()
        self.str_parser = StrOutputParser()

        # 初始化各个子链路
        self._initial_chain = None
        self._refine_chain = None
        self._difficulty_chain = None
        self._concepts_chain = None
        self._build_chains()

    def _build_chains(self) -> None:
        """构建所有需要的链路"""
        # 初始摘要链路
        self._initial_chain = (
            get_summary_initial_prompt()
            | self.model
            | self.str_parser
        )

        # 迭代优化链路
        self._refine_chain = (
            get_summary_refine_prompt()
            | self.model
            | self.str_parser
        )

        # 难度评估链路
        self._difficulty_chain = (
            get_difficulty_assessment_prompt()
            | self.model
            | self.str_parser
        )

        # 概念提取链路
        self._concepts_chain = (
            get_concepts_extraction_prompt()
            | self.model
            | self.str_parser
        )

    async def distill_article(self, content: str) -> Dict[str, Any]:
        """
        执行完整的文章蒸馏流程

        Args:
            content: 待蒸馏的长文本内容

        Returns:
            Dict[str, Any]: 包含以下字段的字典
                - core_summary: 脱水后的逻辑骨架
                - difficulty_level: 难度等级（1-5）
                - estimated_read_min: 预估阅读时间（分钟）
                - core_concepts: 核心概念和术语（Phase 2）
        """
        logger.info(f"开始蒸馏文章，内容长度: {len(content)} 字符")

        # 1. 文本切片
        chunks = split_text_for_distillation(content)
        logger.info(f"文本切分为 {len(chunks)} 个片段")

        if not chunks:
            raise ValueError("文本内容为空或切片失败")

        # 2. Refine 迭代提取摘要（核心步骤）
        logger.info("开始 Refine 迭代提取摘要...")
        core_summary = await self._refine_summary(chunks)
        logger.info(f"摘要提取完成，长度: {len(core_summary)} 字符")

        # 3. 评估难度等级（可选步骤，失败不影响主流程）
        try:
            difficulty_level = await self._assess_difficulty(core_summary)
            logger.info(f"难度评估完成: {difficulty_level}")
        except Exception as e:
            logger.warning(f"难度评估失败，使用默认值: {e}")
            difficulty_level = 3  # 默认中等难度

        # 4. 计算预估阅读时间
        estimated_read_min = self._estimate_read_time(content)

        # 5. 提取核心概念和术语（可选步骤，失败不影响主流程）
        try:
            logger.info("开始提取核心概念和术语...")
            core_concepts = await self._extract_concepts(core_summary, content)
            logger.info(f"概念提取完成: {len(core_concepts.get('concepts', []))} 个概念, {len(core_concepts.get('terms', []))} 个术语")
        except Exception as e:
            logger.warning(f"概念提取失败，使用空结构: {e}")
            core_concepts = {
                "concepts": [],
                "terms": []
            }

        logger.info("文章蒸馏完成")

        return {
            "core_summary": core_summary,
            "difficulty_level": difficulty_level,
            "estimated_read_min": estimated_read_min,
            "core_concepts": core_concepts
        }

    async def _refine_summary(self, chunks: list) -> str:
        """
        使用 Refine 模式迭代提取摘要

        Args:
            chunks: 切片后的文本片段列表

        Returns:
            str: 最终的蒸馏摘要

        注意：
        - 第一块使用初始提示词
        - 后续块使用迭代提示词，逐步整合新信息
        - 限制最大迭代次数防止超时
        - 添加请求间延迟以避免速率限制
        """
        if not chunks:
            return ""

        # 处理第一个片段
        try:
            current_summary = await self._initial_chain.ainvoke({"chunk": chunks[0]})
            await asyncio.sleep(settings.api_request_delay)
        except Exception as e:
            logger.error(f"初始摘要生成失败: {e}")
            raise

        # 迭代处理后续片段
        max_iterations = min(len(chunks[1:]), settings.max_refine_iterations)

        for i, chunk in enumerate(chunks[1:max_iterations + 1], 1):
            try:
                current_summary = await self._invoke_with_retry(
                    self._refine_chain,
                    {
                        "existing_summary": current_summary,
                        "chunk": chunk
                    }
                )

                # 进度追踪（每处理 5 个片段记录一次）
                if i % 5 == 0:
                    logger.info(f"Refine 迭代进度: {i}/{max_iterations}")

                # 请求间延迟，避免速率限制
                await asyncio.sleep(settings.api_request_delay)

            except Exception as e:
                # 迭代失败时记录并返回当前已生成的摘要
                logger.warning(f"Refine 迭代在片段 {i} 处失败: {e}，使用当前已生成摘要")
                break

        return current_summary.strip()

    async def _invoke_with_retry(self, chain, input_data: Dict[str, Any]) -> str:
        """
        带重试的链路调用，用于处理速率限制错误

        Args:
            chain: LangChain 链路
            input_data: 输入数据

        Returns:
            str: 链路输出结果

        Raises:
            Exception: 重试次数耗尽后抛出原始异常
        """
        last_error = None
        delay = settings.initial_retry_delay

        for attempt in range(settings.max_retries):
            try:
                result = await chain.ainvoke(input_data)
                return result
            except RateLimitError as e:
                last_error = e
                logger.warning(f"遇到速率限制，第 {attempt + 1} 次重试，等待 {delay:.1f} 秒...")
                await asyncio.sleep(delay)
                delay *= 2  # 指数退避
            except Exception as e:
                # 其他错误不重试，直接抛出
                raise e

        # 重试次数耗尽
        raise last_error

    async def _assess_difficulty(self, summary: str) -> int:
        """
        评估文本难度等级

        Args:
            summary: 蒸馏后的摘要文本

        Returns:
            int: 难度等级（1-5）

        注意：
        - 使用专门的难度评估提示词
        - 添加错误处理，默认返回中等难度
        - 使用重试机制处理速率限制
        """
        try:
            result = await self._invoke_with_retry(
                self._difficulty_chain,
                {"article": summary}
            )

            # 尝试解析数字
            difficulty = int(result.strip())

            # 确保在有效范围内
            return max(1, min(5, difficulty))

        except RateLimitError:
            # 速率限制时返回默认中等难度
            logger.warning("难度评估遇到速率限制，使用默认值 3")
            return 3
        except (ValueError, IndexError) as e:
            # 解析失败时返回默认中等难度
            logger.warning(f"难度评估解析失败: {e}，使用默认值 3")
            return 3
        except Exception as e:
            # 其他异常也返回默认值
            logger.error(f"难度评估失败: {e}，使用默认值 3")
            return 3

    def _estimate_read_time(self, content: str) -> int:
        """
        估算阅读时间（分钟）

        Args:
            content: 原文内容

        Returns:
            int: 预估阅读时间（分钟）

        计算逻辑：
        - 中文阅读速度：约 400 字/分钟
        - 英文阅读速度：约 200 词/分钟
        - 取保守估计，约 200 字符/分钟
        """
        if not content:
            return 0

        # 简单估算：每 200 字符约 1 分钟
        return max(1, len(content) // 200)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        解析 LLM 返回的 JSON 响应

        Args:
            response: LLM 返回的原始字符串

        Returns:
            Dict[str, Any]: 解析后的 JSON 对象

        注意：
        - 尝试直接解析 JSON
        - 如果失败，尝试提取 JSON 块
        - 如果仍然失败，返回默认结构
        """
        try:
            # 尝试直接解析
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # 尝试提取 JSON 块（处理 markdown 代码块）
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1).strip())
                except json.JSONDecodeError:
                    pass

            # 尝试提取花括号内容
            brace_match = re.search(r'\{.*\}', response, re.DOTALL)
            if brace_match:
                try:
                    return json.loads(brace_match.group(0))
                except json.JSONDecodeError:
                    pass

            # 所有尝试都失败，返回默认结构
            logger.warning("JSON 解析失败，返回默认空结构")
            return {
                "concepts": [],
                "terms": []
            }

    async def _extract_concepts(self, summary: str, original_content: str) -> Dict[str, Any]:
        """
        提取核心概念和术语

        Args:
            summary: 蒸馏后的摘要文本
            original_content: 原始文本内容

        Returns:
            Dict[str, Any]: 包含 concepts 和 terms 的字典

        注意：
        - 使用摘要而非全文进行提取，提高效率
        - 失败时返回空结构，不影响主流程
        """
        try:
            # 使用摘要进行概念提取（比全文更高效）
            result = await self._invoke_with_retry(
                self._concepts_chain,
                {"article": summary}
            )

            # 解析 JSON 结果
            concepts_data = self._parse_json_response(result)

            # 验证和清理数据
            concepts = concepts_data.get("concepts", [])
            terms = concepts_data.get("terms", [])

            # 确保 concepts 是列表
            if not isinstance(concepts, list):
                concepts = []

            # 确保 terms 是列表且每个元素有正确的结构
            if not isinstance(terms, list):
                terms = []
            else:
                # 清理术语数据，确保每个术语都有 term 和 definition
                cleaned_terms = []
                for term_item in terms:
                    if isinstance(term_item, dict):
                        term = term_item.get("term", "").strip()
                        definition = term_item.get("definition", "").strip()
                        if term and definition:
                            cleaned_terms.append({
                                "term": term,
                                "definition": definition
                            })
                terms = cleaned_terms

            logger.info(f"概念提取完成: {len(concepts)} 个概念, {len(terms)} 个术语")

            return {
                "concepts": concepts,
                "terms": terms
            }

        except RateLimitError:
            # 速率限制时返回空结构
            logger.warning("概念提取遇到速率限制，返回空结构")
            return {
                "concepts": [],
                "terms": []
            }
        except Exception as e:
            # 其他异常也返回空结构
            logger.error(f"概念提取失败: {e}，返回空结构")
            return {
                "concepts": [],
                "terms": []
            }


# 便捷函数
async def distill_article(content: str) -> Dict[str, Any]:
    """
    执行文章蒸馏的便捷函数

    Args:
        content: 待蒸馏的长文本内容

    Returns:
        Dict[str, Any]: 蒸馏结果字典
    """
    chain = DistillationChain()
    return await chain.distill_article(content)


# 创建可复用的链路实例（用于 LangServe）
distillation_chain_instance = DistillationChain()

# 如果需要作为 LangServe 端点暴露，可以创建一个 Runnable 包装器
async def distillation_runnable(input_data: Dict[str, str]) -> Dict[str, Any]:
    """
    LangServe 兼容的 Runnable 包装器

    Args:
        input_data: 包含 'content' 字段的输入字典

    Returns:
        Dict[str, Any]: 蒸馏结果
    """
    content = input_data.get("content", "")
    return await distill_article(content)
