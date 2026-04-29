import pytest
from analyzer.parsers.yaml_parser import YamlParser, ParsedPipeline


@pytest.fixture
def parser():
    return YamlParser()


# 
# Базовый парсинг
# 

def test_parse_empty_file(parser):
    pipeline = parser.parse_string("")
    assert pipeline.jobs == []
    assert pipeline.stages == []


def test_parse_stages(parser):
    yaml = """
stages:
  - build
  - test
  - deploy
"""
    pipeline = parser.parse_string(yaml)
    assert pipeline.stages == ["build", "test", "deploy"]


def test_parse_global_image(parser):
    yaml = """
image: python:3.12-slim

build:
  script: echo hi
"""
    pipeline = parser.parse_string(yaml)
    assert pipeline.image == "python:3.12-slim"


def test_parse_global_variables(parser):
    yaml = """
variables:
  ENV: production
  VERSION: "1.0.0"

build:
  script: echo hi
"""
    pipeline = parser.parse_string(yaml)
    assert pipeline.variables["ENV"] == "production"
    assert pipeline.variables["VERSION"] == "1.0.0"


# 
# Jobs
# 

def test_parse_single_job(parser):
    yaml = """
build:
  stage: build
  script:
    - pip install -r requirements.txt
    - python -m build
"""
    pipeline = parser.parse_string(yaml)
    assert len(pipeline.jobs) == 1
    assert pipeline.jobs[0].name == "build"


def test_parse_multiple_jobs(parser):
    yaml = """
build:
  script: echo build

test:
  script: echo test

deploy:
  script: echo deploy
"""
    pipeline = parser.parse_string(yaml)
    job_names = [j.name for j in pipeline.jobs]
    assert "build" in job_names
    assert "test" in job_names
    assert "deploy" in job_names


def test_reserved_keys_not_parsed_as_jobs(parser):
    yaml = """
stages:
  - build

variables:
  FOO: bar

default:
  image: python:3.12

build:
  script: echo hi
"""
    pipeline = parser.parse_string(yaml)
    job_names = [j.name for j in pipeline.jobs]
    assert "stages" not in job_names
    assert "variables" not in job_names
    assert "default" not in job_names
    assert "build" in job_names


# 
# line:col)
# 

def test_job_position_is_tracked(parser):
    yaml = """stages:
  - build

build:
  script: echo hi
"""
    pipeline = parser.parse_string(yaml)
    build_job = next(j for j in pipeline.jobs if j.name == "build")
    assert build_job.pos.line == 4


def test_image_position_is_tracked(parser):
    yaml = """stages:
  - build
image: python:3.12
build:
  script: echo hi
"""
    pipeline = parser.parse_string(yaml)
    assert pipeline.image_pos is not None
    assert pipeline.image_pos.line == 3


# 
# Unexpected
# 

def test_parse_image_as_mapping(parser):
    yaml = """
build:
  image:
    name: python:3.12-slim
    entrypoint: [""]
  script: echo hi
"""
    pipeline = parser.parse_string(yaml)
    assert pipeline.image is None
    assert len(pipeline.jobs) == 1


def test_parse_job_with_variables(parser):
    yaml = """
deploy:
  script: ./deploy.sh
  variables:
    ENV: production
    DB_HOST: localhost
"""
    pipeline = parser.parse_string(yaml)
    assert len(pipeline.jobs) == 1
    deploy = pipeline.jobs[0]
    assert "variables" in deploy.data
    assert deploy.data["variables"]["ENV"] == "production"
