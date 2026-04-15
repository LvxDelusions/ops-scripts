# -*- coding: utf-8 -*-
"""
网络自动化诊断工具 V1.0
Network Auto Diagnostic Tool V1.0

跨平台：Windows / Linux
功能：多网关扫描+本机IP+路由器端口检测+外网+运营商
使用方法：
    LANG=cn python network_check.py   # 中文
    LANG=en python network_check.py   # English
    python network_check.py           # 自动检测
"""

import json
import socket
import subprocess
import sys
import threading
import os

# ==================== 多语言配置字典 ====================
LANG_CN = {
    # 标题
    "title": "网络自动化诊断工具 V1.0",
    "subtitle": "网络自动化诊断工具",
    # 状态信息
    "status": {
        "ok": "正常",
        "down": "异常",
        "na": "无",
        "na_ip": "未获取到",
        "unknown": "未知",
    },
    # 检测项目
    "items": {
        "local_ip": "本机局域网IP",
        "scanning_gateways": "正在扫描网关...",
        "no_gateway": "未检测到任何网关",
        "check_hint": "请检查网线/交换机连接",
        "gateway": "网关",
        "open_ports": "开放管理端口",
        "no_admin_ports": "未检测到管理端口",
        "internet_test": "外网连通性检测",
        "isp": "运营商",
    },
    # 报告
    "report_title": "【诊断报告】",
    "report_items": {
        "local_ip": "本机IP",
        "gateways": "存活网关",
        "gateways_count": "网关数量",
        "internet": "外网状态",
        "isp": "线路运营商",
    },
    # 运营商
    "isp_names": {
        "telecom": "中国电信",
        "uni": "中国联通",
        "mobile": "中国移动",
        "other": "其他",
    },
    # 提示
    "press_enter": "按回车键退出...",
    "exit": "已退出",
    "error": "错误",
    "get_isp_failed": "获取运营商失败",
}

LANG_EN = {
    "title": "Network Auto Diagnostic Tool V1.0",
    "subtitle": "Network Auto Diagnostic Tool",
    "status": {
        "ok": "OK",
        "down": "DOWN",
        "na": "N/A",
        "na_ip": "N/A",
        "unknown": "Unknown",
    },
    "items": {
        "local_ip": "Local IP",
        "scanning_gateways": "Scanning gateways...",
        "no_gateway": "No gateway detected",
        "check_hint": "Check cables/switches",
        "gateway": "Gateway",
        "open_ports": "Open admin ports",
        "no_admin_ports": "No admin ports",
        "internet_test": "Internet connectivity test",
        "isp": "ISP",
    },
    "report_title": "[Diagnostic Report]",
    "report_items": {
        "local_ip": "Local IP",
        "gateways": "Active Gateways",
        "gateways_count": "Gateway Count",
        "internet": "Internet",
        "isp": "ISP",
    },
    "isp_names": {
        "telecom": "China Telecom",
        "uni": "China Union",
        "mobile": "China Mobile",
        "other": "Other",
    },
    "press_enter": "Press Enter to exit...",
    "exit": "Exited",
    "error": "Error",
    "get_isp_failed": "Failed to get ISP",
}

# 语言映射
LANG_MAP = {
    "cn": LANG_CN,
    "zh": LANG_CN,
    "chinese": LANG_CN,
    "en": LANG_EN,
    "english": LANG_EN,
}


# ==================== 自动检测语言 ====================
def detect_language() -> dict:
    """自动检测系统语言环境"""
    # 1. 优先读取环境变量
    lang_env = os.environ.get("LANG", "").lower()
    for key in LANG_MAP:
        if key in lang_env:
            return LANG_MAP[key]

    # 2. 检测终端编码
    try:
        encoding = sys.stdout.encoding or ""
        if "utf-8" in encoding.lower():
            # UTF-8环境，尝试输出中文测试
            test_str = "测试中文"
            try:
                print(test_str)
                return LANG_CN  # 中文可用
            except:
                return LANG_EN
        elif "gb" in encoding.lower():
            return LANG_CN  # GBK/GB2312
    except:
        pass

    return LANG_EN  # 默认英文


# 全局语言配置
LANG = detect_language()


# ==================== 翻译函数 ====================
def t(key: str, default: str = "") -> str:
    """翻译函数 - 从字典获取翻译"""
    return LANG.get(key, default)


def ts(key: str) -> str:
    """翻译状态信息"""
    return LANG.get("status", {}).get(key, key)


def ti(key: str) -> str:
    """翻译检测项目"""
    return LANG.get("items", {}).get(key, key)

def tisp(key: str) -> str:
    """翻译运营商项目"""
    return LANG.get("isp_names", {}).get(key, key)


def tr(key: str) -> str:
    """翻译报告项目"""
    return LANG.get("report_items", {}).get(key, key)


# ==================== 网络检测功能 ====================
# 默认网关
ROUTER_GATEWAYS = [
    "192.168.0.1", "192.168.1.1", "192.168.2.1",
    "192.168.5.1", "192.168.8.1", "192.168.10.1",
    "192.168.31.1", "192.168.100.1", "192.168.168.1",
    "192.168.127.1", "192.168.1.253", "10.0.0.1",
]
# 路由器通用后台端口
ADMIN_PORTS = [80, 443, 8080, 8888]
# DNS服务器列表
DNS_LIST = ["114.114.114.114", "8.8.8.8", "223.5.5.5"]


def get_local_ip() -> str:
    """获取本机局域网IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return ts("na_ip")


def ping_ip(ip: str, timeout=0.3) -> bool:
    """跨平台PING检测"""
    try:
        cmd = (
            f"ping -n 1 -w {int(timeout * 1000)} {ip}"
            if sys.platform == "win32"
            else f"ping -c 1 -W {timeout} {ip}"
        )
        return (
            subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2,
            ).returncode
            == 0
        )
    except:
        return False


def check_port(ip: str, port: int) -> bool:
    """检测路由器管理端口"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        res = s.connect_ex((ip, port))
        s.close()
        return res == 0
    except:
        return False


def scan_all_gateways() -> list:
    """扫描所有存活网关"""
    reachable = []

    def task(ip):
        if ping_ip(ip):
            reachable.append(ip)

    threads = [threading.Thread(target=task, args=(ip,)) for ip in ROUTER_GATEWAYS]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=0.5)
    return sorted(reachable)


def check_isp() -> str:
    """检测当前网络的外网运营商信息"""
    # 外网运营商检测API
    isp_apis = [
        "https://myip.ipip.net/",
        "https://ipapi.co/json/",
    ]

    # 外网运营商检测API处理函数
    api_handlers = {
        "https://myip.ipip.net/": lambda resp: resp.stdout.strip(),
        "https://ipapi.co/json/": lambda resp: json.loads(resp.stdout).get("org", ""),
    }
    # 外网运营商检测API失败计数
    failed_count = 0
    try:
        for api_url in isp_apis:
            cmd = ["curl", "-s", "--connect-timeout", "2", api_url]
            response = subprocess.run(
                cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
            )

            if response.returncode != 0 or not response.stdout.strip():
                failed_count += 1
                continue

            isp_result = api_handlers[api_url](response)

            if "电信" in isp_result or "Chinanet" in isp_result or "Telecom" in isp_result:
                return tisp("telecom")
            elif "联通" in isp_result or "Unicom" in isp_result:
                return tisp("uni")
            elif "移动" in isp_result or "Mobile" in isp_result:
                return tisp("mobile")
            else:
                return tisp("other")

        if failed_count == len(isp_apis):
            return ts("unknown")
    except Exception as e:
        print(f"{t('get_isp_failed')}: {e}")
        return ts("error")

# ==================== 主函数 ====================
def main():
    print("=" * 60)
    print(t("title"))
    print("=" * 60)

    # 1. 本机信息
    local_ip = get_local_ip()
    print(f"\n{ti('local_ip')}：{local_ip}")

    # 2. 扫描网关
    print("\n" + ti("scanning_gateways"))
    gateways = scan_all_gateways()
    if not gateways:
        print(ti("no_gateway") + ti("check_hint"))
        print("=" * 60)
        return

    for ip in gateways:
        ports = [p for p in ADMIN_PORTS if check_port(ip, p)]
        port_str = f"{ti('open_ports')}：{ports}" if ports else ti("no_admin_ports")
        print(f"{ti('gateway')}：{ip} | {port_str}")

    # 3. 外网检测
    print("\n" + ti("internet_test"))
    internet_ok = any(ping_ip(dns) for dns in DNS_LIST)
    isp = check_isp() if internet_ok else ts("na")
    print(f"{ts('ok') if internet_ok else ts('down')} | {tr('isp')}：{isp}")

    # 4. 总结
    print("\n" + t("report_title"))
    print("-" * 30)
    print(f"{ti('local_ip')}：{local_ip}")
    print(f"{tr('gateways')}：{gateways}")
    print(f"{tr('gateways_count')}：{len(gateways)}")
    print(f"{tr('internet')}：{ts('ok') if internet_ok else ts('down')}")
    print(f"{tr('isp')}：{isp}")
    print("-" * 30)
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + t("exit"))
    except Exception as e:
        print(f"\n" + t("error") + "：" + str(e))

    if sys.platform == "win32":
        input("\n" + t("press_enter"))
