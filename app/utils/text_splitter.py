"""
文本切片工具

提供语义感知的文本切片功能，支持中英文混合内容的智能分割
"""
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings


class TextSplitterFactory:
    """文本切片器工厂类"""

    @staticmethod
    def create_distillation_splitter() -> RecursiveCharacterTextSplitter:
        """
        创建用于蒸馏任务的文本切片器

        配置说明：
        - chunk_size: 切片大小（默认2000字符）
        - chunk_overlap: 重叠大小（默认200字符，约10%）
        - separators: 按优先级尝试的分割符（中文友好的分隔符序列）

        Returns:
            RecursiveCharacterTextSplitter: 配置好的切片器实例
        """
        separators = [
            "\n\n\n",  # 三个换行符（段落分隔）
            "\n\n",   # 两个换行符
            "\n",     # 单个换行符
            "。",     # 中文句号
            "！ ",     # 中文感叹号
            "？ ",     # 中文问号
            "；",     # 中文分号
            "，",     # 中文逗号
            ". ",     # 英文句号+空格
            "! ",     # 英文感叹号+空格
            "? ",     # 英文问号+空格
            "; ",     # 英文分号+空格
            ", ",     # 英文逗号+空格
            " ",      # 空格
            ""        # 字符级分割（最后手段）
        ]

        return RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False,
        )

    @staticmethod
    def split_text_for_distillation(content: str) -> List[str]:
        """
        将文本切片为适合蒸馏处理的片段

        Args:
            content: 待切片的长文本内容

        Returns:
            List[str]: 切片后的文本片段列表

        注意：
        - 返回的片段会保持语义完整性
        - 相邻片段有重叠部分以确保上下文连贯性
        - 空文本或极短文本会返回包含原文的单元素列表
        """
        if not content or not content.strip():
            return []

        splitter = TextSplitterFactory.create_distillation_splitter()
        chunks = splitter.split_text(content)

        # 过滤掉空的片段
        chunks = [chunk.strip() for chunk in chunks if chunk and chunk.strip()]

        return chunks

    @staticmethod
    def estimate_chunks(content: str) -> int:
        """
        估算文本会被切成多少个片段

        Args:
            content: 待估算的文本内容

        Returns:
            int: 预估的片段数量
        """
        if not content:
            return 0

        effective_size = settings.chunk_size - settings.chunk_overlap
        return max(1, (len(content) + effective_size - 1) // effective_size)


# 便捷函数
def split_text_for_distillation(content: str) -> List[str]:
    """将文本切片为适合蒸馏处理的片段"""
    return TextSplitterFactory.split_text_for_distillation(content)


def create_distillation_splitter() -> RecursiveCharacterTextSplitter:
    """创建用于蒸馏任务的文本切片器"""
    return TextSplitterFactory.create_distillation_splitter()
