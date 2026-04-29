# Запуск: pytest tests/unit/test_parser_and_security.py -v
import pytest
from analyzer.parsers.yaml_parser import YamlParser


#
# Вспомогательная функция
#

def parse(yaml_text: str):
    return YamlParser().parse_string(yaml_text)


def run_rule(rule_class, yaml_text: str):
    pipeline = parse(yaml_text)
    return rule_class().check(pipeline)


#
# Tests
#

class TestYamlParser:

    def test_parse_empty_returns_pipeline(self):
        pipeline = parse("")
        assert pipeline is not None
        assert pipeline.jobs == []

    def test_parse_stages(self):
        pipeline = parse("""
stages:
  - build
  - test
  - deploy
""")
        assert pipeline.stages == ["build", "test", "deploy"]

    def test_parse_global_image(self):
        pipeline = parse("image: python:3.12-slim")
        assert pipeline.image == "python:3.12-slim"

    def test_parse_global_image_dict_form(self):
        pipeline = parse("""
image:
  name: python:3.12-slim
  entrypoint: [""]
""")
        assert pipeline.image == "python:3.12-slim"

    def test_parse_variables(self):
        pipeline = parse("""
variables:
  APP_ENV: production
  DB_HOST: localhost
""")
        assert pipeline.variables["APP_ENV"] == "production"
        assert pipeline.variables["DB_HOST"] == "localhost"

    def test_parse_job_detected(self):
        pipeline = parse("""
build:
  stage: build
  script:
    - echo hello
""")
        assert len(pipeline.jobs) == 1
        assert pipeline.jobs[0].name == "build"

    def test_parse_job_position(self):
        pipeline = parse("""
stages:
  - build

build-app:
  stage: build
  script:
    - echo hello
""")
        job = pipeline.jobs[0]
        assert job.pos.line > 0  

    def test_reserved_keys_not_parsed_as_jobs(self):
        pipeline = parse("""
stages: [build]
variables:
  FOO: bar
default:
  before_script:
    - echo hi
build:
  stage: build
  script:
    - echo build
""")

        assert len(pipeline.jobs) == 1
        assert pipeline.jobs[0].name == "build"

    def test_parse_job_without_script_using_extends(self):
        pipeline = parse("""
.base:
  script:
    - echo base

my-job:
  extends: .base
  stage: build
""")

        job_names = [j.name for j in pipeline.jobs]
        assert "my-job" in job_names


#
# SEC001
#

class TestSEC001:

    def setup_method(self):
        from analyzer.rules.security import SecretInVariableRule
        self.rule = SecretInVariableRule()

    def test_detects_password_in_plain_text(self):
        pipeline = parse("""
variables:
  DB_PASSWORD: "supersecret123"
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].rule_id == "SEC001"
        assert "DB_PASSWORD" in issues[0].message

    def test_ignores_variable_reference(self):
        pipeline = parse("""
variables:
  DB_PASSWORD: $DB_PASSWORD
""")
        issues = self.rule.check(pipeline)
        assert issues == []

    def test_detects_api_token(self):
        pipeline = parse("""
variables:
  API_TOKEN: "ghp_xxxxxxxxxxxxxxxx"
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1

    def test_ignores_non_secret_variable(self):
        pipeline = parse("""
variables:
  APP_ENV: production
  DEBUG: "false"
""")
        issues = self.rule.check(pipeline)
        assert issues == []

    def test_detects_secret_in_job_variables(self):
        pipeline = parse("""
deploy:
  stage: deploy
  script: ./deploy.sh
  variables:
    SECRET_KEY: "my-very-secret-key"
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].job_name == "deploy"

    def test_issue_has_fix_suggestion(self):
        pipeline = parse("""
variables:
  DB_PASSWORD: "hunter2"
""")
        issues = self.rule.check(pipeline)
        assert issues[0].fix_suggestion is not None


# 
# SEC002
# 

class TestSEC002:

    def setup_method(self):
        from analyzer.rules.security import LatestImageTagRule
        self.rule = LatestImageTagRule()

    def test_detects_global_latest(self):
        pipeline = parse("image: python:latest")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert "latest" in issues[0].message

    def test_detects_image_without_tag(self):
        pipeline = parse("image: python")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1

    def test_no_issue_for_specific_tag(self):
        pipeline = parse("image: python:3.12-slim")
        issues = self.rule.check(pipeline)
        assert issues == []

    def test_detects_latest_in_job(self):
        pipeline = parse("""
build:
  stage: build
  image: node:latest
  script: npm build
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].job_name == "build"


# 
# SEC006
# 

class TestSEC006:

    def setup_method(self):
        from analyzer.rules.security import CurlPipeBashRule
        self.rule = CurlPipeBashRule()

    def test_detects_curl_pipe_bash(self):
        pipeline = parse("""
install:
  stage: build
  script:
    - curl https://example.com/install.sh | bash
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].rule_id == "SEC006"

    def test_detects_wget_pipe_sh(self):
        pipeline = parse("""
setup:
  stage: build
  script:
    - wget -qO- https://get.example.com | sh
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1

    def test_safe_curl_no_pipe(self):
        pipeline = parse("""
download:
  stage: build
  script:
    - curl -o file.sh https://example.com/install.sh
    - bash file.sh
""")
        issues = self.rule.check(pipeline)
        assert issues == []


# 
# PERF001
# 

class TestPERF001:

    def setup_method(self):
        from analyzer.rules.performance import NoDependencyCacheRule
        self.rule = NoDependencyCacheRule()

    def test_detects_pip_without_cache(self):
        pipeline = parse("""
build:
  stage: build
  script:
    - pip install -r requirements.txt
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].rule_id == "PERF001"

    def test_no_issue_when_cache_present(self):
        pipeline = parse("""
build:
  stage: build
  cache:
    paths: [.pip-cache/]
  script:
    - pip install -r requirements.txt
""")
        issues = self.rule.check(pipeline)
        assert issues == []

    def test_detects_npm_install(self):
        pipeline = parse("""
frontend:
  stage: build
  script:
    - npm install
    - npm run build
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1


# 
# REL004
# 

class TestREL004:

    def setup_method(self):
        from analyzer.rules.reliability import NoTestStageRule
        self.rule = NoTestStageRule()

    def test_detects_missing_test_stage(self):
        pipeline = parse("""
stages:
  - build
  - deploy

build:
  stage: build
  script: echo build
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1

    def test_no_issue_when_test_stage_present(self):
        pipeline = parse("""
stages:
  - build
  - test
  - deploy
""")
        issues = self.rule.check(pipeline)
        assert issues == []
