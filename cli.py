import os
import sys

import click

from .config import Config, WORK_DIR
from .session.manager import SessionManager
from .agent import run_agent_simple


@click.command()
@click.option("--provider", default="", help="LLM provider (openai, anthropic, deepseek, ollama)")
@click.option("--model", default="", help="Model name")
@click.option("--api-key", default="", help="API key")
@click.option("--work-dir", default="", help="Working directory")
@click.option("--simple", is_flag=True, help="Use simple CLI mode (no TUI)")
@click.option("--version", is_flag=True, help="Show version")
def main(provider, model, api_key, work_dir, simple, version):
    if version:
        print("rebeca v0.2.0")
        return

    config = Config()

    if provider:
        config.provider = provider
    if model:
        config.model = model
    if api_key:
        config.api_key = api_key
    if work_dir:
        os.chdir(work_dir)
        os.environ["REBECA_WORK_DIR"] = work_dir

    if simple:
        run_agent_simple(config)
        return

    try:
        from .tui.app import RebecaApp
        manager = SessionManager(config)
        manager.create_session("Main")
        app = RebecaApp(manager)
        app.run()
    except ImportError as e:
        print(f" TUI not available ({e}), falling back to simple mode")
        run_agent_simple(config)
    except Exception as e:
        print(f" Error launching TUI: {e}")
        print(" Falling back to simple mode...")
        run_agent_simple(config)


if __name__ == "__main__":
    main()
