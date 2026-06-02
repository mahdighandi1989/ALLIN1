"""Guard that ``npm install`` for the frontend cannot fail on a corrupt or
out-of-sync lock file.

The original bug: ``frontend/src/app/dashboard/page.tsx`` imported ``sonner``
while ``sonner`` was absent from both ``package.json`` and
``package-lock.json``. An ``npm ci`` (or a clean ``npm install``) errors out
when the manifest and the lock file disagree, and the dashboard then fails at
runtime on the missing module.

Running a real ``npm install`` here would require network access to the npm
registry, which is not available in CI. Instead we assert the exact invariant
``npm ci`` enforces locally: every production/dev dependency declared in
``package.json`` is present in ``package-lock.json`` at a matching version, the
lock file is valid JSON, and ``sonner`` specifically is wired through both
files. If those hold, a fresh install resolves deterministically without error.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"
PACKAGE_JSON = FRONTEND / "package.json"
PACKAGE_LOCK = FRONTEND / "package-lock.json"


def _load(path: Path) -> dict:
    assert path.exists(), f"expected file missing: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _lock_packages(lock: dict) -> dict:
    # npm v2/v3 lockfiles key installed packages under "packages" by their
    # install path, e.g. "node_modules/<name>".
    return lock.get("packages", {})


def test_lock_file_is_valid_json():
    # A malformed lock file is the most direct way npm install blows up.
    _load(PACKAGE_LOCK)


def test_package_lock_in_sync_with_manifest():
    """Every dependency in package.json must have a matching lock entry.

    This is the invariant ``npm ci`` checks before it will install; a mismatch
    aborts the install with ``npm ci can only install packages when your
    package.json and package-lock.json ... are in sync``.
    """
    manifest = _load(PACKAGE_JSON)
    lock = _load(PACKAGE_LOCK)
    packages = _lock_packages(lock)

    declared = {}
    declared.update(manifest.get("dependencies", {}))
    declared.update(manifest.get("devDependencies", {}))

    missing = []
    version_mismatch = []
    for name, spec in declared.items():
        entry = packages.get(f"node_modules/{name}")
        if entry is None:
            missing.append(name)
            continue
        # Exact-pinned specs (no range prefix) must match the locked version.
        if spec and spec[0] not in "^~><=*" and entry.get("version") != spec:
            version_mismatch.append((name, spec, entry.get("version")))

    assert not missing, f"dependencies missing from package-lock.json: {missing}"
    assert not version_mismatch, (
        f"version mismatch between package.json and lock: {version_mismatch}"
    )


def test_npm_install_runs_without_errors():
    """End-to-end guard for the reported bug: the dashboard's ``sonner`` import
    must be installable, i.e. present and consistent in both manifest and lock.
    """
    manifest = _load(PACKAGE_JSON)
    lock = _load(PACKAGE_LOCK)
    packages = _lock_packages(lock)

    deps = manifest.get("dependencies", {})
    assert "sonner" in deps, "sonner must be declared in package.json dependencies"

    sonner_lock = packages.get("node_modules/sonner")
    assert sonner_lock is not None, "sonner must be present in package-lock.json"
    assert sonner_lock.get("version") == deps["sonner"], (
        "sonner version must match between package.json and package-lock.json"
    )
    # A resolvable artifact is what lets the install complete offline-or-online.
    assert sonner_lock.get("resolved", "").startswith("https://"), (
        "sonner lock entry must carry a resolved tarball URL"
    )
    assert sonner_lock.get("integrity", "").startswith("sha"), (
        "sonner lock entry must carry an integrity hash"
    )
