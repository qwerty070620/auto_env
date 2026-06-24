"""系统级依赖检测 - 检测 README 文档中提到的系统依赖"""

import os
import re
from pathlib import Path
from .detectors.base import DepInfo, DepType
from .utils import check_tool_installed


# 常见系统级依赖关键词及对应的检查命令
SYSTEM_DEP_PATTERNS = {
    "docker": {
        "keywords": ["docker"],
        "check_cmd": "docker --version",
        "install_cmd": "请从 https://docker.com 下载安装 Docker Desktop",
    },
    "git": {
        "keywords": ["git"],
        "check_cmd": "git --version",
        "install_cmd": "请从 https://git-scm.com 下载安装 Git",
    },
    "postgresql": {
        "keywords": ["postgresql", "postgres", "psql", "pg_"],
        "check_cmd": "psql --version",
        "install_cmd": "请从 https://postgresql.org 下载安装 PostgreSQL",
    },
    "mysql": {
        "keywords": ["mysql", "mariadb"],
        "check_cmd": "mysql --version",
        "install_cmd": "请从 https://mysql.com 下载安装 MySQL/MariaDB",
    },
    "redis": {
        "keywords": ["redis"],
        "check_cmd": "redis-cli --version",
        "install_cmd": "请从 https://redis.io 下载安装 Redis，或用 docker run redis",
    },
    "sqlite": {
        "keywords": ["sqlite"],
        "check_cmd": "sqlite3 --version",
        "install_cmd": "请从 https://sqlite.org 下载，或系统通常自带",
    },
    "mongodb": {
        "keywords": ["mongodb", "mongo"],
        "check_cmd": "mongod --version",
        "install_cmd": "请从 https://mongodb.com 下载安装 MongoDB",
    },
    "openssl": {
        "keywords": ["openssl", "libssl"],
        "check_cmd": "openssl version",
        "install_cmd": "Linux: sudo apt install openssl; macOS: brew install openssl; Windows: choco install openssl",
    },
    "ffmpeg": {
        "keywords": ["ffmpeg"],
        "check_cmd": "ffmpeg -version",
        "install_cmd": "请从 https://ffmpeg.org 下载安装 ffmpeg，或 choco install ffmpeg",
    },
    "imagemagick": {
        "keywords": ["imagemagick", "magick", "convert "],
        "check_cmd": "magick --version",
        "install_cmd": "choco install imagemagick / brew install imagemagick",
    },
    "nginx": {
        "keywords": ["nginx"],
        "check_cmd": "nginx -v",
        "install_cmd": "请从 https://nginx.org 下载安装 nginx",
    },
    "curl": {
        "keywords": ["curl"],
        "check_cmd": "curl --version",
        "install_cmd": "系统通常自带",
    },
    "wget": {
        "keywords": ["wget"],
        "check_cmd": "wget --version",
        "install_cmd": "choco install wget / brew install wget",
    },
    "make": {
        "keywords": ["make ", "makefile", "gnumakefile"],
        "check_cmd": "make --version",
        "install_cmd": "Linux: sudo apt install build-essential; Windows: choco install make; macOS: xcode-select --install",
    },
    "gcc": {
        "keywords": ["gcc", "g\\+\\+", "gnu compiler"],
        "check_cmd": "gcc --version",
        "install_cmd": "Linux: sudo apt install build-essential; Windows: 安装 MinGW-w64; macOS: xcode-select --install",
    },
    "pkg-config": {
        "keywords": ["pkg-config", "pkgconfig"],
        "check_cmd": "pkg-config --version",
        "install_cmd": "choco install pkgconfiglite / brew install pkg-config",
    },
}


def detect_system_deps(project_dir: str) -> list[DepInfo]:
    """扫描项目文档（README、文档）检测系统级依赖"""
    deps: list[DepInfo] = []
    doc_extensions = {".md", ".txt", ".rst", ".adoc", ".org"}
    doc_content = ""

    project_path = Path(project_dir)
    # 限制遍历深度，跳过常见大目录
    skip_dirs = {"node_modules", ".git", "__pycache__", ".venv", "venv",
                 "target", "build", "dist", "vendor", ".idea", ".vscode"}
    max_depth = 4
    for fpath in project_path.rglob("*"):
        # 深度检查
        if len(fpath.relative_to(project_path).parts) > max_depth:
            continue
        # 跳过目录
        if any(p in skip_dirs for p in fpath.parts):
            continue
        if fpath.suffix.lower() in doc_extensions and fpath.is_file():
            if fpath.stat().st_size > 1024 * 500:
                continue
            try:
                doc_content += fpath.read_text(encoding="utf-8", errors="ignore") + "\n"
            except Exception:
                pass

    if not doc_content:
        return deps

    doc_lower = doc_content.lower()

    for dep_key, info in SYSTEM_DEP_PATTERNS.items():
        found = False
        for kw in info["keywords"]:
            # C2 修复：strip + 使用字面子串搜索替代 \b 边界正则
            keyword = kw.strip()
            if keyword in doc_lower:
                found = True
                break

        if found:
            is_installed = check_tool_installed(dep_key, info["check_cmd"])
            deps.append(DepInfo(
                name=dep_key,
                dep_type=DepType.SYSTEM,
                install_command=info["install_cmd"],
                check_command=info["check_cmd"],
                is_installed=is_installed,
            ))

    return deps
