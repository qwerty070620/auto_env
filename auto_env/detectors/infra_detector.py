"""基础设施即代码项目检测器 (Terraform / Ansible / Kubernetes / Helm)"""

import os
from pathlib import Path
from .base import BaseDetector, DepInfo, DepType


class InfraDetector(BaseDetector):
    NAME = "infra"
    CONFIG_FILES = ["*.tf", "*.tfvars", "terraform.tfvars", ".terraform.lock.hcl",
                    "ansible.cfg", "playbook.yml", "playbook.yaml",
                    "Chart.yaml", "values.yaml", "kustomization.yaml",
                    ".helmignore", "Pulumi.yaml", "cdk.json"]
    EXCLUDE_FILES = ["*.yml", "*.yaml"]  # 太宽泛，用名单精确指定

    @classmethod
    def detect(cls, project_dir: str):
        result = super().detect(project_dir)
        if result is None:
            return None

        matched_set = set(result.config_files)
        has_tf = any("tf" in f for f in matched_set)
        has_ansible = any("ansible" in f.lower() for f in matched_set) or \
                      "playbook.yml" in matched_set or "playbook.yaml" in matched_set
        has_helm = "Chart.yaml" in matched_set
        has_pulumi = any("Pulumi" in f for f in matched_set)
        has_cdk = "cdk.json" in matched_set

        if not (has_tf or has_ansible or has_helm or has_pulumi or has_cdk):
            return None

        # 基类已设置 project_name/deps，补充框架检测
        result.framework = cls._detect_framework(project_dir, result.config_files)
        return result

    @classmethod
    def _detect_framework(cls, project_dir: str, matched_files: list[str]) -> str | None:
        matched_set = set(matched_files)
        types = []
        if any("tf" in f for f in matched_set):
            types.append("Terraform")
        if any("ansible" in f.lower() for f in matched_set):
            types.append("Ansible")
        if "Chart.yaml" in matched_set:
            types.append("Helm")
        if any("Pulumi" in f for f in matched_set):
            types.append("Pulumi")
        if "cdk.json" in matched_set:
            types.append("AWS CDK")
        return " + ".join(types) if types else None

    @classmethod
    def _parse_deps(cls, project_dir: str, matched_files: list[str]) -> list[DepInfo]:
        deps: list[DepInfo] = []

        # Terraform
        if any("tf" in f for f in matched_files):
            deps.append(DepInfo(
                name="terraform", dep_type=DepType.BUILD_TOOL,
                install_command="请从 https://terraform.io/downloads 安装 Terraform，或 choco install terraform",
                check_command="terraform --version",
            ))

        # Ansible
        if any("ansible" in f.lower() for f in matched_files) or \
           os.path.isfile(os.path.join(project_dir, "playbook.yml")):
            deps.append(DepInfo(
                name="ansible", dep_type=DepType.BUILD_TOOL,
                install_command="pip install ansible",
                check_command="ansible --version",
            ))

        # Helm
        if "Chart.yaml" in matched_files or ".helmignore" in matched_files:
            deps.append(DepInfo(
                name="helm", dep_type=DepType.BUILD_TOOL,
                install_command="请从 https://helm.sh 安装 Helm，或 choco install kubernetes-helm",
                check_command="helm version",
            ))

        # Kubernetes
        if any(f in matched_files for f in ["kustomization.yaml"]):
            deps.append(DepInfo(
                name="kubectl", dep_type=DepType.BUILD_TOOL,
                install_command="choco install kubernetes-cli",
                check_command="kubectl version --client",
            ))

        # Pulumi
        if any("Pulumi" in f for f in matched_files):
            deps.append(DepInfo(
                name="pulumi", dep_type=DepType.BUILD_TOOL,
                install_command="请从 https://pulumi.com 安装 Pulumi，或 choco install pulumi",
                check_command="pulumi version",
            ))

        # AWS CDK
        if "cdk.json" in matched_files:
            deps.append(DepInfo(
                name="aws-cdk", dep_type=DepType.BUILD_TOOL,
                install_command="npm install -g aws-cdk",
                check_command="cdk --version",
            ))

        return deps
