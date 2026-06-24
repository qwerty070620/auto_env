#!/usr/bin/env python3
"""
AutoEnv — 万能开源项目环境自动检测与安装器

    将任何开源项目目录放进来，自动识别：
      - 语言/框架类型（Python/Node/Rust/Go/Java/Ruby/PHP/.NET/C++/Docker/K8s/Shell...）
      - 运行时版本需求
      - 所有包依赖（含版本号）
      - 系统级工具（数据库、ffmpeg、Git 等）
      - Compose 服务（Redis、PostgreSQL 等）

    然后交互式地让你选择要安装哪些依赖。

用法:
    python -m auto_env <项目目录>              检测 → 交互式选择 → 安装
    python -m auto_env <项目目录> -y           检测 → 确认 → 全部安装
    python -m auto_env <项目目录> --no-install  仅检测，不安装
    python -m auto_env <项目目录> --json        JSON 格式输出
    python -m auto_env <项目目录> --generate    生成 Dockerfile / devcontainer
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import re

from .detectors import ALL_DETECTORS, DetectionResult, DepInfo
from .detectors.base import DepType
from .system_deps import detect_system_deps
from .installer import Installer
from .utils import Color, print_colored, get_os_info, check_tool_installed, run_cmd, run_cmd_safe, SKIP_DIRS, MAX_SCAN_DEPTH, emoji as _e


# 全局 verbose 标志
_VERBOSE = False


def detect_project(project_dir: str) -> list[DetectionResult]:
    """扫描目录，检测所有匹配的项目类型"""
    results: list[DetectionResult] = []
    for DetectorClass in ALL_DETECTORS:
        try:
            result = DetectorClass.detect(project_dir)
            if result and result.deps:
                results.append(result)
        except Exception as e:
            if _VERBOSE:
                msg = str(e)[:150]
                print_colored(f"  ⚠️  {DetectorClass.NAME} 检测器出错: {msg}", Color.YELLOW)
    if not results:
        results = _fallback_detect(project_dir)
    return results


def _fallback_detect(project_dir: str) -> list[DetectionResult]:
    """通用回退检测 — 根据文件后缀猜测，跳过常见大目录和深层目录"""
    from .detectors.base import DetectionResult
    result = DetectionResult(
        project_type="unknown",
        project_name=os.path.basename(os.path.abspath(project_dir)),
        notes=["未检测到标准的项目配置文件，以下是根据文件类型猜测的结果"],
    )
    ext_map = {
        ".py": "python", ".js": "nodejs", ".ts": "nodejs/typescript",
        ".rs": "rust", ".go": "go", ".java": "java", ".rb": "ruby",
        ".php": "php", ".cs": "dotnet/c#", ".c": "c", ".cpp": "c++",
        ".h": "c/c++", ".sh": "shell", ".ps1": "powershell",
        ".swift": "swift", ".kt": "kotlin", ".scala": "scala",
        ".ex": "elixir", ".exs": "elixir", ".hs": "haskell",
        ".jl": "julia", ".r": "r", ".pl": "perl", ".dart": "dart",
        ".tf": "terraform", ".hcl": "terraform",
    }
    ext_count = {}
    for root, dirs, _ in os.walk(project_dir, topdown=True):
        # 跳过常见大目录
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        # 深度限制
        depth = root.replace(project_dir, "").count(os.sep)
        if depth > MAX_SCAN_DEPTH:
            dirs[:] = []  # 不继续深入
            continue
        try:
            for f in os.listdir(root):
                fpath = os.path.join(root, f)
                if os.path.isfile(fpath):
                    _, ext = os.path.splitext(f)
                    if ext in ext_map:
                        ext_count[ext] = ext_count.get(ext, 0) + 1
        except PermissionError:
            pass
    if ext_count:
        top_ext = sorted(ext_count.items(), key=lambda x: x[1], reverse=True)[:5]
        for ext, count in top_ext:
            result.notes.append(f"  {count}个{ext}文件 → 可能是{ext_map[ext]}项目")
    return [result]


def print_detection_report(results: list[DetectionResult], os_info: dict, project_dir: str) -> list[DepInfo]:
    """打印检测报告，返回所有依赖的扁平列表"""
    print_colored("\n" + "=" * 62, Color.BLUE)
    print_colored(f" {_e('🔍', '[>]')}  AutoEnv — 万能开源项目环境自动检测器", Color.BOLD)
    print_colored("=" * 62, Color.BLUE)
    print(f"  {_e('📁', '[D]')} 项目: {project_dir}")
    print(f"  {_e('💻', '[O]')} 系统: {os_info['system']} {os_info['release']}")
    print(f"  {_e('🎯', '[=]')} 识别到 {len(results)} 个项目类型")

    all_deps: list[DepInfo] = []
    dedup = set()

    for i, result in enumerate(results, 1):
        print_colored(f"\n{'─' * 56}", Color.CYAN)
        type_emoji = _type_emoji(result.project_type)
        fw_str = f" | 框架: {result.framework}" if result.framework else ""
        print_colored(f" [{i}] {type_emoji} {result.project_type.upper()}{fw_str}", Color.BOLD)
        if result.project_name:
            print(f"     名称: {result.project_name}")
        if result.config_files:
            shown = result.config_files[:6]
            more = f" ...等{len(result.config_files)}个" if len(result.config_files) > 6 else ""
            print(f"     配置: {', '.join(shown)}{more}")
        for note in result.notes:
            print_colored(f"     ℹ️  {note}", Color.YELLOW)

        deps_by_type: dict[DepType, list[DepInfo]] = {}
        for dep in result.deps:
            deps_by_type.setdefault(dep.dep_type, []).append(dep)

        type_config = {
            DepType.RUNTIME: (_e("🔧", "[rt]") + " 运行时", Color.GREEN),
            DepType.BUILD_TOOL: (_e("🛠️", "[bt]") + " 构建工具", Color.CYAN),
            DepType.PACKAGE: (_e("📦", "[pk]") + " 包依赖", Color.YELLOW),
            DepType.SYSTEM: (_e("💻", "[sy]") + " 系统依赖", Color.BLUE),
            DepType.SERVICE: (_e("☁️", "[sv]") + " 服务", Color.BLUE),
        }

        for dt in DepType:
            if dt in deps_by_type:
                items = deps_by_type[dt]
                label, col = type_config.get(dt, (dt.value, Color.RESET))
                print_colored(f"\n     {label} ({len(items)}个):", col)
                for dep in items:
                    installed = check_tool_installed(dep.name, dep.check_command) if dep.check_command else False
                    dep.is_installed = installed
                    icon = _e("✅", "[Y]") if installed else _e("⬜", "[ ]")
                    ver = f" v{dep.version}" if dep.version else ""
                    print(f"       {icon} {dep.name}{ver}")
                    if dep.name not in dedup:
                        dedup.add(dep.name)
                        all_deps.append(dep)

    # 系统依赖
    print_colored(f"\n{'─' * 56}", Color.CYAN)
    print_colored(" [系统] 文档级依赖检测 (扫描 README/文档)", Color.BOLD)
    sys_deps = detect_system_deps(project_dir)
    if sys_deps:
        for dep in sys_deps:
            icon = _e("✅", "[Y]") if dep.is_installed else _e("⬜", "[ ]")
            print(f"       {icon} {dep.name}")
            if dep.name not in dedup:
                dedup.add(dep.name)
                all_deps.append(dep)
    else:
        print("       未检测到")

    # 汇总
    print_colored(f"\n{'=' * 62}", Color.BLUE)
    total = len(all_deps)
    installed = sum(1 for d in all_deps if d.is_installed)
    missing = total - installed
    print_colored(f" {_e('📊', '[=]')} 总计 {total} 个依赖 | {_e('✅', '[Y]')} 已装 {installed} | {_e('⬜', '[ ]')} 缺 {missing}", Color.BOLD)

    return all_deps


def _type_emoji(project_type: str) -> str:
    """返回项目类型图标（终端不支持 Emoji 时自动回退）"""
    emoji_map = {
        "python": _e("🐍", "[Py]"), "nodejs": _e("🟢", "[JS]"),
        "rust": _e("🦀", "[Rs]"), "go": _e("🔵", "[Go]"),
        "java": _e("☕", "[Jv]"), "ruby": _e("💎", "[Rb]"),
        "php": _e("🐘", "[Ph]"), "dotnet": _e("🟣", "[.N]"),
        "cpp": _e("⚙️", "[C+]"), "docker": _e("🐳", "[Dk]"),
        "infra": _e("🏗️", "[If]"), "shell": _e("💻", "[Sh]"),
        "r": _e("📊", "[R_]"), "perl": _e("🐪", "[Pl]"),
        "haskell": _e("λ", "[Hs]"), "elixir": _e("💧", "[Ex]"),
        "dart": _e("🎯", "[Dr]"), "julia": _e("🔬", "[Jl]"),
        "swift": _e("🦅", "[Sw]"), "kotlin_scala": _e("🎭", "[KS]"),
        "deno": _e("🦕", "[Dn]"), "unknown": _e("❓", "[??]"),
    }
    return emoji_map.get(project_type, _e("📋", "-"))


def interactive_select(deps: list[DepInfo]) -> list[DepInfo]:
    """交互式选择要安装的依赖"""
    missing = [d for d in deps if not d.is_installed]
    if not missing:
        print_colored(f"\n{_e('🎉', ':)')} 所有依赖已安装，无需操作！", Color.GREEN)
        return []

    print_colored(f"\n{'─' * 56}", Color.CYAN)
    print_colored(f" {_e('📋', '[?]')} 以下 {len(missing)} 个依赖尚未安装：", Color.BOLD)

    type_emoji_map = {
        DepType.RUNTIME: _e("🔧", "[rt]"), DepType.BUILD_TOOL: _e("🛠️", "[bt]"),
        DepType.PACKAGE: _e("📦", "[pk]"), DepType.SYSTEM: _e("💻", "[sy]"), DepType.SERVICE: _e("☁️", "[sv]"),
    }

    for i, dep in enumerate(missing, 1):
        emoji = type_emoji_map.get(dep.dep_type, _e("❓", "[?]"))
        ver = f" ({dep.version})" if dep.version else ""
        cmd_hint = f"\n         → {dep.install_command}" if dep.install_command and len(dep.install_command) < 60 else ""
        print(f"  {i:>3}. {emoji} [{dep.dep_type.value:7}] {dep.name}{ver}{cmd_hint}")

    print(f"\n  💡 输入要安装的编号，用逗号/空格分隔")
    print(f"      例: 1,3,5-8  或  all  或  1 2 3  或  packages(仅包依赖)")
    print(f"      直接回车 = 跳过安装")

    while True:
        try:
            choice = input(f"\n  👉 请选择: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  已取消")
            return []

        if choice in ("", "none", "no", "n"):
            print_colored("  ⏭️  跳过安装", Color.YELLOW)
            return []

        if choice in ("all", "a", "yes", "y"):
            return missing

        if choice in ("packages", "pkg"):
            return [d for d in missing if d.dep_type == DepType.PACKAGE]

        indices = set()
        parts = re.split(r'[,;\s]+', choice)
        valid = True
        for part in parts:
            if not part:
                continue
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    for j in range(int(a), int(b) + 1):
                        if 1 <= j <= len(missing):
                            indices.add(j)
                        else:
                            print_colored(f"  ⚠️  编号 {j} 超出范围 (1-{len(missing)})", Color.RED)
                            valid = False
                except ValueError:
                    print_colored(f"  ⚠️  无效范围: {part}", Color.RED)
                    valid = False
            else:
                try:
                    j = int(part)
                    if 1 <= j <= len(missing):
                        indices.add(j)
                    else:
                        print_colored(f"  ⚠️  编号 {j} 超出范围 (1-{len(missing)})", Color.RED)
                        valid = False
                except ValueError:
                    print_colored(f"  ⚠️  无法识别: {part}", Color.RED)
                    valid = False

        if valid and indices:
            selected = [missing[i - 1] for i in sorted(indices)]
            print_colored(f"  ✅ 已选择 {len(selected)} 个依赖", Color.GREEN)
            return selected

        print_colored("  ↩️  请重新输入", Color.YELLOW)


def output_json(results: list[DetectionResult], project_dir: str, os_info: dict):
    """JSON 输出 — 正确反映安装状态 (H4 修复)"""
    output = {"project_dir": project_dir, "os": os_info, "detected": []}
    for r in results:
        # 实时检查每个依赖的安装状态
        deps_json = []
        for d in r.deps:
            is_inst = check_tool_installed(d.name, d.check_command) if d.check_command else False
            d.is_installed = is_inst
            deps_json.append({
                "name": d.name, "type": d.dep_type.value,
                "version": d.version, "installed": is_inst,
                "install_command": d.install_command,
            })
        output["detected"].append({
            "type": r.project_type, "name": r.project_name,
            "framework": r.framework, "config_files": r.config_files,
            "notes": r.notes, "deps": deps_json,
        })
    sys_deps = detect_system_deps(project_dir)
    if sys_deps:
        output["system_deps"] = [{
            "name": d.name, "type": "system",
            "installed": d.is_installed,
            "install_command": d.install_command,
        } for d in sys_deps]
    if hasattr(sys.stdout, 'buffer'):
        data = json.dumps(output, ensure_ascii=False, indent=2)
        sys.stdout.buffer.write(data.encode('utf-8'))
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


def generate_dockerfile(results: list[DetectionResult], project_dir: str) -> str:
    lines = ["# AutoEnv 自动生成的 Dockerfile", ""]
    # 根据检测结果推导基础镜像（优先从项目中提取版本信息）
    image_map = {
        "python": "python:3.12-slim", "nodejs": "node:20-slim",
        "rust": "rust:latest-slim", "go": "golang:1.23-slim",
        "java": "eclipse-temurin:21-jre", "ruby": "ruby:3.3-slim",
        "php": "php:8.3-cli", "dotnet": "mcr.microsoft.com/dotnet/sdk:8.0",
        "elixir": "hexpm/elixir:latest-erlang-ubuntu-noble",
        "deno": "denoland/deno:latest",
        "swift": "swift:latest",
        "haskell": "haskell:latest-slim",
        "cpp": "gcc:14", "dart": "dart:stable-sdk",
        "julia": "julia:1.10-bookworm",
    }
    image = "ubuntu:24.04"
    for r in results:
        if r.project_type in image_map:
            image = image_map[r.project_type]
            break

    lines.append(f"FROM {image}")
    lines.append("")
    lines.append("WORKDIR /app")
    lines.append("COPY . .")
    lines.append("")

    types = {r.project_type for r in results}
    if "python" in types:
        lines.append("RUN pip install --no-cache-dir -r requirements.txt 2>&1 || pip install . 2>&1")
    if "nodejs" in types:
        lines.append("RUN npm ci 2>&1 || npm install 2>&1")
    if "rust" in types:
        lines.append("RUN cargo build --release")
    if "go" in types:
        lines.append("RUN go mod download 2>&1 && go build -o /app/bin/app . 2>&1")

    lines.append("")
    lines.append('CMD ["echo", "请根据项目配置启动命令"]')
    return "\n".join(lines)


def generate_devcontainer(results: list[DetectionResult], project_dir: str) -> str:
    config = {
        "name": os.path.basename(os.path.abspath(project_dir)),
        "image": "mcr.microsoft.com/devcontainers/universal:2",
        "features": {},
        "postCreateCommand": "",
    }
    types = {r.project_type for r in results}
    exts = []
    if "python" in types:
        exts += ["ms-python.python", "ms-python.vscode-pylance"]
        config["postCreateCommand"] = "pip install -r requirements.txt 2>&1"
    if "nodejs" in types:
        exts += ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode"]
    if "rust" in types:
        exts += ["rust-lang.rust-analyzer"]
    if "go" in types:
        exts += ["golang.go"]
    if exts:
        config["customizations"] = {"vscode": {"extensions": exts}}
    return json.dumps(config, ensure_ascii=False, indent=2)


def _validate_url(url: str) -> bool:
    """校验 URL 安全性：拒绝 shell 元字符、阻止内网地址 (C1 + M6)"""
    if re.search(r'[$`;|&(){}<>]', url):
        return False
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in ('http', 'https', 'git'):
        return False
    if parsed.scheme == 'http':
        print_colored(" ❌ 不接受 HTTP 连接，请使用 HTTPS", Color.RED)
        return False
    hostname = (parsed.hostname or '').lower()
    if hostname in ('localhost', '127.0.0.1', '::1', '0.0.0.0'):
        return False
    if hostname.startswith('169.254.') or hostname.startswith('10.') or hostname.startswith('172.16.'):
        return False
    if hostname.startswith('192.168.'):
        return False
    if '@' in parsed.netloc and not url.startswith('git@'):
        return False
    return True


def download_project(url: str, target_dir: str) -> str | None:
    """下载开源项目：支持 Git 仓库 URL 和 ZIP 直链"""
    from urllib.parse import urlparse

    if not _validate_url(url):
        print_colored(" ❌ URL 不合法（包含危险字符、或指向内网地址）", Color.RED)
        return None

    parsed = urlparse(url)
    repo_name = os.path.basename(parsed.path).replace(".git", "") or "downloaded_project"
    repo_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', repo_name)[:100] or "downloaded_project"

    is_github = "github.com" in parsed.netloc.lower()
    is_git = url.endswith(".git") or is_github

    if is_git:
        git_ok, _ = run_cmd_safe(["git", "--version"], timeout=5)
        if git_ok:
            dest = os.path.join(target_dir, repo_name)
            print_colored(f"\n 📥 Git 克隆: {url}", Color.CYAN)
            print_colored(f"    目标: {dest}", Color.CYAN)
            ok, out = run_cmd_safe(["git", "clone", "--depth=1", url, dest], timeout=300)
            if ok:
                print_colored(f"    ✅ 克隆成功", Color.GREEN)
                return dest
            else:
                print_colored(f"    ❌ Git 克隆失败: {out[:200]}", Color.RED)
        else:
            print_colored("    ⚠️  未安装 Git，尝试 ZIP 下载...", Color.YELLOW)

    # 回退：下载 ZIP，带大小限制 (H3)
    zip_url = url.rstrip("/")
    if is_github:
        zip_url = f"{zip_url}/archive/refs/heads/main.zip"

    dest_dir = os.path.join(target_dir, repo_name)
    zip_path = os.path.join(target_dir, f"{repo_name}.zip")
    MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024   # 500 MB
    MAX_UNZIP_BYTES = 1024 * 1024 * 1024     # 1 GB

    print_colored(f"\n 📥 下载: {zip_url}", Color.CYAN)
    try:
        import urllib.request
        import shutil

        def reporthook(count, block_size, total_size):
            if total_size > 0:
                pct = min(count * block_size * 100 // total_size, 100)
                print(f"\r    下载进度: {pct}%", end="", flush=True)
            elif total_size < 0:
                if count * block_size > MAX_DOWNLOAD_BYTES:
                    raise MemoryError(f"下载超过 {MAX_DOWNLOAD_BYTES//1024//1024}MB 限制")

        urllib.request.urlretrieve(zip_url, zip_path, reporthook=reporthook)
        print()

        file_size = os.path.getsize(zip_path)
        if file_size > MAX_DOWNLOAD_BYTES:
            os.remove(zip_path)
            print_colored(f"    ❌ 文件过大 ({file_size//1024//1024}MB)，上限 {MAX_DOWNLOAD_BYTES//1024//1024}MB", Color.RED)
            return None

        # 解压（带路径穿越防护 + 大小限制 + realpath 规范化）(H2 + H3)
        print_colored("    📦 解压中...", Color.CYAN)
        import zipfile
        target_abs = os.path.realpath(target_dir)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            total_unzipped = 0
            prefix = None
            safe_members = []
            for member in zf.namelist():
                resolved = os.path.realpath(os.path.join(target_dir, member))
                if not resolved.startswith(target_abs + os.sep) and resolved != target_abs:
                    raise ValueError(f"安全检查: 路径穿越 — {member}")
                info = zf.getinfo(member)
                if info.is_symlink():
                    continue  # 跳过符号链接
                total_unzipped += info.file_size
                if total_unzipped > MAX_UNZIP_BYTES:
                    raise ValueError(f"解压后超 {MAX_UNZIP_BYTES//1024//1024//1024}GB 限制 (Zip 炸弹)")
                safe_members.append(member)
                if prefix is None:
                    prefix = member.split("/")[0] if "/" in member else None
            # 只提取已验证的成员
            for member in safe_members:
                zf.extract(member, target_dir)
            extracted = os.path.join(target_dir, prefix) if prefix else dest_dir

        os.remove(zip_path)

        if extracted != dest_dir and os.path.isdir(extracted):
            if os.path.isdir(dest_dir):
                shutil.rmtree(dest_dir, ignore_errors=True)
            shutil.move(extracted, dest_dir)
            if os.path.isdir(extracted):
                shutil.rmtree(extracted, ignore_errors=True)

        print_colored(f"    ✅ 下载完成: {dest_dir}", Color.GREEN)
        return dest_dir

    except Exception as e:
        if os.path.isfile(zip_path):
            try:
                os.remove(zip_path)
            except Exception:
                pass
        print_colored(f"    ❌ 下载失败: {e}", Color.RED)
        return None


def resolve_target(project_arg: str) -> str | None:
    """解析目标：可能是本地路径 or GitHub URL or 粘贴板内容"""
    import os

    # 本地路径
    if os.path.isdir(project_arg):
        return os.path.abspath(project_arg)

    # Git / HTTP URL
    if re.match(r'^https?://|^git@', project_arg):
        print_colored("\n 🔗 检测到远程仓库 URL，正在下载...", Color.BOLD)
        downloads_dir = os.path.join(os.getcwd(), "auto_env_downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        result = download_project(project_arg, downloads_dir)
        if result:
            return result
        print_colored(" ❌ 无法下载项目，请检查 URL 或网络", Color.RED)
        return None

    # 不是一个可识别路径
    print_colored(f" ❌ 路径不存在或无法识别的输入: {project_arg}", Color.RED)
    return None


def main():
    parser = argparse.ArgumentParser(
        description="AutoEnv — 万能开源项目环境自动检测与安装器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m auto_env ./my-project              检测 → 交互式选择 → 安装
  python -m auto_env https://github.com/xxx/yyy  自动下载 → 检测 → 交互安装
  python -m auto_env ./my-project -y           跳过交互，全部安装
  python -m auto_env ./my-project --no-install  仅检测报告
  python -m auto_env ./my-project --json        JSON 输出
  python -m auto_env ./my-project --generate    生成 Dockerfile
  双击 启动.bat                                 图形化一键启动菜单
        """,
    )
    parser.add_argument("target", nargs="?", default=None,
                        help="项目目录路径 或 GitHub URL (如 https://github.com/user/repo)")
    parser.add_argument("-y", "--yes", action="store_true", help="跳过交互，全部安装")
    parser.add_argument("--no-install", action="store_true", help="仅检测，不安装")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 格式输出")
    parser.add_argument("--generate", "-g", action="store_true", help="生成 Dockerfile 和 devcontainer.json")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示调试/错误信息")

    args = parser.parse_args()
    global _VERBOSE
    _VERBOSE = args.verbose

    # ─── 无参数交互模式（供 启动.bat 调用） ───
    if args.target is None:
        print_colored("\n" + "=" * 62, Color.BLUE)
        print_colored("  🚀  AutoEnv — 万能开源项目环境一键配置", Color.BOLD)
        print_colored("=" * 62, Color.BLUE)
        print()
        print("  请输入开源项目路径或 GitHub URL：")
        print()
        print("     📁  例: C:\\projects\\my-app")
        print("     📁  例: .\\my-project")
        print("     🔗  例: https://github.com/psf/requests")
        print("     🔗  例: git@github.com:user/repo.git")
        print()
        try:
            target = input("  👉 ").strip().strip('"')
        except (EOFError, KeyboardInterrupt):
            print("\n  已退出")
            return
        if not target:
            target = "."
        args.target = target

    # 解析目标（可能触发下载）
    project_dir = resolve_target(args.target)
    if project_dir is None:
        sys.exit(1)

    os_info = get_os_info()
    results = detect_project(project_dir)

    if args.json:
        output_json(results, project_dir, os_info)
        return

    if args.generate:
        print_colored("📄 Dockerfile:", Color.BOLD)
        print(generate_dockerfile(results, project_dir))
        print_colored("\n📄 devcontainer.json:", Color.BOLD)
        print(generate_devcontainer(results, project_dir))
        return

    # 打印检测报告
    all_deps = print_detection_report(results, os_info, project_dir)

    # 决定安装模式
    if args.no_install:
        print_colored("\n💡 提示: 去掉 --no-install 可进入交互安装模式", Color.CYAN)
        return

    if args.yes:
        selected = [d for d in all_deps if not d.is_installed]
        if not selected:
            print_colored("\n🎉 所有依赖已安装！", Color.GREEN)
            return
        print_colored(f"\n⚡ 自动安装模式，共 {len(selected)} 个依赖", Color.YELLOW)
    else:
        selected = interactive_select(all_deps)
        if not selected:
            return

    installer = Installer(auto_install=True, dry_run=False)
    installer.install_all(selected)
    installer.summary()

    print_colored("\n✅ 全部完成！" , Color.GREEN)
    # 暂停等待，方便看结果
    try:
        input("\n按回车键退出...")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
