"""Python 项目检测器"""

import os
import re
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType

# 常见大目录（本地定义，避免跨包相对导入）
_SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", ".tox",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "target", "build",
    "dist", ".gradle", ".idea", ".vscode", "vendor", "bower_components",
    ".next", ".nuxt", ".output", ".svelte-kit",
}


class PythonDetector(BaseDetector):
    NAME = "python"
    CONFIG_FILES = [
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "Pipfile",
        "Pipfile.lock",
        "poetry.lock",
        "environment.yml",
        "environment.yaml",
    ]

    @classmethod
    def _parse_project_name(cls, project_dir: str, matched_files: list[str]) -> str:
        pyproject = os.path.join(project_dir, "pyproject.toml")
        if os.path.isfile(pyproject):
            content = Path(pyproject).read_text(encoding="utf-8")
            m = re.search(r'name\s*=\s*"([^"]+)"', content)
            if m:
                return m.group(1)
        setup_cfg = os.path.join(project_dir, "setup.cfg")
        if os.path.isfile(setup_cfg):
            content = Path(setup_cfg).read_text(encoding="utf-8")
            m = re.search(r'name\s*=\s*(\S+)', content)
            if m:
                return m.group(1).strip()
        return super()._parse_project_name(project_dir, matched_files)

    @classmethod
    def _detect_framework(cls, project_dir: str, matched_files: list[str]) -> str | None:
        # 高效检查常见框架特征文件（跳过大目录，限制深度）
        file_names = set()
        for root, dirs, files in os.walk(project_dir, topdown=True):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
            depth = root.replace(project_dir, "").count(os.sep)
            if depth > 3:
                dirs[:] = []
                continue
            for f in files:
                file_names.add(f)

        frameworks = {
            "Django": ["manage.py", "wsgi.py"],
            "Flask": ["app.py"],
            "FastAPI": [],
            "Streamlit": [],
            "Pyramid": [],
            "Tornado": [],
            "Scrapy": ["scrapy.cfg"],
        }

        # 也检查依赖中是否包含框架
        all_text = ""
        for fname in matched_files:
            fpath = os.path.join(project_dir, fname)
            try:
                all_text += Path(fpath).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass

        for fw, indicators in frameworks.items():
            if any(ind in file_names for ind in indicators):
                return fw
            if fw.lower() in all_text.lower():
                return fw

        return None

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []

        # Python 运行时本身
        deps.append(DepInfo(
            name="python",
            dep_type=DepType.RUNTIME,
            version=None,
            install_command="请从 https://python.org 下载安装 Python",
            check_command="python --version",
        ))

        # pip
        deps.append(DepInfo(
            name="pip",
            dep_type=DepType.BUILD_TOOL,
            install_command="python -m ensurepip --upgrade",
            check_command="pip --version",
        ))

        # 解析 requirements.txt
        req_path = os.path.join(project_dir, "requirements.txt")
        if os.path.isfile(req_path):
            for line in Path(req_path).read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                if ";" in line:
                    line = line.split(";")[0].strip()
                pkg_name = re.split(r'[<>=!~\[\s]', line)[0].strip()
                # 安全化：只保留安全字符
                safe_name = re.sub(r'[^a-zA-Z0-9_\-\.@/]', '', pkg_name)[:80]
                version = None
                m = re.search(r'[<>=!~]+\s*([\d.]+)', line)
                if m:
                    version = m.group(1)
                if safe_name:
                    deps.append(DepInfo(
                        name=safe_name,
                        dep_type=DepType.PACKAGE,
                        version=version,
                        install_command=f"pip install {safe_name}",
                        check_command=f"pip show {safe_name}",
                    ))

        # 解析 pyproject.toml (Poetry / PEP 621) — 无论是否有 requirements.txt 都解析
        pyproject = os.path.join(project_dir, "pyproject.toml")
        if os.path.isfile(pyproject):
            content = Path(pyproject).read_text(encoding="utf-8", errors="ignore")
            if "poetry" in content.lower():
                deps.append(DepInfo(
                    name="poetry",
                    dep_type=DepType.BUILD_TOOL,
                    install_command="pip install poetry",
                    check_command="poetry --version",
                ))
            # 解析 [tool.poetry.dependencies] 或 [project] dependencies
            in_deps = False
            for line in content.splitlines():
                line = line.strip()
                if re.match(r'\[tool\.poetry\.dependencies\]', line):
                    in_deps = True
                    continue
                elif line.startswith("[") and in_deps:
                    in_deps = False
                if in_deps and "=" in line and not line.startswith("#"):
                    pkg_name = line.split("=")[0].strip()
                    deps.append(DepInfo(
                        name=pkg_name,
                        dep_type=DepType.PACKAGE,
                        install_command=f"poetry add {pkg_name}",
                        check_command=f"pip show {pkg_name}",
                    ))

        # 解析 Pipfile
        pipfile = os.path.join(project_dir, "Pipfile")
        if os.path.isfile(pipfile):
            deps.append(DepInfo(
                name="pipenv",
                dep_type=DepType.BUILD_TOOL,
                install_command="pip install pipenv",
                check_command="pipenv --version",
            ))

        # Conda 环境
        env_yml = os.path.join(project_dir, "environment.yml")
        if os.path.isfile(env_yml):
            deps.append(DepInfo(
                name="conda",
                dep_type=DepType.BUILD_TOOL,
                install_command="请安装 Miniconda: https://docs.conda.io/en/latest/miniconda.html",
                check_command="conda --version",
            ))

        return deps
