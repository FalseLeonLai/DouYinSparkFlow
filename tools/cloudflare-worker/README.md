# Cloudflare Worker 外部触发器

GitHub Actions 的 `schedule:` cron 是尽力而为，高峰时段经常延迟 5–30 分钟，偶尔
完全跳过。这个 Worker 用 Cloudflare 的 Cron Trigger（准时性远好于 GitHub）
按时调用 GitHub `workflow_dispatch` API，把"何时执行"的控制权移到 Cloudflare。

GitHub 这一侧仍然保留 `schedule:`（双保险）和 `workflow_dispatch:`（接受外部触发）。

## 准备

1. **GitHub PAT**
   - 访问 https://github.com/settings/tokens?type=beta
   - Repository access: 选中 `DouYinSparkFlow`
   - Repository permissions: `Actions` = **Read and write**
   - 生成后复制 token，下面会用到

2. **Cloudflare 账号 + Wrangler CLI**
   ```bash
   npm install -g wrangler
   wrangler login
   ```

## 部署

```bash
cd tools/cloudflare-worker
cp wrangler.toml.example wrangler.toml
# 按需修改 wrangler.toml 中的 GH_OWNER / GH_REPO / cron 时间

wrangler secret put GH_TOKEN              # 粘贴上一步的 GitHub PAT
wrangler secret put MANUAL_TRIGGER_TOKEN  # 可选：随便起一个长字符串，用于手动触发鉴权

wrangler deploy
```

部署成功后会得到一个形如 `https://douyin-spark-flow-trigger.<your-subdomain>.workers.dev` 的 URL。

## 验证

**手动触发一次**（验证 PAT 与 Worker 配置都正确）：

```bash
curl -X POST https://douyin-spark-flow-trigger.<your-subdomain>.workers.dev \
     -H "Authorization: Bearer <你的 MANUAL_TRIGGER_TOKEN>"
```

期望返回：`Triggered FalseLeonLai/DouYinSparkFlow/schedule.yml@main`

然后在 GitHub Actions 页面应该立刻能看到一次新的 run（trigger 会显示 `workflow_dispatch`）。

**查看 Worker cron 执行日志**：

```bash
wrangler tail
```

到设定的 cron 时间，应该看到 `[scheduled@29 0 * * *] dispatched ...` 字样。

## 与 GitHub Actions schedule 的关系

部署后，建议**保留** `.github/workflows/schedule.yml` 里的 `schedule:` 部分作为
兜底。这样即使 Worker 故障，GitHub Actions 自己的延迟调度也会兜住。两次重复触发
对续火花业务无副作用（同一天给同一好友重复发消息会被抖音去重，最多多发一条）。

如果你确认 Worker 稳定且不希望重复触发，把 `schedule.yml` 中的 `schedule:` 整段
删掉，只保留 `workflow_dispatch:` 即可。

## 成本

Cloudflare Workers 免费档：每天 10 万次请求 + 每天 1000 次 cron 调用。本 Worker 每天
2 次 cron + 几次手动触发，远在免费档内。
