import os
import httpx
from fastapi import FastAPI, Request, Response

app = FastAPI(title="API Gateway")

SERVICES = {
    "users": os.getenv("USER_SERVICE_URL", "").rstrip("/"),
    "products": os.getenv("PRODUCT_SERVICE_URL", "").rstrip("/"),
    "orders": os.getenv("ORDER_SERVICE_URL", "").rstrip("/"),
}

@app.get("/health")
def health():
    return {"service": "api-gateway", "status": "healthy"}

@app.api_route("/api/{name}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/{name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(name: str, request: Request, path: str = ""):
    base = SERVICES.get(name)
    if not base:
        return Response(content='{"detail":"Unknown service"}',
                        status_code=404, media_type="application/json")

    url = f"{base}/{name}" + (f"/{path}" if path else "")
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.request(
                request.method,
                url,
                params=request.query_params,
                content=await request.body(),
                headers={"content-type": request.headers.get("content-type", "application/json")},
            )
        except httpx.RequestError:
            return Response(content='{"detail":"Service unavailable"}',
                            status_code=503, media_type="application/json")

    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type"))