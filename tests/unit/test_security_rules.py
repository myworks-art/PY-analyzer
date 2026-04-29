# SEC001–SEC006
import pytest
from analyzer.parsers.yaml_parser import YamlParser
from analyzer.rules.security import (
    SecretInVariableRule,
    LatestImageTagRule,
    PrivilegedModeRule,
    PublicArtifactsRule,
    CurlPipeBashRule,
)
from analyzer.rules.base import Severity


@pytest.fixture
def parser():
    return YamlParser()


def parse(yaml_text: str):
    return YamlParser().parse_string(yaml_text)


# 
# SEC001
# 

class TestSecretInVariable:
    rule = SecretInVariableRule()

    def test_detects_password_in_global_variables(self):
        pipeline = parse("""
variables:
  DB_PASSWORD: "mysecretpassword"
build:
  script: echo hi
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].rule_id == "SEC001"
        assert issues[0].severity == Severity.ERROR
        assert "DB_PASSWORD" in issues[0].message

    def test_detects_token_in_job_variables(self):
        pipeline = parse("""
deploy:
  script: ./deploy.sh
  variables:
    API_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].job_name == "deploy"

    def test_ignores_variable_reference(self):
        pipeline = parse("""
variables:
  DB_PASSWORD: $DB_PASSWORD
build:
  script: echo hi
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 0

    def test_ignores_non_secret_variable(self):
        pipeline = parse("""
variables:
  APP_ENV: production
  PORT: "8080"
build:
  script: echo hi
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 0

    def test_detects_multiple_secrets(self):
        pipeline = parse("""
variables:
  DB_PASSWORD: "secret1"
  API_KEY: "abcdef123456"
  NORMAL_VAR: "hello"
build:
  script: echo hi
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 2

    def test_line_number_is_reported(self):
        pipeline = parse("""variables:
  DB_PASSWORD: "mysecret"
build:
  script: echo hi
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].line == 2 

# 
# SEC002
# 

class TestLatestImageTag:
    rule = LatestImageTagRule()

    def test_detects_latest_global_image(self):
        pipeline = parse("""
image: python:latest
build:
  script: echo hi
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].rule_id == "SEC002"

    def test_detects_image_without_tag(self):
        pipeline = parse("""
image: python
build:
  script: echo hi
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1

    def test_no_issue_for_pinned_image(self):
        pipeline = parse("""
image: python:3.12-slim
build:
  script: echo hi
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 0

    def test_detects_latest_in_job_image(self):
        pipeline = parse("""
build:
  image: node:latest
  script: npm build
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].job_name == "build"

    def test_detects_multiple_latest_images(self):
        pipeline = parse("""
image: python:latest

build:
  image: node:latest
  script: npm build

test:
  image: python:3.12
  script: pytest
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 2


# 
# SEC004
# 

class TestPublicArtifacts:
    rule = PublicArtifactsRule()

    def test_detects_public_artifacts(self):
        pipeline = parse("""
build:
  script: echo hi
  artifacts:
    public: true
    paths:
      - dist/
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].rule_id == "SEC004"

    def test_no_issue_for_private_artifacts(self):
        pipeline = parse("""
build:
  script: echo hi
  artifacts:
    paths:
      - dist/
    expire_in: 1 week
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 0


# 
# SEC006 
# 

class TestCurlPipeBash:
    rule = CurlPipeBashRule()

    def test_detects_curl_pipe_bash(self):
        pipeline = parse("""
setup:
  script:
    - curl https://example.com/install.sh | bash
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
        assert issues[0].rule_id == "SEC006"

    def test_detects_wget_pipe_sh(self):
        pipeline = parse("""
setup:
  script:
    - wget -q https://example.com/setup.sh | sh
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1

    def test_no_issue_for_safe_curl(self):
        pipeline = parse("""
setup:
  script:
    - curl -o install.sh https://example.com/install.sh
    - bash install.sh
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 0

    def test_detects_in_before_script(self):
        pipeline = parse("""
build:
  before_script:
    - curl https://get.helm.sh/install.sh | bash
  script: helm install .
""")
        issues = self.rule.check(pipeline)
        assert len(issues) == 1
