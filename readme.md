欢迎来到阿敏

## 项目简介

阿敏（Mint_Digit）是一个基于 QQ/LLOneBot 的智能群聊/私聊机器人，扮演“夜鹰家族司律官 · 阿敏EVIL”的角色。它能够管理用户、记忆聊天上下文、调用多种大模型进行对话，并对群内行为进行一定程度的“裁决”和管理（如禁言、处理加群请求等）。

## 整体架构

- **入口与事件分发**
  - `main.py`：基于 FastAPI 的 HTTP 服务入口，监听来自 LLOneBot 的事件回调（如私聊、群聊消息、加群请求等），将事件转交给业务逻辑。
  - `mint_utils.py`：事件处理核心模块，根据不同事件类型进行路由与处理，包括消息频率限制、重复消息检测与禁言逻辑等。

- **对话与 Agent 流程**
  - `chat_agent.py`：使用 LangGraph 搭建对话 Agent 工作流，负责组织多轮对话、调用大模型和工具。
  - `memory.py`：对话记忆管理模块，维护用户会话历史、压缩与清理历史消息，并注入系统提示词（如阿敏EVIL的角色设定）。
  - 支持基于 FAISS + 向量检索的“用户信息检索”，在对话中利用历史资料。

- **用户与资产管理**
  - `user_manager.py`：用户信息管理（ID、别名、声望、备注等），负责在 `user_info.json` 中持久化用户数据，并提供搜索、清洗用户名等功能。
  - `asset_utils.py`：用户资产与抽奖系统，管理余额、抽卡（SSR/SR/R/N）以及生成称号（会调用豆包模型）。

- **多模型能力封装**
  - `gpt_utils.py`：OpenAI GPT 与 DALL·E 的封装。
  - `doubao_utils.py`：字节跳动豆包模型封装。
  - `grok_utils.py`：X.AI Grok 模型封装（包含函数调用能力）。
  - `gemini_utils.py`：Google Gemini 系列模型封装（含简单配额管理逻辑）。

- **机器人与外部服务接口**
  - `llob_utils.py`：LLOneBot API 封装，用于发送 QQ 私聊/群聊消息、群禁言、处理加群请求等。

- **测试与工具**
  - `test/` 目录：包含针对核心模块（如 `user_manager.py`、`chat_agent.py`、`memory.py` 等）的单元测试，有助于保证行为稳定。

## 数据与配置

- **数据文件（典型）**
  - `user_info.json`：用户信息数据文件（当前仓库中以 `.bak` 形式存在备份示例）。
  - `user_assets.json`：用户资产/余额等信息。
  - `memory.log`：对话记忆日志。

- **配置与环境变量（推测）**
  项目依赖多家大模型服务，需要在环境变量或配置文件中提供对应的 API Key，例如（具体名称请以代码为准）：
  - `DOUBAO_API_KEY`
  - `XAI_API_KEY`
  - `GEMINI_API_KEY`
  - `OPENAI_API_KEY`
  - `ZHIPU_API_KEY`

  建议增加一个 `.env.example` 或在本 README 中单独列出配置说明，方便部署与协作。

## 运行与依赖（根据当前仓库推断）

当前仓库中已存在 `requirements.txt`，但内容尚未完善。根据代码实际使用情况，项目大致依赖：

- Web 框架相关：
  - `fastapi`
  - `uvicorn`
- AI / Agent 框架：
  - `langchain`
  - `langgraph`
  - `faiss-cpu`
- 各模型 SDK：
  - OpenAI 官方 SDK
  - `zhipuai` / `langchain-zhipu`（或等价封装）
  - X.AI / Grok SDK
  - `google-generativeai`
  - 豆包相关 SDK（如 `dashscope` / 字节官方 SDK，根据代码实际为准）
- 其他：
  - `requests`
  - `python-dotenv`

后续可以在 `requirements.txt` 中补充、锁定具体版本。

## 当前项目优点

- **架构清晰**：入口（`main.py`）– 事件处理（`mint_utils.py`）– 对话 Agent（`chat_agent.py` + `memory.py`）– 用户与资产管理（`user_manager.py` / `asset_utils.py`）这一链路较为清晰。
- **功能完整度较高**：
  - 支持群聊/私聊消息处理、加群请求处理。
  - 支持多模型接入（GPT、豆包、Grok、Gemini、智谱等）。
  - 具备用户管理、资产系统、抽卡与称号生成等扩展玩法。
  - 对话有记忆与向量检索，整体体验更接近“有记忆的群管理 AI”。
- **有测试基础**：`test/` 目录下存在多模块的测试文件，说明已有一定的质量保障意识。

## 当前主要问题与改进建议

- **依赖与环境说明不足**
  - `requirements.txt` 目前为空，无法一键安装依赖。
  - 未见 `.env.example` 或配置说明，新人或未来自己回看时都不够直观。
  - **建议**：根据当前代码实际导入的包，补全 `requirements.txt`；在 README 中增加“环境变量说明”章节，或提供 `.env.example`。

- **文档与使用说明缺失**
  - 之前的 README 仅有一行欢迎语，缺少部署、运行方式（如何启动 FastAPI/Uvicorn、如何与 LLOneBot 对接）等信息。
  - **建议**：后续在本文件中继续补充：
    - 安装步骤（创建虚拟环境、安装依赖）。
    - 启动方式（命令示例，如 `uvicorn main:app --host 0.0.0.0 --port 8080`）。
    - 与 LLOneBot 的对接方式（回调 URL、事件类型等）。

- **配置与安全性**
  - API Key 等敏感信息的管理方式需要统一说明（环境变量/.env/配置文件），避免误提交到仓库。
  - **建议**：增加 `.gitignore` 中对 `.env`、日志和数据文件（如 `user_info.json`、`user_assets.json`）的忽略规则，并在 README 说明。

- **监控与异常处理**
  - 目前从代码结构来看，主要以简单日志/print 为主，缺少系统性的监控与错误恢复策略。
  - **建议**：后续可考虑引入统一日志模块、异常捕获中间件，以及必要时的告警机制（如群内发送异常提示等）。

总体来看，阿敏项目在**功能设计和架构分层**上已经相当完整，当前的主要短板集中在**文档、依赖管理和配置说明**这三块。只要完善这些基础设施，就非常适合长期维护与继续扩展。