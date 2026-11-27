"""Manual startup entry point: `python -m webapp`.

Per features/standalone-web-app.md Requirements, startup is manual for now
(a .bat file or Startup-folder shortcut is sufficient — see
start_webapp.bat at the repository root). No auto-launch of the browser;
the user opens/pins the tab manually.
"""
import uvicorn

from webapp.Constants import HOST, PORT

if __name__ == "__main__":
    uvicorn.run("webapp.main:app", host=HOST, port=PORT, reload=False)
