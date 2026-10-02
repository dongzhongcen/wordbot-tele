# WordBot Tele

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.12-blue">
  <img alt="Telegram Bot" src="https://img.shields.io/badge/telegram-bot-26a5e4">
  <img alt="Render" src="https://img.shields.io/badge/render-web%20service-46e3b7">
  <img alt="Docker" src="https://img.shields.io/badge/docker-ready-2496ed">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/postgresql-neon-336791">
</p>

WordBot Tele 是一个 Telegram 每日单词机器人。用户可以随机获取单词、进行选择题测验、订阅每天北京时间 8 点的单词推送，也可以手动触发一次测试推送。项目支持本地 SQLite 运行，也支持通过 Render Web Service + Neon PostgreSQL 部署到云端。

## 功能特性

- **随机单词**：发送 `/word` 随机返回一个单词、释义和例句。
- **单词测验**：发送 `/quiz` 生成四选一选择题，点击按钮后显示答题结果。
- **每日推送**：发送 `/subscribe` 后，每天北京时间 8 点自动推送今日单词。
- **取消订阅**：发送 `/unsubscribe` 删除当前聊天的订阅记录。
- **立即测试**：发送 `/pushnow` 立刻执行一次推送逻辑，便于部署后检查。
- **数据库适配**：默认使用本地 `wordbot.db`，设置 `DATABASE_URL` 后可切换到 PostgreSQL / Neon。
- **健康检查网页**：内置极简 HTTP 服务，访问 Render 分配的网址会返回 `ok`，用于部署健康检查和定时唤醒。
- **Docker 部署**：提供 `Dockerfile` 和 `requirements.txt`，可直接用 Render Docker Web Service 部署。

## 项目结构

```text
.
├── bot.py             # Telegram 机器人主程序、定时任务和健康检查网页
├── words.json         # 单词数据源
├── requirements.txt   # Python 依赖
├── Dockerfile         # Render / Docker 部署配置
├── .gitignore         # Git 忽略规则
└── .dockerignore      # Docker 构建忽略规则
```

## 快速开始

### 环境要求

- Python 3.12 或兼容版本
- Telegram Bot Token（通过 BotFather 创建机器人获取）
- 可选：Neon PostgreSQL 数据库（云端部署时推荐）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

本地运行至少需要配置 `BOT_TOKEN`：

```bash
# PowerShell
$env:BOT_TOKEN="你的机器人 token"
```

可选环境变量：

```text
DATABASE_URL=postgresql://用户名:密码@主机/数据库?sslmode=require
TG_PROXY=http://127.0.0.1:7890
PORT=8080
```

说明：

- `BOT_TOKEN`：Telegram 机器人 token，必填。
- `DATABASE_URL`：数据库连接字符串。不填时默认使用本地 SQLite：`sqlite:///wordbot.db`。
- `TG_PROXY`：本地网络需要代理 Telegram 时使用；部署到 Render 时通常不要填写。
- `PORT`：健康检查网页端口，Render 会自动注入；本地默认 `8080`。

### 本地运行

```bash
python bot.py
```

启动后浏览器打开：

```text
http://127.0.0.1:8080
```

页面显示 `ok` 说明健康检查网页正常。然后在 Telegram 里发送 `/start`、`/word`、`/quiz`、`/subscribe` 或 `/pushnow` 测试机器人。

## 部署到 Render

1. 将项目推送到 GitHub。
2. 在 Render 新建 **Web Service**。
3. 连接本仓库。
4. Language 选择 **Docker**。
5. Region 可选择 **Singapore**。
6. Instance Type 可选择 **Free**。
7. 添加环境变量：

```text
BOT_TOKEN=你的机器人 token
DATABASE_URL=你的 Neon 连接字符串
```

> 部署到 Render 时不要配置 `TG_PROXY`。Render 服务器通常可以直接访问 Telegram。

点 Deploy 前，请先停止本地正在运行的 `python bot.py`。同一个 Telegram 机器人同一时间只能有一个程序接收消息，否则会出现 `Conflict` 错误。

## 定时唤醒

Render 免费实例可能会休眠。部署成功并显示 Live 后，复制 Render 分配的网址，确认浏览器打开能看到 `ok`，然后在 cron-job.org 创建定时任务：

1. 注册并登录 [cron-job.org](https://cron-job.org/)。
2. 点击 **Create cronjob**。
3. URL 填写 Render 的 Web Service 地址。
4. 执行间隔设置为每 10 分钟。
5. 保存任务。

这样 cron-job.org 会定期访问健康检查网页，让服务保持活跃。

## Telegram 命令

| 命令 | 说明 |
| --- | --- |
| `/start` | 查看机器人欢迎信息和命令说明 |
| `/word` | 随机获取一个单词 |
| `/quiz` | 做一道单词选择题 |
| `/subscribe` | 订阅每天北京时间 8 点的单词推送 |
| `/unsubscribe` | 取消每日推送订阅 |
| `/pushnow` | 立刻触发一次推送测试 |

## 当前状态

项目已完成 Telegram 机器人、订阅数据库、每日定时推送、健康检查网页和 Docker 部署配置。后续可继续完善：

- 增加管理员权限，限制 `/pushnow` 只允许管理员使用
- 增加更多单词数据和分类标签
- 支持用户自定义推送时间
- 增加日志和错误监控
- 为数据库逻辑和单词格式化逻辑增加测试
