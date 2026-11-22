"""Context and severity rules used for the robustness analysis and the validation pre-labels."""
import re

# A finding in these paths is not a deployable, real-world configuration.
NONPROD_RE = re.compile(
    r"(^|/)(tests?|testdata|test-data|fixtures?|examples?|samples?|demos?|e2e|mocks?|hack|sandbox|playground|"
    r"testing|spec|__tests__|positive|negative|bad|insecure|vulnerable)(/|$)|(^|/)test_[^/]*$|_test\.(tf|ya?ml)$",
    re.I)

# High-impact: the setting can directly enable access, escalation, exposure or data leakage.
HIGH_RE = re.compile(
    r"privilege ?escalation|privileged|root|net_raw|capabilit|\"\*\"|wildcard|admin|public|0\.0\.0\.0|"
    r"ingress|security group|exposed|host ?(network|pid|ipc|path|port)|encrypt|kms|tls|ssl|https|secret|password|"
    r"credential|service account token|seccomp|apparmor|read-only filesystem|rbac|cluster-admin|iam",
    re.I)


def context(path: str) -> str:
    return "nonprod" if NONPROD_RE.search(path or "") else "prod"


def tier(check_name: str) -> str:
    return "high" if HIGH_RE.search(check_name or "") else "hygiene"
