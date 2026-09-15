# Embedded PM Daily · 嵌入式 PM 每日早报

每天早上 8 点(北京时间)自动从 20+ 个国内外嵌入式 / 消费电子 / 半导体 / 拆解 / 众筹 / 政策网站抓取文章,
通过 LLM 生成 PM 视角的中文摘要,推送至你的 Telegram。

## ✨ 特性

- **20+ 信息源覆盖**:政策 / 产业 / 技术 / 拆解 / 趋势 / 用户痛点,全场景
- **AI 中文摘要**:每篇文章 2-3 句 PM 视角精炼摘要,英文自动转中文
- **Telegram 推送**:HTML 美化版,按分类分组
- **零成本运行**:用 GitHub Actions 跑,无需服务器,无需域名
- **去重不刷屏**:基于 URL 去重,7 天内不重复推同一条
- **本地 dryrun**:不消耗 LLM 配额也能预览抓取结果
- **双策略抓取**:优先 RSS,RSS 失败自动 fallback 到 HTML 列表解析(覆盖更多国内站)

## 🗂 数据源清单

| 分类 | 来源 |
|---|---|
| 🏛 政策 | 中国电子报、赛迪(经产业图谱/与非网) |
| 🏭 产业 | 与非网产业、爱集微、智东西 |
| 🔬 技术(中文) | 与非网、电子工程专辑、电子产品世界、电子发烧友 |
| 🔬 技术(英文) | EE Times、Embedded.com、IEEE Spectrum、Semiconductor Engineering、Electronics Weekly、CNX Software、Circuit Cellar、EE Herald |
| 🔧 拆解 | iFixit、ChargerLAB、我爱音频网 |
| 🚀 趋势 | Kickstarter、Hackaday、The Verge |

## 🚀 快速开始

### 1. 准备 Telegram Bot

1. 在 Telegram 找 [@BotFather](https://t.me/BotFather),发 `/newbot`,按提示创建机器人,**记下 Token**
2. 给你的机器人发任意一条消息
3. 浏览器访问(把 `<TOKEN>` 替换成你的):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
   找到 `chat.id`(个人通常是纯数字,群组是负数)

### 2. 准备 LLM API Key

支持任何兼容 OpenAI Chat Completion 协议的 API:
- **MiniMax**:https://platform.MiniMax.cn/
- **OpenAI**:https://platform.openai.com/
- **DeepSeek**:https://platform.deepseek.com/(便宜,推荐)
- **智谱 GLM**:https://open.bigmodel.cn/

把 `API Key` + `Base URL` + `Model` 记下来。

### 3. 部署到 GitHub

1. **Fork 或新建仓库**,把本目录所有文件 push 上去
2. 进入仓库的 `Settings` → `Secrets and variables` → `Actions`,添加以下 Secrets:
   ```
   TELEGRAM_BOT_TOKEN   = 你的 bot token
   TELEGRAM_CHAT_ID     = 你的 chat id
   LLM_API_BASE         = https://api.deepseek.com  (举例)
   LLM_API_KEY          = sk-xxxxxxxx
   LLM_MODEL            = deepseek-chat
   ```
3. 进入 `Actions` 标签,左边选 `Embedded PM Daily`,点 `Run workflow` 试一次
4. 每天早上 8 点(UTC 0 点)自动跑

### 4.(可选)本地测试

```bash
# 安装依赖
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env
# 编辑 .env 填入你的 token / key

# 测试 Telegram 连通
python scripts/test_telegram.py

# 不消耗 LLM 配额,预览抓取结果
python scripts/dryrun.py

# 真正跑一次
python -m src.main
```

## ⚙️ 调参

编辑 `.env`(本地)或 GitHub Secrets:

| 变量 | 说明 | 默认 |
|---|---|---|
| `LOOKBACK_HOURS` | 抓多少小时内的文章 | 24 |
| `MAX_PER_SOURCE` | 每个源最多取多少篇 | 8 |
| `LLM_MAX_ARTICLES` | 单次最多摘要多少篇(防止爆 token) | 80 |
| `TELEGRAM_BATCH_SIZE` | 单条消息最大字符 | 3500(自动切) |

调整抓取频率:编辑 `.github/workflows/daily.yml` 的 `cron`。

```yaml
# 北京时间早 8 点 = UTC 0 点
- cron: "0 0 * * *"
# 改成早 7 点 = UTC 23 点
- cron: "0 23 * * *"
# 改成工作日(周一到周五)
- cron: "0 0 * * 1-5"
```

## 🧠 摘要风格

LLM 收到的 prompt 模板(可在 `src/summarizer.py` 改):

> 你是嵌入式消费电子行业的产品经理助手。
> 要求:
> 1. 2-3 句话,不超过 120 字
> 2. 直接讲"这意味着什么"或"PM 该关注什么"
> 3. 优先指出:技术/产品变化、产业链动向、价格/供应变化、用户痛点信号
> 4. 避免空话,不要"近日""据悉"
> 5. 不要"标题党"风格,实事求是

## 🛠 项目结构

```
.
├── .github/workflows/daily.yml   # GitHub Actions 定时任务
├── data/seen.json                # 去重记录(自动维护)
├── scripts/
│   ├── dryrun.py                 # 本地预览抓取
│   └── test_telegram.py          # Telegram 连通性测试
├── src/
│   ├── main.py                   # 主入口
│   ├── config.py                 # 配置加载
│   ├── models.py                 # Article 数据类
│   ├── deduplicator.py           # 去重 + JSON 持久化
│   ├── summarizer.py             # LLM 摘要
│   ├── formatter.py              # Telegram 消息格式化
│   ├── telegram_bot.py           # 推送
│   └── sources/
│       ├── base.py               # 数据源基类(RSS 通用解析)
│       ├── registry.py           # 中文 + 拆解 + 众筹源
│       ├── english.py            # 英文媒体源
│       └── __init__.py           # 聚合入口
├── requirements.txt
├── .env.example
└── README.md
```

## 🐛 常见问题

**Q: GitHub Actions 跑失败,日志报 rate limit?**
A: 部分源(如 CSDN、部分国内站)对海外 IP 不友好。如果在 Actions 上抓取失败,改用自托管 runner 或在本地跑。

**Q: 想去掉某些源 / 加新源?**
A: 编辑 `src/sources/registry.py` 和 `src/sources/english.py`,在 `src/sources/__init__.py` 的 `SOURCE_PLAN` 列表里增减。

**Q: HTML 兜底抓到了 tag / category 页面这种垃圾?**
A: 编辑 `src/sources/fallback.py`,对应源类里的 `URL_PATTERNS` 加上更严格的白名单正则。

**Q: 不想用 LLM,只用标题+链接?**
A: 把 `src/main.py` 里的 `summarizer.summarize_batch(...)` 那行注释掉,formatter 会自动用 `raw_text` 兜底。

**Q: 想推送到多个 chat / 群?**
A: 改 `src/telegram_bot.py`,在 `_send_async` 里循环发送。

**Q: 怎么确认抓取没有问题?**
A: 先跑 `python scripts/dryrun.py`,会打印所有抓到的文章按分类,不发 Telegram 也不消耗 LLM。确认抓取内容 OK 之后再 `python -m src.main` 完整跑。

## 📜 License

MIT
