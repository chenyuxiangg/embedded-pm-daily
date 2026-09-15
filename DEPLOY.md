# 5 分钟部署到 GitHub

跟着下面 4 步走,5 分钟搞定。

---

## 第 1 步:在 GitHub 网页创建空仓库

打开 https://github.com/new

填这几项:
- **Repository name**: `embedded-pm-daily`(随便起,但要记住)
- **Public / Private**: 都行,推荐 Private(你的 Telegram 和 API key 在 Secrets 里,但代码本身不敏感)
- ⚠️ **不要勾** Add a README file / Add .gitignore / Choose a license(我已经准备好了)

点 **Create repository**

---

## 第 2 步:把代码推上去

打开终端,进入项目目录:

```bash
cd embedded-pm-daily
bash deploy.sh
```

按提示输入:
- GitHub 用户名
- 仓库名(默认 `embedded-pm-daily`)

它会自动:
- 加 origin
- 推送到 main 分支

> 如果你用 HTTPS 而不是 SSH,可能需要先配置 token 或改 `deploy.sh` 里的 `git@github.com:` 改成 `https://github.com/`。

如果 `bash deploy.sh` 不灵,你也可以手动:
```bash
git remote add origin git@github.com:<你的用户名>/embedded-pm-daily.git
git push -u origin main
```

---

## 第 3 步:填 Secrets(2 分钟)

在 GitHub 仓库页面:

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

依次添加 5 个:

| Name | 填什么 | 示例 |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather 给你那个 token | `123456:ABC-DEF...` |
| `TELEGRAM_CHAT_ID` | 你的 chat id(数字) | `987654321` |
| `LLM_API_KEY` | DeepSeek / OpenAI 的 key | `sk-xxxxxxxx` |
| `LLM_API_BASE` | API 的 base URL | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | 模型名 | `deepseek-chat` |

> 推荐用 **DeepSeek**:便宜,中文也好。每天成本基本几毛钱。

---

## 第 4 步:触发第一次运行

回到仓库主页:

`Actions` 标签 → 左边选 `Embedded PM Daily` → 右边 `Run workflow` → 绿色按钮 `Run workflow`

等 1-2 分钟看日志。如果看到 ✅,去 Telegram 应该已经收到早报了。

---

## 之后的每天

默认 `0 0 * * *`(UTC)= 北京时间早 8 点自动跑。

想改时间:编辑 `.github/workflows/daily.yml` 的 `cron` 字段。

比如改成早 7 点:
```yaml
- cron: "0 23 * * *"  # UTC 23 点 = 北京时间早 7 点
```

想工作日才跑:
```yaml
- cron: "0 0 * * 1-5"
```

改完 commit + push,GitHub Actions 会自动用新的 schedule。

---

## 出问题了?

**Actions 跑失败:**
- 点进去看日志,找红色 ERROR
- 80% 是 Secrets 名字打错了(注意大小写敏感)
- 也可能是某个 RSS 源暂时挂了,可以重试或改 `src/sources/__init__.py` 把它去掉

**Telegram 没收到:**
- 跑 `python scripts/test_telegram.py` 本地测试连通性
- 看 chat_id 对不对(群是负数)
- 看 Bot 是不是被屏蔽了

**抓不到内容:**
- 跑 `python scripts/dryrun.py` 看哪些源挂了
- RSS 失败会自动 fallback 到 HTML,一般不会全挂

---

## 想要更"工程化"?

- 调抓取频率:改 `.github/workflows/daily.yml` 的 cron
- 调摘要风格:改 `src/summarizer.py` 里的 prompt
- 加新源:在 `src/sources/registry.py` 或 `src/sources/english.py` 加类,然后在 `src/sources/__init__.py` 的 `SOURCE_PLAN` 注册
- 改消息格式:改 `src/formatter.py`