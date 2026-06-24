"""Swift / Objective-C 项目检测器"""

import os
import platform
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class SwiftDetector(BaseDetector):
    NAME = "swift"
    CONFIG_FILES = ["Package.swift", "Package.resolved",
                    "*.xcodeproj", "*.xcworkspace", "Podfile", "Podfile.lock",
                    "Cartfile", "Cartfile.resolved"]

    @classmethod
    def detect(cls, project_dir: str):
        return super().detect(project_dir)

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []
        grep = "findstr" if platform.system() == "Windows" else "grep"
        deps.append(DepInfo(
            name="swift", dep_type=DepType.RUNTIME,
            install_command="请从 https://swift.org/download 安装 Swift (macOS 自带 Xcode)",
            check_command="swift --version",
        ))

        # Package.swift (Swift Package Manager)
        pkg_swift = os.path.join(project_dir, "Package.swift")
        if os.path.isfile(pkg_swift):
            import re
            content = Path(pkg_swift).read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r'\.package\s*\(\s*(?:name:\s*)"([^"]+)"', content):
                name = m.group(1)
                deps.append(DepInfo(
                    name=name, dep_type=DepType.PACKAGE,
                    install_command=f"swift package resolve",
                    check_command=f"swift package show-dependencies | {grep} {name}",
                ))
            # 也匹配 url 风格的
            for m in re.finditer(r'\.package\s*\(\s*url:\s*"[^"]*/([^/"]+)"', content):
                deps.append(DepInfo(
                    name=m.group(1).replace(".git", ""),
                    dep_type=DepType.PACKAGE,
                    install_command="swift package resolve",
                ))

        # Podfile (CocoaPods)
        podfile = os.path.join(project_dir, "Podfile")
        if os.path.isfile(podfile):
            deps.append(DepInfo(
                name="cocoapods", dep_type=DepType.BUILD_TOOL,
                install_command="gem install cocoapods",
                check_command="pod --version",
            ))
        return deps
