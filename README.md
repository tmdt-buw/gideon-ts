# Gideon-TS: Efficient Exploration and Labeling of Multivariate Industrial Sensor Data

Gideon TS is a general purpose semi-automatic labeling tool, which is tailored to the needs of industrial sensor data. 
The tool supports datasets that are available in a wide range of time series forms and contain an arbitrary number of label classes. 
It is also suitable for visualizing and interactively labeling large amounts of data by storing sensor data in a time series database and, based on the size of the retrieved data, sampling and aggregating it if necessary. We also develop a support system to obtain label suggestions and thus to explore and label even large amounts of data in a short time. 
In order to do this, we divide the time series into windows and use an unsupervised learning approach to detect anomalous windows and flag them as potential error cases if they exceed a threshold configured by the user. Based on errors already labeled, we perform a similarity search and assign a corresponding error class.

## Cite as

```
@article{LANGER.2022,
    author={Langer, Tristan and Welbers, Viktor and Meisen, Tobias},
    title={{Gideon-TS: Efficient Exploration and Labeling of Multivariate Industrial Sensor Data}},
    booktitle={Proceedings of the 24th International Conference on Enterprise Information Systems - Volume 1},
    year={2022},
    pages={321-331},
    publisher={SciTePress},
    organization={INSTICC},
    isbn={978-989-758-569-2},
    issn={2184-4992},
}
```

## Start and develop application

### Infrastructure 

Gideon-TS uses TimescaleDB as database and Redis for caching. Both can be started with running `docker-compose up -d` inside ./docker folder.

### Frontend

Angular Frontend

With npm installed switch to ./frontend folder and run `npm i` to install dependencies and `npm start` to start the application afterwards.

### Backend

FastAPI Backend (https://fastapi.tiangolo.com/)

With python >= 3.9 installed switch to ./backend folder and run `pip install -r requirements.txt` to install dependencies and `uvicorn main:app --workers 8` to start backend.
Gideon-TS need multiple workers otherwise long-running requests may block the server.

### Application and API

Application is available at `http://localhost:4200/` when frontend is running.
API is available at `localhost:5000/docs` when backend is running.