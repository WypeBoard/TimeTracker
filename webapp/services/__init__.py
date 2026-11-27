# webapp/services/ — independent web-service functions that read/write the
# shared SQLite database directly via db/repository.py.
#
# This is the webapp/ equivalent of app/'s *Storage.py layer. Per
# features/standalone-web-app.md Non-Goals, webapp/ does not reuse
# app.Commands / app.*Storage / app.AppContext — these modules are written
# fresh, independently, even where the query shape mirrors an existing
# app/ module (e.g. app/EpicStorage.py, app/SettingsStorage.py).
