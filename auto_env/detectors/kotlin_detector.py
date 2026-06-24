"""Kotlin / Scala / SBT 项目检测器"""

import os
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class KotlinDetector(BaseDetector):
    NAME = "kotlin_scala"
    CONFIG_FILES = ["build.gradle.kts", "build.gradle", "settings.gradle.kts",
                    "build.sbt", "project/build.properties"]

    @classmethod
    def detect(cls, project_dir: str):
        result = super().detect(project_dir)
        if result is None:
            return None

        # M4: 区分 JavaDetector — 仅当有 kts/sbt 时触发; 纯 build.gradle 交给 JavaDetector
        has_java = os.path.isfile(os.path.join(project_dir, "pom.xml"))
        has_kts_or_sbt = any("kts" in f or "sbt" in f for f in result.config_files)
        has_only_gradle = all("kts" not in f and "sbt" not in f for f in result.config_files)

        if has_java and has_only_gradle:
            return None  # 纯 Gradle 交给 JavaDetector
        if has_only_gradle and not has_kts_or_sbt:
            return None  # 无 kts 无 sbt，不是 Kotlin/Scala 项目

        result.framework = cls._detect_framework(project_dir, result.config_files)
        return result

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        deps.append(DepInfo(
            name="java", dep_type=DepType.RUNTIME,
            install_command="请从 https://adoptium.net 下载 JDK",
            check_command="java --version",
        ))

        has_sbt = any("sbt" in f for f in matched_files)
        has_kts = any("kts" in f for f in matched_files)

        if has_kts:
            deps.append(DepInfo(
                name="kotlin", dep_type=DepType.RUNTIME,
                install_command="Gradle 项目通过 gradle 自动管理 Kotlin",
                check_command="kotlin -version",
            ))
        if has_sbt:
            deps.append(DepInfo(
                name="scala", dep_type=DepType.RUNTIME,
                install_command="请从 https://scala-lang.org 安装 Scala",
                check_command="scala -version",
            ))
            deps.append(DepInfo(
                name="sbt", dep_type=DepType.BUILD_TOOL,
                install_command="请从 https://scala-sbt.org 安装 sbt",
                check_command="sbt --version",
            ))

        # 解析 build.sbt
        build_sbt = os.path.join(project_dir, "build.sbt")
        if os.path.isfile(build_sbt):
            import re
            content = Path(build_sbt).read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r'"([^"]+)"\s*%+\s*"([^"]+)"\s*%+\s*"([^"]*)"', content):
                group, artifact, version = m.group(1), m.group(2), m.group(3)
                deps.append(DepInfo(
                    name=f"{group}:{artifact}", dep_type=DepType.PACKAGE,
                    version=version if version else None,
                    install_command="sbt update",
                ))
        return deps
