

from fastapi import FastAPI
from app.api.v1.routes import v1_router


app = FastAPI(title="Statement Parse")

app.include_router(router=v1_router)




