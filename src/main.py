import os
import uvicorn

from api.app import app
from database import db
from settings import settings

if __name__ == "__main__":
    host = settings.host
    port = settings.port
    log_level = settings.logging_level
    reload_enabled = settings.reload in ("1", "true", "yes")
    workers = settings.workers

    db.createAllTables()

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload_enabled,
        workers=(1 if reload_enabled else workers),
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level=log_level,
    )