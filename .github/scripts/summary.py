"""Writes a Markdown pass/fail table from a pytest JUnit XML file, for the GitHub Actions summary.

Usage: python .github/scripts/summary.py "<title>" reports/junit.xml >> "$GITHUB_STEP_SUMMARY"
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    """Prints the table for one JUnit XML file: totals, then the names of the failed tests."""
    title, path = sys.argv[1], Path(sys.argv[2])
    print(f"### {title}\n")
    if not path.exists():
        print("No results file: the tests did not run (see the job log).")
        return
    root = ET.parse(path).getroot()
    # pytest writes <testsuites><testsuite tests=.. failures=.. errors=.. skipped=..>
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    total = int(suite.get("tests", 0))
    failed = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    passed = total - failed - skipped
    print("| Total | Passed | Failed | Skipped | Time |")
    print("|---|---|---|---|---|")
    print(f"| {total} | {passed} | {failed} | {skipped} | {float(suite.get('time', 0)):.0f} s |")
    if failed:
        print("\nFailed:")
        for case in suite.iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                print(f"- `{case.get('classname')}.{case.get('name')}`")
    print("\nHTML report: see the run's artifacts.")


if __name__ == "__main__":
    main()
