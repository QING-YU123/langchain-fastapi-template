"""
蒸馏服务提示词模板

管理知识蒸馏相关的 AI 提示词，包括 Refine 模式的初始和迭代提示词
"""
from langchain_core.prompts import ChatPromptTemplate


# ==================== Refine 模式提示词 ====================

# Refine 初始提示 - 提取第一片段的核心逻辑骨架
summary_initial_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是知识蒸馏专家，擅长从长文本中提取核心逻辑骨架。

请对给定的文本片段进行脱水处理：

**核心要求**：
1. 去除冗余修饰、举例、比喻和非核心的描述性文字
2. 保留核心论点、关键数据、重要结论和逻辑关系
3. 用简洁清晰的语言重新组织
4. 输出长度控制在原文的 30% 以内

**输出格式**：
- 直接输出蒸馏后的文本，不需要任何格式标记或说明
- 保持段落结构，确保逻辑连贯性
- 使用专业但不过于晦涩的语言"""),
    ("user", "文本片段：\n{chunk}")
])


# Refine 迭代提示 - 基于现有摘要整合新片段
summary_refine_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是知识蒸馏专家，负责整合新的文本片段到现有摘要中。

**核心任务**：
将新文本片段的核心信息整合到现有摘要中，形成更完整的逻辑骨架。

**整合原则**：
1. 识别新片段中的新信息、新观点、新数据
2. 避免重复现有摘要中已包含的内容
3. 保持全文的逻辑连贯性和一致性
4. 更新摘要的结构，确保信息层次清晰
5. 总体长度仍控制在原文总量的 30% 以内

**输出格式**：
- 直接输出整合后的摘要，不需要任何格式标记
- 保持段落结构，使用逻辑连接词确保流畅性"""),
    ("user", """现有摘要：
{existing_summary}

新文本片段：
{chunk}""")
])


# ==================== 导读三问生成提示词（Phase 2 预留）====================

reading_questions_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是导读设计专家，擅长为文章设计激发深度思考的问题。

请基于文章内容设计 3 个导读问题：

**问题设计原则**：
1. **启发性**：问题应该引导读者主动思考，而非简单的信息检索
2. **层次性**：问题应覆盖理解、分析、应用不同层次
3. **开放性**：避免是/否答案，鼓励探索性思考
4. **针对性**：紧扣文章核心观点和价值

**输出格式**：
- 以 JSON 数组格式输出 3 个问题
- 每个问题包含 question（问题内容）和 purpose（设计目的）
- 示例：[{"question": "...", "purpose": "..."}]"""),
    ("user", "文章内容：\n{article}")
])


# ==================== 概念术语提取提示词（Phase 2 预留）====================

concepts_extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是概念分析专家，擅长识别文本中的核心概念和专业术语。

请从文章中提取：

1. **核心概念**（3-5个）：
   - 文章的核心思想或关键理论概念
   - 对理解文章至关重要的抽象概念
   - 跨领域的重要概念

2. **关键术语**（5-8个）：
   - 专业术语或行业特定词汇
   - 文章中定义或重点解释的词汇
   - 为每个术语提供简洁的定义（一句话）

**输出格式**：
- 以 JSON 格式输出，必须严格符合以下结构：
- 包含两个字段：concepts（字符串数组）和 terms（对象数组）
- terms 数组中每个对象包含 term（术语名称）和 definition（术语定义）
- 输出示例结构：包含核心概念列表和术语定义列表的 JSON 对象"""),
    ("user", "文章内容：\n{article}")
])


# ==================== 难度评估提示词（辅助）====================

difficulty_assessment_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是内容难度评估专家。

请基于以下维度评估文章的难度等级（1-5级）：

**评估维度**：
1. **概念复杂度**：涉及概念的抽象程度和专业性
2. **背景知识要求**：读者需要的前置知识量
3. **逻辑复杂度**：论证链条的复杂程度
4. **专业术语密度**：专业术语的使用频率

**难度等级标准**：
- 1级：面向大众，无需专业背景
- 2级：高中文化程度可理解
- 3级：大学本科水平或行业入门
- 4级：需要专业背景或深度思考
- 5级：高度专业，需要领域专家知识

**输出格式**：
- 直接输出 1-5 的数字，不需要其他内容"""),
    ("user", "文章内容：\n{article}")
])


def get_summary_initial_prompt():
    """获取 Refine 初始提示词"""
    return summary_initial_prompt


def get_summary_refine_prompt():
    """获取 Refine 迭代提示词"""
    return summary_refine_prompt


def get_reading_questions_prompt():
    """获取导读三问提示词（Phase 2）"""
    return reading_questions_prompt


def get_concepts_extraction_prompt():
    """获取概念术语提取提示词（Phase 2）"""
    return concepts_extraction_prompt


def get_difficulty_assessment_prompt():
    """获取难度评估提示词"""
    return difficulty_assessment_prompt
