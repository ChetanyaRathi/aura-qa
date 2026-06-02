"""cli.py - the keyboard control for AuraQA.

Examples:
    python cli.py generate --url https://example.com
    python cli.py run --suite tests_store/example_suite.json
    python cli.py heal --suite tests_store/example_suite.json --headed
"""

from __future__ import annotations

import argparse
import sys

from auraqa import generator, runner, reporter


def cmd_generate(args):
    suite = generator.generate_suite(args.url, n_flows=args.flows)
    print(f"Generated {len(suite.steps)} steps for suite '{suite.name}'.")


def cmd_run(args, heal: bool):
    suite = generator.load_suite(args.suite)
    result = runner.run_suite(suite, heal=heal, headless=not args.headed)

    # Persist any healed selectors back into the suite file.
    if heal and result.healed:
        generator.save_suite(suite, args.suite)

    path = reporter.build_report(result)
    print(f"\nPassed: {result.passed}  Healed: {result.healed}  "
          f"Failed: {result.failed}")
    print(f"Report: {path}")
    sys.exit(1 if result.failed else 0)


def main():
    parser = argparse.ArgumentParser(description="AuraQA self-healing test agent")
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="write tests for a URL")
    g.add_argument("--url", required=True)
    g.add_argument("--flows", type=int, default=3)

    r = sub.add_parser("run", help="run a suite (no healing)")
    r.add_argument("--suite", required=True)
    r.add_argument("--headed", action="store_true", help="show the browser")

    h = sub.add_parser("heal", help="run a suite with self-healing on")
    h.add_argument("--suite", required=True)
    h.add_argument("--headed", action="store_true", help="show the browser")

    args = parser.parse_args()
    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "run":
        cmd_run(args, heal=False)
    elif args.command == "heal":
        cmd_run(args, heal=True)


if __name__ == "__main__":
    main()
