# PyInstaller spec for the bundled backend that the packaged Electron app runs.
# Build from backend/ with the backend's virtual environment (npm run build:backend does this):
#     python -m PyInstaller packaging/chatbot-backend.spec --noconfirm
# Output: backend/dist/chatbot-backend/ (the program and its files), which electron-builder
# copies into the app's resources (package.json "extraResources").
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

backend = SPECPATH + "/.."

datas = [
    (backend + "/knowledge", "knowledge"),            # conversation rules, answers, facts
    (backend + "/templates/email", "templates/email"),  # parent email templates
]
binaries = []
hiddenimports = []

# spaCy and its English model find their parts through package metadata and registries
for package in ("spacy", "en_core_web_sm", "thinc", "srsly", "catalogue", "confection", "spacy_legacy",
                "spacy_loggers", "weasel", "blis", "murmurhash", "cymem", "preshed", "wasabi", "langcodes"):
    try:
        package_datas, package_binaries, package_hidden = collect_all(package)
    except Exception:
        continue  # not installed in this environment
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

# llama-cpp-python: the Python package and llama.cpp's shared libraries (lib/), to run the model
llama_datas, llama_binaries, llama_hidden = collect_all("llama_cpp")
datas += llama_datas
binaries += llama_binaries
hiddenimports += llama_hidden

# Modules imported only by name at run time
hiddenimports += collect_submodules("uvicorn")
hiddenimports += collect_submodules("apscheduler")
hiddenimports += ["passlib.handlers.bcrypt", "jose.backends.cryptography_backend", "email_validator"]
datas += copy_metadata("APScheduler")

a = Analysis(
    [backend + "/run_backend.py"],
    pathex=[backend],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["pytest", "black", "flake8", "mypy", "tkinter", "PIL"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="chatbot-backend", console=True)
coll = COLLECT(exe, a.binaries, a.datas, name="chatbot-backend")
