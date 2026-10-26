"""
Start the backend server. This is the entry point of the bundled backend that the packaged
app runs (see packaging/chatbot-backend.spec); during development, python main.py does the
same with auto-reload.

The working directory holds the per-user files: .env, data/ (the database), logs/ and
models/. The packaged app starts this in the app's user data folder.
"""

import multiprocessing

import uvicorn


def main() -> None:
    from main import app
    from utils.config import settings

    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level=settings.LOG_LEVEL.lower())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
