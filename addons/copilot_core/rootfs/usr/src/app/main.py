import os

from waitress import serve

from copilot_core.app import create_app


def main() -> None:
    app = create_app()
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "8099"))
    serve(app, host=host, port=port)


if __name__ == "__main__":
    main()
