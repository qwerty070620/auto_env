"""工具函数 - 系统命令执行与环境检测"""

from __future__ import annotations
import subprocess
import platform
import shutil
import os
import sys
import re
import shlex
from typing import Optional

# 依赖名安全校验：允许字母数字_-.@, scoped 包名 (@scope/name), Maven group:artifact
_SAFE_DEP_NAME = re.compile(r'^@?[a-zA-Z0-9][a-zA-Z0-9_\-\.]*(/[a-zA-Z0-9][a-zA-Z0-9_\-\.]*)*(\[[^\]]*\])*(:[a-zA-Z0-9][a-zA-Z0-9_\-\.]*)*$')

# 常见大目录 -- 遍历时要跳过
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", ".tox",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "target", "build",
    "dist", ".gradle", ".idea", ".vscode", "vendor", "bower_components",
    ".next", ".nuxt", ".output", ".svelte-kit",
}

# 最大遍历深度
MAX_SCAN_DEPTH = 4


def is_safe_dep_name(name: str) -> bool:
    """检查依赖名是否安全（不包含命令注入字符）"""
    return bool(_SAFE_DEP_NAME.match(name))


def sanitize_for_cmd(value: str, max_len: int = 200) -> str:
    """安全化参数：截断长度 + 仅允许安全字符"""
    value = value.strip()[:max_len]
    if not is_safe_dep_name(value):
        # 如果不安全，取安全子串
        safe = re.sub(r'[^a-zA-Z0-9_\-\.@/:]', '', value)[:80]
        return safe or "unknown"
    return value


def run_cmd(cmd: str, timeout: int = 10) -> tuple[bool, str]:
    """
    执行命令并返回 (成功, 输出)。跨平台兼容。
    注意：永远不要将用户输入直接拼接到此命令中；
    调用方应先用 sanitize_for_cmd() 过滤所有外部来源的参数。
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding=_get_system_encoding(),
            errors="replace",
            env=_get_safe_env(),
        )
        output = result.stdout.strip() or result.stderr.strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "(超时)"
    except FileNotFoundError:
        return False, "(命令不存在)"
    except Exception as e:
        return False, str(e)


def run_cmd_safe(args: list[str], timeout: int = 10) -> tuple[bool, str]:
    """
    安全命令执行：使用列表传参 + shell=False，杜绝命令注入。
    当命令无需 shell 特性时请优先使用此函数。
    """
    try:
        result = subprocess.run(
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding=_get_system_encoding(),
            errors="replace",
            env=_get_safe_env(),
        )
        output = result.stdout.strip() or result.stderr.strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "(超时)"
    except FileNotFoundError:
        return False, "(命令不存在)"
    except Exception as e:
        return False, str(e)


def _get_system_encoding() -> str:
    """获取系统终端编码（优先 cp65001/utf-8，其次系统默认）"""
    if sys.stdout.encoding and sys.stdout.encoding.lower() in ('utf-8', 'cp65001'):
        return 'utf-8'
    return sys.stdout.encoding or sys.getdefaultencoding() or 'utf-8'


def _get_safe_env() -> dict:
    """构建安全环境变量，移除可能干扰的命令"""
    env = os.environ.copy()
    env.pop("PYTHONSTARTUP", None)
    env["PYTHONUNBUFFERED"] = "1"
    return env


def check_tool_installed(tool_name: str, check_cmd: Optional[str] = None) -> bool:
    """检查某个工具是否已安装"""
    safe_name = sanitize_for_cmd(tool_name)
    if check_cmd is None:
        check_cmd = f"{safe_name} --version"
    else:
        # check_cmd 是检测器内部硬编码的命令（非用户输入），只拒绝危险字符
        if re.search(r'[;&`$(){}<>]|\|\|', check_cmd):
            return False
        # 不过 sanitize_for_cmd，保留单管道符，拒绝 ||
    success, _ = run_cmd(check_cmd)
    if not success:
        cmd = "where" if platform.system() == "Windows" else "which"
        success, _ = run_cmd(f"{cmd} {safe_name}")
    return success


def get_os_info() -> dict:
    """获取操作系统信息"""
    system = platform.system()
    return {
        "system": system,
        "release": platform.release(),
        "version": platform.version(),
        "is_windows": system == "Windows",
        "is_mac": system == "Darwin",
        "is_linux": system == "Linux",
    }


def has_shell_command(cmd: str) -> bool:
    """检查某个 shell 命令是否可用"""
    return shutil.which(cmd) is not None


def scan_project_files(project_dir: str) -> list[str]:
    """扫描项目目录下所有文件名（非递归，只一层）"""
    files = []
    try:
        for name in os.listdir(project_dir):
            fpath = os.path.join(project_dir, name)
            if os.path.isfile(fpath):
                files.append(name)
    except PermissionError:
        pass
    return files


# 颜色输出 (ANSI)
class Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

# 终端 Emoji 能力检测 (A6)
def _supports_emoji() -> bool:
    """检测终端是否支持 Emoji 显示"""
    # 终端编码必须是 UTF-8 系列
    enc = (sys.stdout.encoding or '').lower()
    if 'utf' not in enc and 'cp65001' not in enc:
        return False
    if platform.system() == "Windows":
        ver = platform.version()
        try:
            if "10." in ver:
                build = int(ver.split(".")[-1]) if ver.split(".")[-1].isdigit() else 0
                return build >= 16299
        except (ValueError, IndexError):
            pass
        return False
    term = os.environ.get("TERM", "")
    lang = os.environ.get("LANG", "")
    return "256color" in term or "utf" in lang.lower() or "UTF" in lang


_HAS_EMOJI = _supports_emoji()


def emoji(text: str, fallback: str = "") -> str:
    """根据终端能力返回 Emoji 或 ASCII 替代"""
    return text if _HAS_EMOJI else fallback


def print_colored(text: str, color: str = Color.RESET):
    """带颜色打印（终端支持 ANSI 时）"""
    try:
        # Windows 下可能需要处理编码
        encoded = f"{color}{text}{Color.RESET}"
        print(encoded.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8', errors='replace'))
    except Exception:
        try:
            print(text)
        except Exception:
            print(text.encode('ascii', errors='replace').decode('ascii'))
