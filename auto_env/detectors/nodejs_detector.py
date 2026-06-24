"""Node.js / JavaScript 项目检测器"""

import os
import json
import re
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType

# 安全校验
def _safe(name: str) -> str:
    import re
    return re.sub(r'[^a-zA-Z0-9_\-\.@/]', '', str(name))[:80]


class NodeJSDetector(BaseDetector):
    NAME = "nodejs"
    CONFIG_FILES = [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "bun.lock",
        "bun.lockb",
    ]

    @classmethod
    def _parse_project_name(cls, project_dir: str, matched_files: list[str]) -> str:
        pkg = os.path.join(project_dir, "package.json")
        if os.path.isfile(pkg):
            try:
                data = json.loads(Path(pkg).read_text(encoding="utf-8-sig"))
                return data.get("name", "") or super()._parse_project_name(project_dir, matched_files)
            except Exception:
                pass
        return super()._parse_project_name(project_dir, matched_files)

    @classmethod
    def _detect_framework(cls, project_dir: str, matched_files: list[str]) -> str | None:
        pkg = os.path.join(project_dir, "package.json")
        if not os.path.isfile(pkg):
            return None

        try:
            data = json.loads(Path(pkg).read_text(encoding="utf-8-sig"))
        except Exception:
            return None

        all_deps = {}
        all_deps.update(data.get("dependencies", {}))
        all_deps.update(data.get("devDependencies", {}))
        dep_names = [k.lower() for k in all_deps.keys()]

        framework_map = {
            "next": "Next.js",
            "react": "React",
            "vue": "Vue.js",
            "svelte": "Svelte",
            "angular": "Angular",
            "express": "Express.js",
            "koa": "Koa",
            "fastify": "Fastify",
            "nest": "NestJS",
            "nuxt": "Nuxt.js",
            "astro": "Astro",
            "remix": "Remix",
            "gatsby": "Gatsby",
            "vite": "Vite",
            "webpack": "Webpack",
            "electron": "Electron",
        }

        for dep, framework_name in framework_map.items():
            if dep in dep_names:
                return framework_name

        # 或从 scripts 判断
        scripts = data.get("scripts", {})
        if any("next" in v for v in scripts.values()):
            return "Next.js"
        if any("react-scripts" in v for v in scripts.values()):
            return "React (CRA)"

        return None

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []

        deps.append(DepInfo(
            name="node",
            dep_type=DepType.RUNTIME,
            install_command="请从 https://nodejs.org 下载安装 Node.js",
            check_command="node --version",
        ))

        # 检测包管理器
        has_yarn = "yarn.lock" in matched_files
        has_pnpm = "pnpm-lock.yaml" in matched_files
        has_bun = "bun.lock" in matched_files or "bun.lockb" in matched_files
        has_npm = "package-lock.json" in matched_files

        if has_npm or (not has_yarn and not has_pnpm and not has_bun):
            deps.append(DepInfo(
                name="npm",
                dep_type=DepType.BUILD_TOOL,
                install_command="随 Node.js 自带",
                check_command="npm --version",
            ))
        if has_yarn:
            deps.append(DepInfo(
                name="yarn",
                dep_type=DepType.BUILD_TOOL,
                install_command="npm install -g yarn",
                check_command="yarn --version",
            ))
        if has_pnpm:
            deps.append(DepInfo(
                name="pnpm",
                dep_type=DepType.BUILD_TOOL,
                install_command="npm install -g pnpm",
                check_command="pnpm --version",
            ))
        if has_bun:
            deps.append(DepInfo(
                name="bun",
                dep_type=DepType.BUILD_TOOL,
                install_command="请从 https://bun.sh 下载安装 Bun",
                check_command="bun --version",
            ))

        # 解析 package.json
        pkg = os.path.join(project_dir, "package.json")
        if os.path.isfile(pkg):
            try:
                data = json.loads(Path(pkg).read_text(encoding="utf-8-sig"))
            except Exception:
                return deps

            def add_dep(dep_name: str, dep_version: str, is_dev: bool = False):
                if dep_name in {"node", "npm", "yarn", "pnpm", "bun"}:
                    return
                safe_name = _safe(dep_name)
                deps.append(DepInfo(
                    name=dep_name,
                    dep_type=DepType.PACKAGE,
                    version=str(dep_version).lstrip("^~>=<"),
                    install_command=f"npm install {safe_name}",
                    check_command=f"npm ls {safe_name} --depth=0",
                ))

            for name, ver in data.get("dependencies", {}).items():
                add_dep(name, ver)
            for name, ver in data.get("devDependencies", {}).items():
                add_dep(name, ver, is_dev=True)

        return deps
