"""PHP 项目检测器"""

import os
import json as json_module
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class PHPDetector(BaseDetector):
    NAME = "php"
    CONFIG_FILES = ["composer.json", "composer.lock"]

    @classmethod
    def _parse_project_name(cls, project_dir: str, matched_files: list[str]) -> str:
        composer = os.path.join(project_dir, "composer.json")
        if os.path.isfile(composer):
            try:
                data = json_module.loads(Path(composer).read_text(encoding="utf-8-sig"))
                return data.get("name", "") or super()._parse_project_name(project_dir, matched_files)
            except Exception:
                pass
        return super()._parse_project_name(project_dir, matched_files)

    @classmethod
    def _detect_framework(cls, project_dir: str, matched_files: list[str]) -> str | None:
        composer = os.path.join(project_dir, "composer.json")
        if not os.path.isfile(composer):
            return None
        try:
            data = json_module.loads(Path(composer).read_text(encoding="utf-8-sig"))
        except Exception:
            return None
        all_deps = {}
        all_deps.update(data.get("require", {}))
        all_deps.update(data.get("require-dev", {}))
        dep_names = [k.lower() for k in all_deps.keys()]

        framework_map = {
            "laravel/framework": "Laravel",
            "symfony/framework-bundle": "Symfony",
            "yiisoft/yii2": "Yii",
            "cakephp/cakephp": "CakePHP",
            "codeigniter4/framework": "CodeIgniter",
            "slim/slim": "Slim",
            "laminas/laminas-mvc": "Laminas",
        }
        for dep, fw_name in framework_map.items():
            if dep in dep_names:
                return fw_name
        return None

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []

        deps.append(DepInfo(
            name="php",
            dep_type=DepType.RUNTIME,
            install_command="请从 https://php.net 下载安装 PHP",
            check_command="php --version",
        ))
        deps.append(DepInfo(
            name="composer",
            dep_type=DepType.BUILD_TOOL,
            install_command="请从 https://getcomposer.org 下载安装 Composer",
            check_command="composer --version",
        ))

        composer = os.path.join(project_dir, "composer.json")
        if os.path.isfile(composer):
            try:
                data = json_module.loads(Path(composer).read_text(encoding="utf-8-sig"))
            except Exception:
                return deps

            def add_dep(dep_name: str, dep_version: str):
                deps.append(DepInfo(
                    name=dep_name,
                    dep_type=DepType.PACKAGE,
                    version=dep_version,
                    install_command=f"composer require {dep_name}" + (f":{dep_version}" if dep_version else ""),
                    check_command=f"composer show {dep_name}",
                ))

            for name, ver in data.get("require", {}).items():
                if name != "php":
                    add_dep(name, ver)
            for name, ver in data.get("require-dev", {}).items():
                add_dep(name, ver)

        return deps
