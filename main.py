import uvicorn
from fastapi import FastAPI
import logging
from routers import auth, genres

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:\t%(asctime)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
app = FastAPI()
app.include_router(auth.router)
app.include_router(genres.router)


def main():
    uvicorn.run("main:app", reload=True)


if __name__ == "__main__":
    main()
