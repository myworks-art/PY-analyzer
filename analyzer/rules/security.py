#
# Security (SEC001–SEC006).
#
# All rules are registered in @registry.register.
#

from __future__ import annotations

import re

from ruamel.yaml.comments import CommentedMap

from analyzer.parsers.yaml_parser import ParsedPipeline, _get_pos
from analyzer.rules.base import BaseRule, Category, Issue, Severity
from analyzer.rules.registry import registry

#
# SEC001
#

_SECRET_NAME_PATTERNS = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|auth[_-]?key|private[_-]?key|"
    r"access[_-]?key|credentials?|credential)",
    re.IGNORECASE,
)

_SECRET_VALUE_PATTERNS = re.compile(
    r"^(?!\$)(?!\s*$).{8,}$"
)

_BENIGN_VALUES = re.compile(
    r"^(true|false|yes|no|none|null|"
    r"production|staging|development|dev|prod|local|"
    r"https?://|/[a-z]|[0-9]+\.[0-9]+|"
    r"[a-z][-a-z0-9]*\.[a-z]{2,})$",
    re.IGNORECASE,
)


@registry.register
class SecretInVariableRule(BaseRule):

    rule_id = "SEC001"
    severity = Severity.ERROR
    category = Category.SECURITY
    description = "Возможный секрет в переменной окружения"

    def check(self, pipeline: ParsedPipeline) -> list[Issue]:
        issues: list[Issue] = []

        if pipeline.variables:
            issues.extend(self._check_variables_map(pipeline.raw_data, "variables"))

        for job in pipeline.jobs:
            if "variables" in job.data:
                issues.extend(
                    self._check_variables_map(job.data, "variables", job_name=job.name)
                )

        return issues

    def _check_variables_map(
        self,
        parent: CommentedMap,
        key: str,
        job_name: str | None = None,
    ) -> list[Issue]:
        issues: list[Issue] = []
        vars_map = parent.get(key)
        if not isinstance(vars_map, CommentedMap):
            return issues

        for var_name, var_value in vars_map.items():
            var_name_str = str(var_name)
            var_value_str = str(var_value) if var_value is not None else ""

            name_suspicious = bool(_SECRET_NAME_PATTERNS.search(var_name_str))
            value_suspicious = bool(
                var_value_str and _SECRET_VALUE_PATTERNS.match(var_value_str)
            )

            if name_suspicious and value_suspicious:
                if _BENIGN_VALUES.match(var_value_str):
                    continue
                pos = _get_pos(vars_map, var_name)
                issues.append(
                    self._make_issue(
                        message=f"Возможный секрет в переменной '{var_name_str}' — значение задано в открытом виде",
                        line=pos.line if pos else 0,
                        col=pos.col if pos else 0,
                        job_name=job_name,
                        fix_suggestion=(
                            f"Перенесите '{var_name_str}' в Settings → CI/CD → Variables "
                            "с флагами Masked и Protected. В YAML используйте: "
                            f"{var_name_str}: ${var_name_str}"
                        ),
                    )
                )
        return issues


#
# SEC002
#

@registry.register
class LatestImageTagRule(BaseRule):

    rule_id = "SEC002"
    severity = Severity.WARNING
    category = Category.SECURITY
    description = "Образ использует тег 'latest' — нарушает детерминированность сборок"

    def check(self, pipeline: ParsedPipeline) -> list[Issue]:
        issues: list[Issue] = []

        if pipeline.image and self._is_latest(pipeline.image):
            pos = pipeline.image_pos
            issues.append(
                self._make_issue(
                    message=f"Глобальный образ '{pipeline.image}' использует тег 'latest'",
                    line=pos.line if pos else 0,
                    col=pos.col if pos else 0,
                    fix_suggestion="Укажите конкретную версию, например: python:3.12-slim",
                )
            )

        for job in pipeline.jobs:
            image = self._extract_image_name(job.data.get("image"))
            if image and self._is_latest(image):
                pos = _get_pos(job.data, "image")
                issues.append(
                    self._make_issue(
                        message=f"Образ '{image}' использует тег 'latest'",
                        line=pos.line if pos else 0,
                        col=pos.col if pos else 0,
                        job_name=job.name,
                        fix_suggestion="Укажите конкретную версию, например: node:20-alpine",
                    )
                )

        return issues

    @staticmethod
    def _is_latest(image: str) -> bool:
        name = image.split("/")[-1]
        if ":" not in name:
            return True
        tag = name.split(":")[-1]
        return tag == "latest"

    @staticmethod
    def _extract_image_name(image_val: object) -> str | None:
        if isinstance(image_val, str):
            return image_val
        if isinstance(image_val, CommentedMap):
            name = image_val.get("name")
            return str(name) if name else None
        return None


#
# SEC003
#

@registry.register
class PrivilegedModeRule(BaseRule):

    rule_id = "SEC003"
    severity = Severity.ERROR
    category = Category.SECURITY
    description = "Privileged mode даёт контейнеру полный доступ к хост-системе"

    def check(self, pipeline: ParsedPipeline) -> list[Issue]:
        issues: list[Issue] = []

        for job in pipeline.jobs:
            self._check_job(job.data, job.name, issues)

        return issues

    def _check_job(self, job_data: CommentedMap, job_name: str, issues: list[Issue]) -> None:
        variables = job_data.get("variables", {})
        if isinstance(variables, CommentedMap):
            for key in variables:
                if "privileged" in str(key).lower() and str(variables[key]).lower() == "true":
                    pos = _get_pos(variables, key)
                    issues.append(
                        self._make_issue(
                            message=f"Переменная '{key}' включает privileged mode",
                            line=pos.line if pos else 0,
                            job_name=job_name,
                            fix_suggestion=(
                                "Рассмотрите kaniko или buildah как альтернативу "
                                "Docker-in-Docker без privileged mode"
                            ),
                        )
                    )


#
# SEC004
#

@registry.register
class PublicArtifactsRule(BaseRule):

    rule_id = "SEC004"
    severity = Severity.WARNING
    category = Category.SECURITY
    description = "Артефакты с public: true доступны без аутентификации"

    def check(self, pipeline: ParsedPipeline) -> list[Issue]:
        issues: list[Issue] = []

        for job in pipeline.jobs:
            artifacts = job.data.get("artifacts")
            if not isinstance(artifacts, CommentedMap):
                continue
            if artifacts.get("public") is True:
                pos = _get_pos(artifacts, "public")
                issues.append(
                    self._make_issue(
                        message="Артефакты доступны публично без аутентификации (public: true)",
                        line=pos.line if pos else 0,
                        job_name=job.name,
                        fix_suggestion=(
                            "Удалите 'public: true' если артефакты не должны быть "
                            "доступны внешним пользователям"
                        ),
                    )
                )

        return issues


#
# SEC005
#

_CURL_PIPE_PATTERN = re.compile(
    r"(curl|wget).+\|\s*(ba)?sh",
    re.IGNORECASE | re.DOTALL,
)


@registry.register
class CurlPipeBashRule(BaseRule):

    rule_id = "SEC006"
    severity = Severity.ERROR
    category = Category.SECURITY
    description = "Загрузка и немедленное исполнение скрипта (curl/wget | bash/sh)"

    def check(self, pipeline: ParsedPipeline) -> list[Issue]:
        issues: list[Issue] = []

        for job in pipeline.jobs:
            for script_key in ("script", "before_script", "after_script"):
                script = job.data.get(script_key)
                if not isinstance(script, (list,)):
                    continue
                for i, line in enumerate(script):
                    if isinstance(line, str) and _CURL_PIPE_PATTERN.search(line):
                        try:
                            pos_line = script.lc.item(i)[0] + 1
                        except (AttributeError, KeyError, TypeError):
                            pos_line = 0
                        issues.append(
                            self._make_issue(
                                message=f"Небезопасный паттерн в '{script_key}': curl/wget piped to shell",
                                line=pos_line,
                                job_name=job.name,
                                fix_suggestion=(
                                    "Скачайте скрипт отдельно, проверьте контрольную сумму, "
                                    "затем выполните: curl -o install.sh URL && "
                                    "sha256sum -c install.sh.sha256 && bash install.sh"
                                ),
                            )
                        )

        return issues


#
# SEC005
#

_SIGNING_TOOLS = re.compile(
    r"\b(cosign\s+verify|notary\s+verify|skopeo\s+inspect.*sig|"
    r"docker\s+trust\s+inspect)\b",
    re.IGNORECASE,
)

_EXTERNAL_REGISTRIES = re.compile(
    r"^(?!localhost|registry\.gitlab|.*\.internal).*\.(io|com|org|net)/",
    re.IGNORECASE,
)


@registry.register
class ImageSignatureRule(BaseRule):

    rule_id = "SEC005"
    severity = Severity.INFO
    category = Category.SECURITY
    description = "Образы из внешних реестров не верифицируются (cosign/notary)"

    def check(self, pipeline: ParsedPipeline) -> list[Issue]:
        issues: list[Issue] = []

        external_images: list[tuple[str, int, str | None]] = []

        if pipeline.image and _EXTERNAL_REGISTRIES.match(pipeline.image):
            pos = pipeline.image_pos
            external_images.append((pipeline.image, pos.line if pos else 0, None))

        for job in pipeline.jobs:
            img_val = job.data.get("image")
            if img_val is None:
                continue
            img_name = str(img_val) if isinstance(img_val, str) else (
                str(img_val.get("name", "")) if hasattr(img_val, "get") else ""
            )
            if img_name and _EXTERNAL_REGISTRIES.match(img_name):
                pos = _get_pos(job.data, "image")
                external_images.append((img_name, pos.line if pos else 0, job.name))

        if not external_images:
            return []

        has_signing = self._pipeline_uses_signing(pipeline)
        if has_signing:
            return []

        img, line, job_name = external_images[0]
        issues.append(
            self._make_issue(
                message=(
                    f"Образ '{img}' из внешнего реестра не проверяется на подпись"
                ),
                line=line,
                job_name=job_name,
                fix_suggestion=(
                    "Добавьте проверку подписи: cosign verify <image> "
                    "или настройте Docker Content Trust: DOCKER_CONTENT_TRUST=1"
                ),
            )
        )
        return issues

    def _pipeline_uses_signing(self, pipeline: ParsedPipeline) -> bool:
        for job in pipeline.jobs:
            for key in ("script", "before_script", "after_script"):
                scripts = job.data.get(key, [])
                if not isinstance(scripts, list):
                    continue
                for cmd in scripts:
                    if isinstance(cmd, str) and _SIGNING_TOOLS.search(cmd):
                        return True
        return False
