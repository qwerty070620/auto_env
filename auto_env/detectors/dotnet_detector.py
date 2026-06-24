""".NET / C# 项目检测器"""

import os
import platform
import re
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class DotnetDetector(BaseDetector):
    NAME = "dotnet"
    CONFIG_FILES = [
        "*.csproj",
        "*.fsproj",
        "*.vbproj",
        "*.sln",
        "global.json",
        "NuGet.config",
    ]

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        grep = "findstr" if platform.system() == "Windows" else "grep"

        deps.append(DepInfo(
            name="dotnet",
            dep_type=DepType.RUNTIME,
            install_command="请从 https://dotnet.microsoft.com/download 下载安装 .NET SDK",
            check_command="dotnet --version",
        ))

        # 搜索所有 csproj/fsproj 文件（跳过常见大目录）
        skip = {"node_modules", ".git", "bin", "obj", ".vs", ".idea"}
        for proj in Path(project_dir).rglob("*.csproj"):
            if any(p in skip for p in proj.parts):
                continue
            content = proj.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r'<PackageReference\s+Include="([^"]+)"\s+Version="([^"]*)"', content):
                name = m.group(1)
                version = m.group(2)
                deps.append(DepInfo(
                    name=name,
                    dep_type=DepType.PACKAGE,
                    version=version,
                    install_command=f"dotnet add package {name}",
                    check_command=f"dotnet list package | {grep} {name}",
                ))

        return deps
