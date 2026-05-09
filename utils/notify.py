"""
utils/notify.py
任务运行通知。支持飞书自定义机器人 / 企业微信群机器人。

环境变量：
- NOTIFY_TYPE: 逗号分隔的通知渠道，如 "feishu" / "wecom" / "feishu,wecom"。空表示禁用。
- FEISHU_WEBHOOK_URL: 飞书机器人 webhook 完整 URL
- WECOM_WEBHOOK_URL: 企业微信机器人 webhook 完整 URL
"""

import os
import requests

from utils.logger import setup_logger

logger = setup_logger(name="notify")


def _send_feishu(webhook: str, title: str, content: str, success: bool) -> None:
    template = "green" if success else "red"
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "template": template,
                "title": {"tag": "plain_text", "content": title},
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": content}}
            ],
        },
    }
    resp = requests.post(webhook, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("StatusCode", data.get("code", 0)) not in (0, None):
        raise RuntimeError(f"飞书返回非 0：{data}")


def _send_wecom(webhook: str, title: str, content: str, success: bool) -> None:
    icon = "✅" if success else "❌"
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": f"## {icon} {title}\n\n{content}"},
    }
    resp = requests.post(webhook, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("errcode", 0) != 0:
        raise RuntimeError(f"企业微信返回非 0：{data}")


_DISPATCH = {
    "feishu": ("FEISHU_WEBHOOK_URL", _send_feishu),
    "wecom": ("WECOM_WEBHOOK_URL", _send_wecom),
}


def notify(title: str, content: str, success: bool = True) -> None:
    """
    根据 NOTIFY_TYPE 环境变量发送通知。配置缺失时静默跳过，单渠道失败不影响其它渠道。
    """
    raw = os.getenv("NOTIFY_TYPE", "").strip()
    if not raw:
        return

    channels = [c.strip().lower() for c in raw.split(",") if c.strip()]
    for channel in channels:
        entry = _DISPATCH.get(channel)
        if not entry:
            logger.warning(f"未知通知渠道：{channel}")
            continue
        env_key, sender = entry
        webhook = os.getenv(env_key, "").strip()
        if not webhook:
            logger.warning(f"渠道 {channel} 未配置 {env_key}，已跳过")
            continue
        try:
            sender(webhook, title, content, success)
            logger.info(f"已发送 {channel} 通知")
        except Exception as e:
            logger.warning(f"发送 {channel} 通知失败：{e}")


if __name__ == "__main__":
    # 手动测试：python -m utils.notify
    notify("测试通知", "这是一条来自 DouYinSparkFlow 的测试消息。", success=True)
