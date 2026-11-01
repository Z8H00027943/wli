#!/usr/bin/env python3
"""Update one Discord webhook embed with Minecraft Java server status."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def fetch_status(address: str) -> dict:
    endpoint = "https://api.mcsrvstat.us/3/" + urllib.parse.quote(address, safe=".:-[]")
    req = urllib.request.Request(
        endpoint,
        headers={
            "User-Agent": "WLICraft-Discord-Status/1.0 (server status display)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def embed_for(address: str, info: dict) -> dict:
    online = info.get("online") is True
    players = info.get("players") or {}
    online_count = players.get("online", "?") if online else "—"
    max_count = players.get("max", "?") if online else "—"
    last_check = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return {
        "title": "wli craft | Server Status",
        "color": 0x2ECC71 if online else 0xED4245,
        "fields": [
            {"name": "الحالة | Status", "value": "🟢 Online | شغال" if online else "🔴 Offline | طافي", "inline": False},
            {"name": "اللاعبون | Players", "value": f"{online_count}/{max_count}" if online else "غير متاح (Offline)", "inline": False},
            {"name": "الآيبي | Server IP", "value": f"`{address}`", "inline": False},
        ],
        "footer": {"text": {last_check} • Last Check 5 minutes Ago"},
    }


def update_message(webhook_url: str, message_id: str, embed: dict) -> None:
    base = webhook_url.rstrip("/").split("?", 1)[0]
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme != "https" or parsed.hostname not in ("discord.com", "discordapp.com"):
        raise ValueError("DISCORD_WEBHOOK_URL must be an official Discord webhook URL")
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 4 or parts[:2] != ["api", "webhooks"]:
        raise ValueError("DISCORD_WEBHOOK_URL format is invalid")
    if not message_id.isdigit():
        raise ValueError("DISCORD_MESSAGE_ID must be the numeric ID from the message link")
    endpoint = f"{base}/messages/{message_id}"
    payload = json.dumps({"embeds": [embed], "allowed_mentions": {"parse": []}}).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        method="PATCH",
        headers={"Content-Type": "application/json", "User-Agent": "WLICraft-Status-Updater/1.0"},
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError(f"Discord replied HTTP {response.status}")


def main() -> None:
    url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    message_id = os.environ.get("DISCORD_MESSAGE_ID", "").strip()
    address = os.environ.get("MC_SERVER_ADDRESS", "CE5MF.aternos.me").strip()
    if not url or not message_id or not address:
        raise ValueError("Set DISCORD_WEBHOOK_URL and DISCORD_MESSAGE_ID, plus optional MC_SERVER_ADDRESS")
    info = fetch_status(address)
    update_message(url, message_id, embed_for(address, info))
    print(f"Updated Discord embed for {address}. Online: {info.get('online') is True}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, urllib.error.HTTPError, RuntimeError) as exc:
        print(f"Update failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
