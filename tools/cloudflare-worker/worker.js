/**
 * DouYinSparkFlow 外部触发器（Cloudflare Worker）
 *
 * 用途：通过 Cloudflare 自家 cron 调度调用 GitHub workflow_dispatch API，
 * 把"何时执行"的控制权从 GitHub Actions 移到 Cloudflare，规避 Actions
 * 调度器的随机延迟。
 *
 * 部署：见同目录 README.md。
 *
 * 环境变量（Worker secrets / vars）：
 *   GH_TOKEN              GitHub PAT，需 workflow / actions:write 权限（secret）
 *   GH_OWNER              仓库 owner，例如 "FalseLeonLai"（var）
 *   GH_REPO               仓库名，例如 "DouYinSparkFlow"（var）
 *   GH_WORKFLOW           workflow 文件名，例如 "schedule.yml"（var）
 *   GH_REF                触发分支，默认 "main"（var）
 *   MANUAL_TRIGGER_TOKEN  手动 HTTP 触发的鉴权 token（secret，可选）
 */

async function dispatch(env) {
  const owner = env.GH_OWNER;
  const repo = env.GH_REPO;
  const workflow = env.GH_WORKFLOW;
  const ref = env.GH_REF || "main";

  if (!env.GH_TOKEN || !owner || !repo || !workflow) {
    throw new Error(
      "Missing required env vars: GH_TOKEN / GH_OWNER / GH_REPO / GH_WORKFLOW"
    );
  }

  const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`;
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${env.GH_TOKEN}`,
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "douyin-spark-flow-trigger",
    },
    body: JSON.stringify({ ref }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`GitHub API ${resp.status}: ${text}`);
  }
  return { owner, repo, workflow, ref };
}

export default {
  // Cron 触发（定时）
  async scheduled(event, env, ctx) {
    ctx.waitUntil(
      dispatch(env)
        .then((info) =>
          console.log(`[scheduled@${event.cron}] dispatched ${info.owner}/${info.repo}/${info.workflow}@${info.ref}`)
        )
        .catch((err) => {
          console.error(`[scheduled@${event.cron}] failed:`, err);
          throw err;
        })
    );
  },

  // HTTP 触发（手动测试 / 外部联动）
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response(
        "DouYinSparkFlow trigger. POST with Authorization: Bearer <MANUAL_TRIGGER_TOKEN> to dispatch.\n",
        { status: 405 }
      );
    }
    const token = env.MANUAL_TRIGGER_TOKEN;
    if (!token) {
      return new Response("MANUAL_TRIGGER_TOKEN not configured\n", { status: 503 });
    }
    const auth = request.headers.get("authorization");
    if (auth !== `Bearer ${token}`) {
      return new Response("Unauthorized\n", { status: 401 });
    }
    try {
      const info = await dispatch(env);
      return new Response(
        `Triggered ${info.owner}/${info.repo}/${info.workflow}@${info.ref}\n`,
        { status: 200 }
      );
    } catch (err) {
      return new Response(`Failed: ${err.message}\n`, { status: 502 });
    }
  },
};
