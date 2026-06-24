"""Shell 脚本项目检测器"""

import os
import platform
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class ShellDetector(BaseDetector):
    NAME = "shell"
    CONFIG_FILES = ["install.sh", "setup.sh", "bootstrap.sh",
                    "configure", "autogen.sh", "Makefile.am", "*.ebuild"]

    @classmethod
    def detect(cls, project_dir: str):
        result = super().detect(project_dir)

        # 额外检测：大量 .sh 文件的情况
        sh_count = len(list(Path(project_dir).glob("*.sh")))
        if sh_count >= 3:
            if result is None:
                from .base import DetectionResult
                result = DetectionResult(
                    project_type=cls.NAME,
                    project_name=os.path.basename(os.path.abspath(project_dir)),
                    config_files=[f"*.sh ({sh_count}个)"],
                )
            else:
                result.config_files.append(f"*.sh ({sh_count}个)")

        if result is None:
            return None

        if not result.deps:
            try:
                result.deps = cls._parse_deps(project_dir, result.config_files)
            except Exception as e:
                result.notes.append(f"Shell 依赖解析出错: {e}")
        return result

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        tools_found = set()
        common_tools = {
            "curl", "wget", "gcc", "make", "cmake", "autoconf", "automake",
            "git", "tar", "unzip", "gzip", "bzip2", "xz",
            "sed", "awk", "grep", "diff", "patch",
            "python", "python3", "perl", "ruby", "node", "npm",
            "pkg-config", "pkgconfig", "ldconfig",
            "systemctl", "service", "chkconfig",
            "javac", "java", "mvn", "gradle",
            "cargo", "rustc", "go", "dotnet",
            "docker", "podman", "kubectl", "helm",
            "nginx", "apache2", "httpd", "mysql", "psql", "redis-cli",
            "ffmpeg", "imagemagick", "convert", "rsvg-convert",
            "openssl", "ssh-keygen", "gpg",
            "jq", "yq", "xmlstarlet",
        }

        sh_files = list(Path(project_dir).glob("*.sh")) + list(Path(project_dir).glob("configure"))
        for sh_file in sh_files:
            try:
                content = sh_file.read_text(encoding="utf-8", errors="ignore")
                for tool in common_tools:
                    if tool in content and tool not in tools_found:
                        tools_found.add(tool)
            except Exception:
                pass

        show_limit = 20
        shown = sorted(tools_found)[:show_limit]
        if len(tools_found) > show_limit:
            from ..utils import print_colored, Color
            print_colored(f"  ⚠️  检测到 {len(tools_found)} 个 Shell 工具引用，仅显示前 {show_limit}", Color.YELLOW)

        for tool in shown:
            deps.append(DepInfo(
                name=tool, dep_type=DepType.SYSTEM,
                install_command=f"请确保 {tool} 已安装",
                check_command=f"{tool} --version",
            ))
        return deps
