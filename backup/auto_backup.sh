#!/bin/bash

# ==============================================
# Ubuntu 自动备份脚本 V1.0
# Ubuntu Auto Backup Script V1.0

# 规则：只有 zh_CN / zh_CN.UTF-8 才输出中文
#       其他环境一律输出英文
# 远程推送：确保远程服务器已配置SSH免密登录
# ==============================================

# -------------------------- 基础配置区域 --------------------------
# 备份目录
BACKUP_SOURCES=(
    "/opt"
    "/etc"
    "/home"
)
# 备份目标目录
BACKUP_DEST="/backup/daily"
# 备份文件前缀
BACKUP_PREFIX="server_backup"
# 保留天数
RETAIN_DAYS=7
# 日志文件
LOG_FILE="/var/log/auto_backup.log"

# -------------------------- 远程备份服务器配置 --------------------------
# 推送开关：true=开启远程推送 false=关闭（仅本地备份）
ENABLE_REMOTE_SYNC=false
# 远程服务器SSH用户名
REMOTE_USER="root"
# 远程服务器IP地址
REMOTE_IP=""
# 远程服务器存储路径
REMOTE_PATH="/backup/remote"
# SSH端口
SSH_PORT=22

# -------------------------- 多语言包 --------------------------
MSG_CN=(
    "==================== 备份任务开始 ===================="
    "开始备份目录："
    "备份成功！文件："
    "，大小："
    "备份失败！请检查目录权限或磁盘空间"
    "开始清理 $RETAIN_DAYS 天前的旧备份..."
    "已删除旧备份："
    "无过期备份需要清理"
    "==================== 备份任务完成 ===================="
    "开始推送备份文件至远程服务器..."
    "远程推送成功！"
    "远程推送失败！请检查服务器配置/网络/SSH免密"
)

MSG_EN=(
    "==================== Backup Task Start ===================="
    "Starting backup directories: "
    "Backup successful! File: "
    ", Size: "
    "Backup failed! Check permissions or disk space"
    "Cleaning backups older than $RETAIN_DAYS days..."
    "Deleted old backups: "
    "No expired backups to clean"
    "==================== Backup Task Complete ===================="
    "Starting sync backup to remote server..."
    "Remote sync successful!"
    "Remote sync failed! Check config/network/SSH key"
)

# -------------------------- 语言判断 --------------------------
detect_language() {
    local lang="$LANG"
    if [[ "$lang" == "zh_CN"* ]]; then
        echo "CN"
    else
        echo "EN"
    fi
}

# 加载语言
CUR_LANG=$(detect_language)
if [ "$CUR_LANG" = "CN" ]; then
    MSG=("${MSG_CN[@]}")
else
    MSG=("${MSG_EN[@]}")
fi

# -------------------------- 执行备份 --------------------------
mkdir -p "$BACKUP_DEST"
touch "$LOG_FILE"
# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}
# 开始备份
log "${MSG[0]}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILENAME="${BACKUP_PREFIX}_${DATE}.tar.gz"
BACKUP_PATH="${BACKUP_DEST}/${BACKUP_FILENAME}"

log "${MSG[1]}${BACKUP_SOURCES[*]}"
# 执行备份
tar -czf "$BACKUP_PATH" \
    --exclude='*.log' \
    --exclude='*/tmp/*' \
    --exclude='*/temp/*' \
    "${BACKUP_SOURCES[@]}"
# 判断备份结果
if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_PATH" | awk '{print $1}')
    log "${MSG[2]}$BACKUP_FILENAME${MSG[3]}$BACKUP_SIZE"
else
    log "${MSG[4]}"
    exit 1
fi

# 清理旧备份
log "${MSG[5]}"
DELETED_FILES=$(find "$BACKUP_DEST" -name "${BACKUP_PREFIX}_*.tar.gz" -mtime +$RETAIN_DAYS -print -delete)

if [ -n "$DELETED_FILES" ]; then
    log "${MSG[6]}"
    log "$DELETED_FILES"
else
    log "${MSG[7]}"
fi

# -------------------------- 远程推送逻辑 --------------------------
if [ "$ENABLE_REMOTE_SYNC" = true ]; then
    # 校验远程配置是否填写
    if [ -z "$REMOTE_USER" ] || [ -z "$REMOTE_IP" ] || [ -z "$REMOTE_PATH" ]; then
        log "远程推送配置不完整，请填写用户名/IP/存储路径"
    else
        log "${MSG[9]}"
        # 执行远程推送（rsync+SSH）
        rsync -avz -e "ssh -p $SSH_PORT" "$BACKUP_PATH" "$REMOTE_USER@$REMOTE_IP:$REMOTE_PATH/"
        # 判断推送结果
        if [ $? -eq 0 ]; then
            log "${MSG[10]}"
        else
            log "${MSG[11]}"
        fi
    fi
fi

# 结束日志
log "${MSG[8]}"
echo "" >> "$LOG_FILE"