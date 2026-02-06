# Skip API paths
        api_prefixes = ["auth/", "customers/", "facilities/", "stats/", "api/"]
        if any(path.startswith(prefix) for prefix in api_prefixes) or path in ["docs", "redoc", "openapi.json", "health"]:
            raise HTTPException(status_code=404, detail="Not found")