#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()


def run_tests(args):
    """Run the test suite"""
    # Ensure we have the required environment variables
    if not os.getenv("TEST_CONVERSATION_ID"):
        print("Warning: TEST_CONVERSATION_ID environment variable not set.")
        print("Tests will use the default conversation ID (20).")

    # Build the pytest command
    cmd = ["pytest"]

    if args.verbose:
        cmd.append("-v")

    if args.test_file:
        cmd.append(args.test_file)
    else:
        cmd.append("tests/")

    # Add markers if specified
    if args.markers:
        for marker in args.markers:
            cmd.append(f"-m {marker}")

    # Run the tests
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the test suite")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase verbosity")
    parser.add_argument("-f", "--test-file", help="Run tests in a specific file")
    parser.add_argument("-m", "--markers", nargs="+", help="Run tests with specific markers")

    args = parser.parse_args()
    sys.exit(run_tests(args))
