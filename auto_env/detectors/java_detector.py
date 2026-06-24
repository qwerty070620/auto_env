"""Java 项目检测器 (Maven / Gradle)"""

import os
import platform
import re
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class JavaDetector(BaseDetector):
    NAME = "java"
    CONFIG_FILES = [
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
        "gradlew",
        "gradlew.bat",
        "mvnw",
        "mvnw.cmd",
    ]

    @classmethod
    def _parse_project_name(cls, project_dir: str, matched_files: list[str]) -> str:
        pom = os.path.join(project_dir, "pom.xml")
        if os.path.isfile(pom):
            content = Path(pom).read_text(encoding="utf-8", errors="ignore")
            m = re.search(r'<artifactId>([^<]+)</artifactId>', content)
            if m:
                return m.group(1)
        settings = os.path.join(project_dir, "settings.gradle")
        if os.path.isfile(settings):
            content = Path(settings).read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"rootProject\.name\s*=\s*['\"]([^'\"]+)", content)
            if m:
                return m.group(1)
        return super()._parse_project_name(project_dir, matched_files)

    @classmethod
    def _detect_framework(cls, project_dir: str, matched_files: list[str]) -> str | None:
        all_text = ""
        for fname in ["pom.xml", "build.gradle", "build.gradle.kts"]:
            fpath = os.path.join(project_dir, fname)
            if os.path.isfile(fpath):
                all_text += Path(fpath).read_text(encoding="utf-8", errors="ignore")

        frameworks = {
            "spring-boot-starter": "Spring Boot",
            "springframework": "Spring",
            "quarkus": "Quarkus",
            "micronaut": "Micronaut",
            "jakarta": "Jakarta EE",
            "javalin": "Javalin",
            "helidon": "Helidon",
        }
        for keyword, fw_name in frameworks.items():
            if keyword in all_text.lower():
                return fw_name

        return None

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []

        deps.append(DepInfo(
            name="java",
            dep_type=DepType.RUNTIME,
            install_command="请从 https://adoptium.net 下载安装 JDK (推荐 17+)",
            check_command="java --version",
        ))

        has_maven = any(f in matched_files for f in ["pom.xml", "mvnw", "mvnw.cmd"])
        has_gradle = any(f in matched_files for f in ["build.gradle", "build.gradle.kts", "gradlew", "gradlew.bat"])

        if has_maven:
            deps.append(DepInfo(
                name="maven",
                dep_type=DepType.BUILD_TOOL,
                install_command="请从 https://maven.apache.org 下载安装 Maven，或用项目内的 mvnw",
                check_command="mvn --version",
            ))
            cls._parse_maven_deps(project_dir, deps)

        if has_gradle:
            deps.append(DepInfo(
                name="gradle",
                dep_type=DepType.BUILD_TOOL,
                install_command="项目内有 gradlew，无需额外安装",
                check_command="gradle --version",
            ))

        return deps

    @classmethod
    def _parse_maven_deps(cls, project_dir: str, deps: list):
        """解析 pom.xml 中的依赖（使用 xml.etree.ElementTree）"""
        grep = "findstr" if platform.system() == "Windows" else "grep"
        pom = os.path.join(project_dir, "pom.xml")
        if not os.path.isfile(pom):
            return
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(pom)
            root = tree.getroot()
            # Maven namespace
            ns = root.tag.split("}")[0].strip("{") if "}" in root.tag else ""
            ns_map = {"m": ns} if ns else {}

            for dep in root.findall(".//m:dependency", ns_map) if ns else root.findall(".//dependency"):
                group = dep.find("m:groupId" if ns else "groupId", ns_map)
                artifact = dep.find("m:artifactId" if ns else "artifactId", ns_map)
                version_el = dep.find("m:version" if ns else "version", ns_map)
                if group is not None and artifact is not None and group.text and artifact.text:
                    group_id = group.text.strip()
                    artifact_id = artifact.text.strip()
                    version = version_el.text.strip() if version_el is not None and version_el.text else None
                    full_name = f"{group_id}:{artifact_id}"
                    deps.append(DepInfo(
                        name=full_name,
                        dep_type=DepType.PACKAGE,
                        version=version,
                        install_command=f"mvn dependency:get -Dartifact={full_name}" + (f":{version}" if version else ""),
                        check_command=f"mvn dependency:tree | {grep} {artifact_id}",
                    ))
        except Exception:
            # 回退到正则解析（处理格式不规范的 XML）
            content = Path(pom).read_text(encoding="utf-8", errors="ignore")
            pattern = re.compile(
                r'<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>\s*(?:<version>([^<]*)</version>)?',
                re.DOTALL
            )
            for m in pattern.finditer(content):
                group = m.group(1).strip()
                artifact = m.group(2).strip()
                version = m.group(3).strip() if m.group(3) else None
                full_name = f"{group}:{artifact}"
                deps.append(DepInfo(
                    name=full_name,
                    dep_type=DepType.PACKAGE,
                    version=version,
                    install_command=f"mvn dependency:get -Dartifact={full_name}" + (f":{version}" if version else ""),
                    check_command=f"mvn dependency:tree | {grep} {artifact}",
                ))
