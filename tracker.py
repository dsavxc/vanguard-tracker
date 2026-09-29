import hashlib
import json
import os
import requests

CONFIG_URL = "https://clientconfig.rpg.riotgames.com/api/v1/config/public"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
VERSION_FILE = "last_vanguard_version.json"


def get_vanguard_api_info():
  try:
    res = requests.get(CONFIG_URL, timeout=10)
    data = res.json()
    version = data.get("anticheat.vanguard.version")
    url = data.get("anticheat.vanguard.url")
    return version, url
  except Exception as e:
    print(f"API取得エラー: {e}")
    return None, None


def calculate_file_hash_and_size(file_path):
  sha256_hash = hashlib.sha256()
  file_size = os.path.getsize(file_path)
  with open(file_path, "rb") as f:
    for byte_block in iter(lambda: f.read(4096), b""):
      sha256_hash.update(byte_block)
  return sha256_hash.hexdigest(), file_size


def send_discord_notification(version, download_url, file_hash, file_size_mb):
  if not DISCORD_WEBHOOK_URL:
    return
  size_str = f"{file_size_mb / (1024 * 1024):.2f} MB"
  embed = {
      "title": "🛡️ Riot Vanguard Update Detected",
      "color": 0xFF4655,
      "fields": [
          {"name": "🎮 Game / Product", "value": "VALORANT / LoL", "inline": True},
          {"name": "📦 Platform", "value": "win64_x64", "inline": True},
          {
              "name": "📊 Download Size",
              "value": f"`{size_str}`",
              "inline": True,
          },
          {
              "name": "🏷️ New Version",
              "value": f"```ini\n{version}\n```",
              "inline": False,
          },
          {
              "name": "🔑 SHA-256 Hash",
              "value": f"```css\n{file_hash}\n```",
              "inline": False,
          },
          {
              "name": "🔗 Direct Download",
              "value": f"[Click here to download]({download_url})",
              "inline": False,
          },
      ],
      "footer": {"text": "Vanguard Automated Tracker"},
  }
  requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})


def main():
  new_version, download_url = get_vanguard_api_info()
  if not new_version or not download_url:
    return

  old_version = None
  if os.path.exists(VERSION_FILE):
    with open(VERSION_FILE, "r") as f:
      old_version = json.load(f).get("version")

  if new_version != old_version:
    print(f"新しいバージョンを検知: {new_version} (旧: {old_version})")

    installer_path = "temp_vanguard_setup.exe"
    r = requests.get(download_url, stream=True)
    with open(installer_path, "wb") as f:
      for chunk in r.iter_content(chunk_size=8192):
        f.write(chunk)

    file_hash, file_size = calculate_file_hash_and_size(installer_path)
    send_discord_notification(
        new_version, download_url, file_hash, file_size
    )

    if os.path.exists(installer_path):
      os.remove(installer_path)

    with open(VERSION_FILE, "w") as f:
      json.dump({"version": new_version}, f)
  else:
    print(f"更新なし (Current: {new_version})")


if __name__ == "__main__":
  main()
