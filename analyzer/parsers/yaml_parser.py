#
# YAML parser for .gitlab-ci.yml
#

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from analyzer.logger import get_logger

log = get_logger(__name__)


#
# Data structure
#

@dataclass
class Position:
    line: int
    col: int

    def __str__(self) -> str:
        return f"line {self.line}, col {self.col}"


@dataclass
class JobNode:
    """Один джоб из пайплайна."""
    name: str
    data: CommentedMap
    pos: Position


@dataclass
class ParsedPipeline:
    stages: list[str] = field(default_factory=list)
    stages_pos: Position | None = None

    variables: dict[str, str] = field(default_factory=dict)
    variables_pos: Position | None = None

    default: CommentedMap | None = None
    default_pos: Position | None = None

    image: str | None = None
    image_pos: Position | None = None

    jobs: list[JobNode] = field(default_factory=list)

    raw_data: CommentedMap | None = None

    filename: str = ".gitlab-ci.yml"


#
# Зарезервированые ключи верхнего уровня
#

RESERVED_KEYS = {
    "stages",
    "variables",
    "default",
    "image",
    "services",
    "before_script",
    "after_script",
    "cache",
    "include",
    "workflow",
    "pages",
}

#
# Extra funcs
#

def _get_pos(data: CommentedMap, key: str) -> Position | None:
    try:
        line, col = data.lc.data[key][:2]
        return Position(line=line + 1, col=col + 1)
    except (AttributeError, KeyError, TypeError):
        return None


def _extract_string(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None

#
# Main parcer
#

class YamlParser:

#
#    Использование:
#        parser = YamlParser()
#
#     из файла
#        pipeline = parser.parse_file(Path(".gitlab-ci.yml"))
#
#     из строки (tests and API)
#        pipeline = parser.parse_string(yaml_content)
#

    def __init__(self) -> None:
        self._yaml = YAML()
        self._yaml.preserve_quotes = True

    #
    # Pub API
    #

    def parse_file(self, path: Path) -> ParsedPipeline:
        content = path.read_text(encoding="utf-8")
        pipeline = self._parse(content)
        pipeline.filename = path.name
        return pipeline

    def parse_string(self, content: str, filename: str = ".gitlab-ci.yml") -> ParsedPipeline:
        pipeline = self._parse(content)
        pipeline.filename = filename
        return pipeline

    #
    # Inner logic
    #

    def _parse(self, content: str) -> ParsedPipeline:
        log.debug("Парсинг YAML (%d байт)", len(content.encode()))
        data: CommentedMap = self._yaml.load(content)

        if data is None:
            log.warning("Файл пустой — возвращён пустой пайплайн")
            return ParsedPipeline(raw_data=CommentedMap())

        if not isinstance(data, CommentedMap):
            log.error("YAML не является маппингом (тип: %s)", type(data).__name__)
            raise ValueError("Файл не является корректным YAML-маппингом")

        pipeline = ParsedPipeline(raw_data=data)

        # stages
        if "stages" in data:
            pipeline.stages_pos = _get_pos(data, "stages")
            stages_val = data["stages"]
            if isinstance(stages_val, (list, CommentedSeq)):
                pipeline.stages = [str(s) for s in stages_val]

        # variables
        if "variables" in data:
            pipeline.variables_pos = _get_pos(data, "variables")
            vars_val = data["variables"]
            if isinstance(vars_val, CommentedMap):
                pipeline.variables = {
                    str(k): str(v) if v is not None else ""
                    for k, v in vars_val.items()
                }

        # default
        if "default" in data:
            pipeline.default_pos = _get_pos(data, "default")
            pipeline.default = data["default"]

        # global image
        if "image" in data:
            pipeline.image_pos = _get_pos(data, "image")
            img = data["image"]
            if isinstance(img, str):
                pipeline.image = img
            elif isinstance(img, CommentedMap) and "name" in img:
                # image: {name: "python:3.12", entrypoint: [...]}
                pipeline.image = str(img["name"])

        # jobs-
        for key in data:
            if key in RESERVED_KEYS:
                continue
            value = data[key]
            if not isinstance(value, CommentedMap):
                continue
            job_indicators = {"script", "extends", "trigger", "needs", "stage"}
            if not any(ind in value for ind in job_indicators):
                continue

            pos = _get_pos(data, key)
            if pos is None:
                pos = Position(line=0, col=0)

            pipeline.jobs.append(JobNode(name=str(key), data=value, pos=pos))

        return pipeline
