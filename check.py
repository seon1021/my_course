import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parent


def run_git(args):
    try:
        return subprocess.run(
            ["git", *args],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            check=False,
        )
    except OSError as exc:
        return SimpleNamespace(returncode=1, stdout=b"", stderr=str(exc).encode("utf-8", errors="replace"))


def get_first_commit():
    result = run_git(["rev-list", "--max-parents=0", "HEAD"])
    if result.returncode != 0:
        return None
    commit = result.stdout.decode("utf-8", errors="replace").strip().splitlines()
    return commit[0] if commit else None


def git_file_bytes(commit, path):
    result = run_git(["show", f"{commit}:{path}"])
    if result.returncode != 0:
        return None
    return result.stdout


def check_responses_same(first_commit):
    relative = Path("project/data/responses_raw.csv")
    target = ROOT / relative
    if not target.is_file() or not first_commit:
        return False
    old_bytes = git_file_bytes(first_commit, relative.as_posix())
    if old_bytes is None:
        return False
    return target.read_bytes() == old_bytes


def check_exam_same(first_commit):
    exam_dir = ROOT / "exam"
    if not exam_dir.is_dir() or not first_commit:
        return False

    diff_result = run_git(["diff", "--quiet", first_commit, "--", "exam"])
    if diff_result.returncode != 0:
        return False

    untracked = run_git(["ls-files", "--others", "--exclude-standard", "--", "exam"])
    if untracked.returncode != 0:
        return False
    return not untracked.stdout.strip()


def check_report_placeholder_absent():
    report = ROOT / "project/report_draft.md"
    if not report.is_file():
        return False
    content = report.read_text(encoding="utf-8", errors="replace")
    return "(아직 쓰지 않음)" not in content


def main():
    first_commit = get_first_commit()

    results = [
        check_responses_same(first_commit),
        check_exam_same(first_commit),
        check_report_placeholder_absent(),
    ]

    lines = ["PASS" if ok else "FAIL" for ok in results]
    lines.append(str(sum(1 for ok in results if not ok)))
    output_text = "\n".join(lines)

    print(output_text)

    if len(sys.argv) == 2:
        output_path = Path(sys.argv[1])
        output_path.write_text(output_text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()