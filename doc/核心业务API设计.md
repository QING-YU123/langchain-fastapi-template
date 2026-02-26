这种**“双端解耦”**的微服务架构非常契合现代 AI 应用的开发范式。

把所有和数据库打交道、状态机流转、鉴权路由的脏活累活交给 **Hono + Drizzle + Postgres (数据端)**，保证极高的并发和极低的延迟；而把需要跑重型 LangChain 链、处理大上下文、 CPU 密集型任务交给 **Python (AI 端)**，作为无状态的纯计算引擎。

下面我为你梳理出这套 MVP（最小可行性产品）的核心 API 矩阵，严格按照“认知代谢”生命周期的顺序列出。

---

### 一、 数据服务端 API (Hono + Drizzle)

**定位：** 系统的“大管家”。负责与 Electron 客户端直接通信，管理所有数据持久化、状态机流转以及复习调度算法（SRS）。

| **API 路由**                        | **核心业务流**     | **作用描述 (Action)**                                                                                        | **影响的数据库表**                                                                                |
| --------------------------------- | ------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `POST /api/articles`              | **1. 捕获落库**   | 接收 Electron 传来的 Markdown，创建网页快照，赋予初始状态 (`INBOX`)，并**异步调用 Python 端**进行脱水处理。                               | `INSERT` 进 `articles`<br><br>  <br><br>`INSERT` 进 `review_schedules` (初始化倒计时)              |
| `POST /api/webhooks/ai-distilled` | **2. 接收脱水结果** | 接收 AI 提取的导读、术语，以及用于关联的**核心概念 (`core_concepts`) 和技术栈 (`tech_stack`) 等纯 JSON 数据**。完成关联落库，将文章状态推进为 `READY`。 | `INSERT` 进 `ai_distillations` (存入 JSONB 字段)<br><br>`UPDATE` 进 `articles`<br>               |
| `GET /api/schedules/today`        | **3. 调度拉取**   | 根据用户的精力状态查询条件，拉取 `next_review_at <= NOW()` 的文章列表（含脱水教案）。                                                 | `SELECT` 查 `articles`<br><br>  <br><br>`SELECT` 查 `review_schedules`                       |
| `POST /api/debates/evaluate`      | **4. 反刍与对弈**  | 接收用户的回答文本，**同步调用 Python 端**进行逻辑评分。拿到评分后，Hono 本地运行 SRS 算法计算下一次复习时间。                                       | `INSERT` 进 `evaluation_debates`<br><br>  <br><br>`UPDATE` 进 `review_schedules` (更新权重与下次时间) |
| `GET /api/connections/search`     | **5. 语义检索**   | 接收查询文本，利用 Drizzle 执行 `pgvector` 的余弦相似度计算，返回逻辑相关或冲突的历史文章。                                                 | `SELECT` 查 `article_embeddings` (走 HNSW 索引)                                                |

---

### 二、 AI 计算端 API (Python + LangChain)

**定位：** 系统的“大脑/导师”。无状态服务，不直接连数据库。只负责接收文本 $\rightarrow$ 跑大模型 $\rightarrow$ 返回结构化 JSON。

| **API 路由**              | **核心业务流**   | **作用描述 (Action)**                                                                             | **交互模式**                                                             |
| ----------------------- | ----------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `POST /ai/distill`      | **1. 硬核脱水** | 接收长文本。使用 LangChain 的 Text Splitter 处理超长文本，调用 LLM 提取 `guiding_questions` (导读三问) 和 `key_terms`。 | 异步长任务（建议：Hono 发起请求后，Python 端通过消息队列处理，处理完再 HTTP 回调 Hono）。             |
| `POST /ai/ask-question` | **3. 生成考题** | 接收文章核心文本及当前用户的“掌握度等级”，调用 LLM 动态生成一道“苏格拉底式”的情景提问或变式题。                                          | 同步调用。在用户点击“开始复习”的瞬间，由 Hono 向 Python 索要考题。                            |
| `POST /ai/score-answer` | **4. 导师评分** | 接收 [原文逻辑骨架 + AI考题 + 用户回答]。LLM 扮演严师，比对逻辑漏洞，返回明确的等级分（如 A, B, C）和纠偏评语。                           | 同步调用。需严格约束 LangChain 的 OutputParser，确保返回 100% 可被 Hono 解析的 JSON 格式评分。 |


---

### 💡 核心业务流转示例（数据与 AI 的握手）

以最核心的**Epic 4：闭环评估与反刍**为例，看看双端是如何配合的：

1. **Electron (前端):** 提醒用户该复习了，展示文章。用户点击“开始测试”。
    
2. **Hono (数据端):** 收到请求。从 PG `articles` 表查出正文，发送到 `Python: /ai/ask-question`。
    
3. **Python (AI 端):** LangChain 瞬间生成一道题返回给 Hono。
    
4. **Electron (前端):** 遮蔽正文，展示题目。用户输入回答：“我认为这是因为多路复用避免了队头阻塞...” 并提交 (`POST /api/debates/evaluate`)。
    
5. **Hono (数据端):** 把用户的回答扔给 `Python: /ai/score-answer`。
    
6. **Python (AI 端):** LangChain 分析后返回：`{"score": "B", "feedback": "提到了队头阻塞，但忘了讲连接迁移特性。"}`。
    
7. **Hono (数据端):** 收到 `B` 评分。运行本地代码 `calculateNextReview(currentEase, 'B')`，算出 3 天后再次复习。利用 Drizzle 将这一切更新到 `review_schedules` 和 `evaluation_debates`。
    

---
