## Requirements.

Python >= 3.10

## Installation

Install requirements:

```bash
pip install -r requirements.txt
```

## Run with Pycharm or Bash

Run main.py in Pycharm

or run via console:

```bash
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

and open your browser at `http://localhost:5000/docs/` to see the docs.

## Running with Docker

To run the server on a Docker container, please execute the following from the root directory:

```bash
docker-compose up --build
```

## Tests

To run the tests:

```bash
pip3 install pytest
PYTHONPATH=src pytest tests
```
