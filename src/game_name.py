#!/usr/bin/env python3

from main import runGame
import sys
import os
import logging
import argparse

# -------------------------------
# Configuration
# -------------------------------
LOG_LEVEL = logging.INFO

# -------------------------------
# Setup logging
# -------------------------------
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# -------------------------------
# Argument Parser
# -------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Your script description here.")
    parser.add_argument(
        "--input", "-i", type=str, help="Path to input file", required=False
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable debug logging"
    )
    return parser.parse_args()

# -------------------------------
# Main function
# -------------------------------
def main():
    args = parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("Script started.")
    
    # Example usage
    if args.input:
        if os.path.exists(args.input):
            logger.debug(f"Input file: {args.input}")
            # Do something with the file
        else:
            logger.error(f"File not found: {args.input}")
            sys.exit(1)

    # Add your main logic here
    logger.info("Script finished.")
    runGame(logger)

# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    main()
