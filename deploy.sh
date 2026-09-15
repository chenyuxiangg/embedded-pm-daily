#!/usr/bin/env bash
# 一键部署到 GitHub
# 用法:
#   bash deploy.sh                              # 交互式输入用户名和仓库名
#   bash deploy.sh <github-user> <repo-name>    # 直接传参
#
# 前置: 已经在 GitHub 网页上创建好空仓库(不要勾 README/.gitignore/license)

set -e

# 取参数或交互问
if [ -n "$1" ] && [ -n "$2" ]; then
    GH_USER="$1"
    REPO="$2"
else
    read -p "GitHub 用户名: " GH_USER
    read -p "仓库名(默认 embedded-pm-daily): " REPO
    REPO="${REPO:-embedded-pm-daily}"
fi

# 校验
if [ -z "$GH_USER" ] || [ -z "$REPO" ]; then
    echo "❌ 用户名和仓库名不能为空"
    exit 1
fi

# 检查 / 兜底初始化 git
if [ ! -d ".git" ]; then
    echo "⚠️  当前目录不是 git 仓库,自动初始化..."
    git init -b main
    git config user.name "embedded-pm-bot"
    git config user.email "bot@example.com"
    git add .
    git commit -m "feat: 初始化嵌入式 PM 每日早报项目"
    echo "✅ git 仓库已自动初始化"
fi

# 检查是否有 commit
if ! git rev-parse HEAD >/dev/null 2>&1; then
    echo "❌ 仓库还没有任何 commit,请检查项目目录"
    exit 1
fi

REMOTE_URL="git@github.com:${GH_USER}/${REPO}.git"

echo ""
echo "=========================================="
echo "  准备推送到:"
echo "  ${REMOTE_URL}"
echo "=========================================="
echo ""

# 看一下当前 remote
if git remote get-url origin >/dev/null 2>&1; then
    EXISTING=$(git remote get-url origin)
    echo "⚠️  当前 origin 已存在: ${EXISTING}"
    read -p "是否替换为新的远程地址?(y/N): " ANSWER
    if [ "$ANSWER" = "y" ] || [ "$ANSWER" = "Y" ]; then
        git remote set-url origin "$REMOTE_URL"
    else
        echo "保留原远程地址"
    fi
else
    git remote add origin "$REMOTE_URL"
fi

echo ""
echo "📤 推送代码到 GitHub..."
git push -u origin main

echo ""
echo "=========================================="
echo "  ✅ 代码已推送!"
echo "=========================================="
echo ""
echo "接下来你需要在 GitHub 网页上做这几件事:"
echo ""
echo "1. 打开仓库页面: https://github.com/${GH_USER}/${REPO}"
echo ""
echo "2. 配置 Secrets(仓库 → Settings → Secrets and variables → Actions → New repository secret):"
echo ""
echo "   ┌──────────────────────────┬─────────────────────────────┐"
echo "   │ Name                     │ Value                       │"
echo "   ├──────────────────────────┼─────────────────────────────┤"
echo "   │ TELEGRAM_BOT_TOKEN       │ 你的 Bot Token               │"
echo "   │ TELEGRAM_CHAT_ID         │ 你的 Chat ID(数字)           │"
echo "   │ LLM_API_KEY              │ DeepSeek/OpenAI 的 key       │"
echo "   │ LLM_API_BASE             │ https://api.deepseek.com/v1 │"
echo "   │ LLM_MODEL                │ deepseek-chat               │"
echo "   └──────────────────────────┴─────────────────────────────┘"
echo ""
echo "3. 触发第一次运行:"
echo "   Actions 标签 → Embedded PM Daily → Run workflow → Run workflow"
echo ""
echo "4. 之后每天早 8 点(北京时间)自动跑"
echo ""
echo "详细说明见项目内的 DEPLOY.md"
echo ""