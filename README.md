# Tomorrow Scraper

To run, copy an api key to a file called `api_key` in a directory called `data/` at the root of the project and run `docker compose up`. This will create a SQLite database file in `data/` and begin running the scraping service. On initialization, and every hour after, the scraper will pull data from Tomrorrow.io and put it in this database file. The Jupyter notebook in `notebooks/` then queries this file to report on:

- The latest temperature and windspeed for the 10 requested geolocations.
- An hourly time series of temperature, wind speed, humidity, and the uvIndex of a selected location.

## Design philosophy

Tomorrow Scraper uses `requests` to query `tomorrow.io` as an industry standard and SQLite as a hosting database. SQLite is fast to set up, can be hosted locally with ease, and creates DB files that can be copied around in a pinch. SQLite's biggest pitfall is that it is a client and file instead of a client and server, which makes it difficult if not outright impossible to run in a distributed environment. For productionized solutions I prefer a proper RDBMS, namely Postgres.

Tomorrow Scraper functions by taking each coordinate, querying for its weather values from tomorrow.io, and putting each daily JSON sub-object from the query into `Weather.db`. Since tomorrow.io provides forecasting data five days into the future and we are running scrapes every hour, there is a lot of redundant data in `Weather.db`.

I elected to keep this redundant data for two reasons:

- I don't have to manage the state of the database to determine whether or not to insert/update columns, which keeps my code simple.
- It's better to have data and not need it than need it and not have it.
        
However, there is a big drawback with this solution: there is more data than needed to generate reports, which is difficult to read and computationally expensive to query. To mitigate this, I could query the database after querying tomorrow.io, and run an update with new data on any record with matching coordinates and dateteime. As a tradeoff, the code would have to add complexity to maintain DB state and even though most of it would be redundant, we would lose some of the data being scraped.

More granular design choices are annotated and commented throughout the code.

## Testing philosopy

The majority of the problem statement consists of moving data from an api to a database. Since the majority of this work is I/O based, there's not much code that can be unit tested as a pure function. If there were transformations on the data (ex: store the median forecasted temperature of an api query in the database), I would write those transformations as pure functions and write applicable unit tests.

Since anything in the code that could be seen as a unit is tightly coupled I/O work, the most effective form of testing demonstrates that the entire codebase integrates properly and fulfills its requrirements. As such there is a test that identifies requirements in the problem statement and confirms they are fulfilled by running the application. As the project expands in scope, this test could be automated to serve as a regression test.