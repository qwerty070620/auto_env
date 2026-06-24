"""自动安装器 - 根据检测结果尝试安装依赖"""

from __future__ import annotations
import subprocess
import platform
from .detectors.base import DepInfo, DepType
from .utils import run_cmd, run_cmd_safe, Color, print_colored, check_tool_installed, sanitize_for_cmd


class Installer:
    """依赖安装器"""

    INSTALL_TIMEOUT = 180  # 安装超时（秒）

    def __init__(self, auto_install: bool = False, dry_run: bool = False):
        self.auto_install = auto_install
        self.dry_run = dry_run
        self.installed: list[str] = []
        self.failed: list[str] = []
        self.skipped: list[str] = []

    def install(self, dep: DepInfo) -> bool:
        """尝试安装单个依赖"""
        # 先检查是否已安装
        if dep.check_command:
            if check_tool_installed(dep.name, dep.check_command):
                print_colored(f"  ✅ {dep.name} - 已安装", Color.GREEN)
                self.skipped.append(dep.name)
                return True

        if not dep.install_command:
            print_colored(f"  ⚠️  {dep.name} - 无安装命令，请手动安装", Color.YELLOW)
            self.skipped.append(dep.name)
            return False

        print_colored(f"  📦 {dep.name} - 准备安装...", Color.CYAN)

        if self.dry_run:
            print_colored(f"     [DRY-RUN] 将执行: {dep.install_command}", Color.YELLOW)
            self.skipped.append(dep.name)
            return True

        if self.auto_install:
            # 检查 install_command 是否为自然语言提示 (M2)
            if dep.install_command and any(c in dep.install_command for c in "请从下载"):
                print_colored(f"     📝 {dep.name} - 需手动安装: {dep.install_command[:100]}", Color.YELLOW)
                self.skipped.append(dep.name)
                return False

            # 优先安全模式（shell=False），回退到 shell=True
            try:
                import shlex
                parts = shlex.split(dep.install_command)
                parts = [sanitize_for_cmd(p) for p in parts]
                success, output = run_cmd_safe(parts, timeout=self.INSTALL_TIMEOUT)
            except Exception:
                safe_cmd = sanitize_for_cmd(dep.install_command, max_len=500)
                if not safe_cmd or safe_cmd == "unknown":
                    print_colored(f"     ⚠️  {dep.name} - 无法解析安装命令", Color.YELLOW)
                    self.skipped.append(dep.name)
                    return False
                success, output = run_cmd(safe_cmd, timeout=self.INSTALL_TIMEOUT)
            if success:
                print_colored(f"     ✅ 安装成功", Color.GREEN)
                self.installed.append(dep.name)
                return True
            else:
                print_colored(f"     ❌ 安装失败: {output[:200]}", Color.RED)
                self.failed.append(dep.name)
                return False
        else:
            print_colored(f"     💡 手动执行: {dep.install_command}", Color.YELLOW)
            self.skipped.append(dep.name)
            return False

    def install_all(self, deps: list[DepInfo]):
        """批量安装依赖"""
        if not deps:
            print_colored("  无依赖需要安装", Color.GREEN)
            return

        # 按类型排序：先装运行时，再装构建工具，最后包依赖
        priority = {
            DepType.RUNTIME: 0,
            DepType.BUILD_TOOL: 1,
            DepType.SYSTEM: 2,
            DepType.PACKAGE: 3,
            DepType.SERVICE: 4,
        }
        sorted_deps = sorted(deps, key=lambda d: priority.get(d.dep_type, 5))

        print_colored(f"\n📋 共 {len(sorted_deps)} 个依赖", Color.BOLD)

        for dep in sorted_deps:
            type_emoji = {
                DepType.RUNTIME: "🔧",
                DepType.BUILD_TOOL: "🛠️",
                DepType.SYSTEM: "💻",
                DepType.PACKAGE: "📦",
                DepType.SERVICE: "☁️",
            }
            emoji = type_emoji.get(dep.dep_type, "❓")
            ver_info = f" ({dep.version})" if dep.version else ""

            print(f"  {emoji} [{dep.dep_type.value}] {dep.name}{ver_info}")
            self.install(dep)

    def summary(self):
        """打印安装汇总"""
        print_colored("\n" + "=" * 50, Color.BLUE)
        print_colored(" 安装汇总", Color.BOLD)
        print_colored("=" * 50, Color.BLUE)
        print(f"  ✅ 已安装/跳过: {len(self.skipped)}")
        print(f"  🆕 新安装: {len(self.installed)}")
        print(f"  ❌ 失败: {len(self.failed)}")
        if self.failed:
            print_colored(f"  失败项: {', '.join(self.failed)}", Color.RED)
