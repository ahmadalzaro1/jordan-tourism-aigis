import os
os.environ.setdefault("DATA_MODE", "demo")
url=os.environ.get("GIS_VALIDATION_DATABASE_URL")
if url:
    if "127.0.0.1:5546/tourism_validation" not in url:
        raise RuntimeError("Tests require the isolated validation database")
    os.environ["DATABASE_URL"]=url
