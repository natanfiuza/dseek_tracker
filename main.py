"""Ponto de entrada do DeepSeek Accountant & Tracker."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dseek_tracker.gui import iniciar_app


def main():
    iniciar_app()


if __name__ == "__main__":
    main()
