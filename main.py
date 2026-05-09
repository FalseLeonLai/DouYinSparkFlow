# 尝试从 .env 文件加载环境变量
import os
if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv(".env")

import traceback

from core.tasks import runTasks
from utils.notify import notify


def _format_summary(results):
    if not results:
        return "（无可执行账号）"
    lines = []
    total_sent = 0
    total_failed_accounts = 0
    for username, sent, err in results:
        if err:
            total_failed_accounts += 1
            lines.append(f"- ❌ **{username}**：异常 `{err}`")
        else:
            total_sent += len(sent)
            friends = "、".join(sent) if sent else "（无）"
            lines.append(f"- ✅ **{username}**：发送 {len(sent)} 个 — {friends}")
    header = f"账号 {len(results)} 个，成功发送 {total_sent} 条，账号异常 {total_failed_accounts} 个"
    return header + "\n\n" + "\n".join(lines)


def main():
    try:
        results = runTasks()
    except Exception:
        err = traceback.format_exc()
        notify("续火花运行失败", f"```\n{err}\n```", success=False)
        raise

    summary = _format_summary(results)
    has_failure = any(err for _, _, err in results)
    notify(
        "续火花运行完成（含异常）" if has_failure else "续火花运行完成",
        summary,
        success=not has_failure,
    )


if __name__ == "__main__":
    main()
