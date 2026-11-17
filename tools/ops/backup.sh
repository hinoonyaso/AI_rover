#!/bin/sh
# Back up only the operations database to a private directory.
# 한글: 운영 DB만 사용자 전용 디렉터리에 백업한다.
set -eu
ops_root="$HOME/.local/share/jetinspect-ops"
umask 077
mkdir -p "$ops_root/backups"
file="$ops_root/backups/jetinspect-$(date +%Y%m%d-%H%M%S).sql"
LD_LIBRARY_PATH="$ops_root/mysql-root/usr/lib/aarch64-linux-gnu" "$ops_root/mysql/bin/mysqldump" --no-defaults --protocol=socket --socket="$ops_root/mysql-run/mysql.sock" --user=root --single-transaction --set-gtid-purged=OFF jetinspect > "$file"
printf '백업: %s\n' "$file"
