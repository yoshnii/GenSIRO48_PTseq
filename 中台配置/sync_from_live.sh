#!/usr/bin/env bash
# 把"线上"中台配置 db 同步进本 repo，并重新导出可 diff 的 SQL dump。
# 线上 db 是机器人软件实际读取的那份；repo 里的是版本化副本。
# 改完线上配置后跑这个脚本，再 git add / commit。
set -euo pipefail

LIVE="/Users/shan/Documents/BGI/SIRO解决方案中心/SIRO48PTseq开发/GenSIRO48_PTseq/中台配置/GenSIRO48-PTseq/Database"
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$HERE/GenSIRO48-PTseq/Database"

mkdir -p "$DEST"
cp "$LIVE/SIRO16productV4.db" "$DEST/SIRO16productV4.db"
sqlite3 "$DEST/SIRO16productV4.db" .dump > "$DEST/SIRO16productV4.sql"

echo "已同步:"
echo "  $DEST/SIRO16productV4.db"
echo "  $DEST/SIRO16productV4.sql"
echo "接着: cd '$HERE/..' && git add 中台配置 && git status  (确认后再 commit)"
