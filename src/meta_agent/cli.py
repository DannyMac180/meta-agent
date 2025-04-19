import argparse
import sys
import json

from meta_agent.spec_schema import SpecSchema
from meta_agent.utils.logging import setup_logging
from meta_agent.orchestrator import MetaAgent


def main():
    parser = argparse.ArgumentParser(
        prog="meta-agent",
        description="Meta Agent CLI: generate code from a spec"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate agent code from specification"
    )
    gen_parser.add_argument(
        "--spec-file", "-s",
        type=str,
        required=True,
        help="Path to JSON spec file"
    )
    gen_parser.add_argument(
        "--audit",
        action="store_true",
        help="Enable audit mode"
    )
    gen_parser.add_argument(
        "--demo",
        action="store_true",
        help="Enable demo mode"
    )

    args = parser.parse_args()
    logger = setup_logging(__name__)
    logger.debug(f"Parsed args: {args}")

    if args.command == "generate":
        try:
            with open(args.spec_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load spec file: {e}")
            sys.exit(1)

        try:
            spec = SpecSchema(**data)
        except Exception as e:
            logger.error(f"Spec validation error: {e}")
            sys.exit(1)

        agent = MetaAgent()
        agent.run(spec, audit=args.audit, demo=args.demo)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
