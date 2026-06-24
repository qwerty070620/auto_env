# auto_env
万能开源项目环境自动检测与安装器 — 丢任意项目进去，自动下载、识别 22 种语言/平台的依赖，交互式一键安装。纯标准库，零外部依赖。
# 🚀 AutoEnv — Universal Open-Source Project Environment Auto-Detector & Installer

<p align="center">
  <b>Drop any open-source project — local path or GitHub URL.</b><br>
  <b>Auto-download → Detect all dependencies → Interactive one-click setup.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/dependencies-0%20(zero)--brightgreen" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/detectors-22-orange" alt="22 Detectors">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Cross Platform">
</p>

---

## ✨ Features

- 🔍 **22 language/platform detectors** — Python, Node.js, Rust, Go, Java, Ruby, PHP, .NET, C/C++, Docker, Terraform, Shell, R, Perl, Haskell, Elixir, Dart/Flutter, Julia, Swift, Deno, Kotlin/Scala, and more
- 📥 **Auto-download** from GitHub — just paste a URL, it `git clone`s or downloads the ZIP
- 📦 **Full dependency extraction** — runtime, build tools, packages, system tools, and services (Docker Compose, databases)
- 🔧 **Interactive selection** — choose exactly which dependencies to install (`all`, `1,3,5-8`, `packages`, or custom range)
- 🛡️ **Security-hardened** — command injection prevention, ZIP path traversal protection, SSRF blocking, resource limits
- 🌍 **Cross-platform** — Windows, macOS, Linux with automatic encoding and shell detection
- 🎨 **Terminal-adaptive** — Emoji with ASCII fallback for older terminals
- 📄 **Generates Dockerfile & Dev Container config** on the fly
- 📊 **JSON output** for CI/CD integration
- 🪶 **Zero external dependencies** — pure Python standard library

---

## ⚡ Quick Start

```bash
# Clone this repo
git clone https://github.com/<your-username>/auto_env.git
cd auto_env

# Run on any project
python -m auto_env /path/to/any/project          # Interactive mode
python -m auto_env https://github.com/psf/requests  # Auto-download from GitHub
python -m auto_env                                # Prompt for URL/path

# All-in-one (skip prompts)
python -m auto_env ./my-project -y

# Report only, no install
python -m auto_env ./my-project --no-install

# JSON output for CI/CD
python -m auto_env ./my-project --json

# Generate Dockerfile + Dev Container
python -m auto_env ./my-project --generate
```

**Windows users:** Double-click `启动.bat` for a menu-driven experience.

---

## 📦 What It Detects

| Type | Stack / Tools | Config Files |
|---|---|---|
| 🐍 Python | pip / poetry / pipenv / conda | `requirements.txt`, `pyproject.toml`, `Pipfile` |
| 🟢 Node.js | npm / yarn / pnpm / bun | `package.json`, `yarn.lock`, `pnpm-lock.yaml` |
| 🦀 Rust | Cargo | `Cargo.toml` |
| 🔵 Go | Go Modules | `go.mod` |
| ☕ Java | Maven / Gradle | `pom.xml`, `build.gradle` |
| 🎭 Kotlin/Scala | Gradle KTS / SBT | `build.gradle.kts`, `build.sbt` |
| 💎 Ruby | Bundler | `Gemfile` |
| 🐘 PHP | Composer | `composer.json` |
| 🟣 .NET | NuGet | `*.csproj`, `*.sln` |
| ⚙️ C/C++ | CMake / Make / Meson | `CMakeLists.txt`, `Makefile` |
| 🐳 Docker | Docker + Compose | `Dockerfile`, `docker-compose.yml` |
| 🏗️ IaC | Terraform / Ansible / Helm / K8s / Pulumi / CDK | `*.tf`, `Chart.yaml`, `playbook.yml` |
| 💻 Shell | Bash script projects | `*.sh`, `configure` |
| 📊 R | R packages | `DESCRIPTION`, `renv.lock` |
| 🐪 Perl | CPAN | `cpanfile`, `Makefile.PL` |
| λ Haskell | Stack / Cabal | `*.cabal`, `stack.yaml` |
| 💧 Elixir | Mix | `mix.exs` |
| 🎯 Dart/Flutter | Pub | `pubspec.yaml` |
| 🔬 Julia | Pkg | `Project.toml` |
| 🦅 Swift | SPM / CocoaPods | `Package.swift`, `Podfile` |
| 🦕 Deno | Deno | `deno.json`, `import_map.json` |

Also scans `README` and docs for system-level dependencies: Docker, PostgreSQL, Redis, ffmpeg, Git, nginx, MySQL, SQLite, OpenSSL, etc.

---

## 🎮 Interactive Selection

After scanning, you choose what to install:

```
  📋 7 dependencies are missing:

    1. 🔧 [runtime] python
    2. 🛠️  [build_tool] pip
    3. 📦 [package] flask (3.0.0)
    4. 📦 [package] requests (2.31.0)
    5. 📦 [package] numpy (1.26.0)
    6. 📦 [package] pandas
    7. 💻 [system] docker

  💡 Enter numbers to install (comma/space/range separated):
      1,3,5-8  |  all  |  packages  |  Enter to skip

  👉 Your choice:
```

| Input | Result |
|---|---|
| `all` or `y` | Install everything |
| `1,3,5` | Install items 1, 3, 5 |
| `2-6` | Install items 2 through 6 |
| `1-3,7` | Mixed range |
| `packages` | Only package dependencies |
| `Enter` or `n` | Skip installation |

---

## 🏗️ Architecture

```
auto_env/
├── auto_env.py                    # Main CLI (detect → interact → install)
├── utils.py                       # Cross-platform shell, encoding, sanitization
├── system_deps.py                 # Document-level system dependency scanner
├── installer.py                   # Dependency installer (safe/fallback modes)
├── 启动.bat                        # Windows one-click launcher (Chinese)
├── README.md
└── detectors/                     # 22 pluggable detectors
    ├── base.py                    #    Template method pattern base class
    ├── python_detector.py         #    🐍 Python
    ├── nodejs_detector.py         #    🟢 Node.js
    ├── rust_detector.py           #    🦀 Rust
    ├── go_detector.py             #    🔵 Go
    ├── java_detector.py           #    ☕ Java
    ├── kotlin_detector.py         #    🎭 Kotlin/Scala
    ├── ruby_detector.py           #    💎 Ruby
    ├── php_detector.py            #    🐘 PHP
    ├── dotnet_detector.py         #    🟣 .NET
    ├── cpp_detector.py            #    ⚙️ C/C++
    ├── docker_detector.py         #    🐳 Docker
    ├── infra_detector.py          #    🏗️ Terraform/K8s/Ansible
    ├── shell_detector.py          #    💻 Shell
    ├── r_detector.py              #    📊 R
    ├── perl_detector.py           #    🐪 Perl
    ├── haskell_detector.py        #    λ Haskell
    ├── elixir_detector.py         #    💧 Elixir
    ├── dart_detector.py           #    🎯 Dart/Flutter
    ├── julia_detector.py          #    🔬 Julia
    ├── swift_detector.py          #    🦅 Swift
    └── deno_detector.py           #    🦕 Deno
```

---

## 🔒 Security

**3-layer command execution defense:**

1. **git clone** → `run_cmd_safe(["git", "clone", ...])` with `shell=False`
2. **URL validation** → rejects shell metacharacters, blocks internal/private IPs (SSRF), enforces HTTPS
3. **Install commands** → safe mode first (`shell=False` + list args), sanitized fallback

**Additional hardening:**
- ZIP path traversal protection (`os.path.realpath` + boundary check, symlinks skipped)
- Download size limit (500 MB) and unzip size limit (1 GB) — Zip bomb defense
- Dependency name whitelist regex: `@scope/name`, `group:artifact`, `package[extra]`

---

## 📋 Requirements

- **Python 3.9+** (any OS — Windows, macOS, Linux)
- **Zero external dependencies** — pure standard library
- Git is recommended for GitHub downloads (falls back to ZIP download otherwise)

---

## 🎯 Use Cases

**Clone-and-run any GitHub project in one command:**
```bash
python -m auto_env https://github.com/AUTOMATIC1111/stable-diffusion-webui -y
```

**Detect a full-stack project with multiple languages:**
```bash
python -m auto_env ./my-fullstack-app
# → Detects Python + Node.js + Docker + Shell simultaneously
# → Lists all runtimes, packages, and Compose services
# → Pick what to install
```

**Generate ready-to-use Dev Container config:**
```bash
python -m auto_env ./project --generate
# → Outputs Dockerfile + .devcontainer/devcontainer.json
# → Open in VS Code and run immediately
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

AutoEnv was designed, audited, and hardened through multiple rounds of security review. Special thanks to the code review process that helped close command injection, path traversal, resource exhaustion, and dozens of other issues before release.

---

<p align="center">
  <sub>Built with ❤️ in pure Python. No pip install required.</sub>
</p>
