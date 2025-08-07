## Quick start

### Run in Docker

`sudo docker compose up --build`

OR
### Run Local

Run next commands:

1. `python -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `uvicorn search_service.main:app --port 9000`

___

And service will be available on:

`127.0.0.1:9000`