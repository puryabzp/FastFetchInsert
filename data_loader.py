import time
import asyncpg
import json
from prefect import flow, task, get_run_logger
from requests_futures.sessions import FuturesSession


# Read configuration from conf.json
with open("conf.json", "r") as config_file:
    config = json.load(config_file)
    db_config = config["database"]


@task(name="Fetch Data")
def fetch_data():
    logger = get_run_logger()
    url = config["url"]    # a mock api, you can add your api address

    session = FuturesSession()
    start_time = time.time()
    response = session.get(url)
    end_time = time.time()
    response = response.result()

    if response.status_code == 200:
        data = response.json()
        logger.info("--- %s seconds for fetching data, fetched %s record ---", (end_time - start_time), len(data))
        return data
    else:
        logger.error("Failed to fetch data. Status code: %s", response.status_code)
        return None


@task(name="Insert Data")
async def insert_data_into_db(data):
    logger = get_run_logger()
    connection = await asyncpg.connect(
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database_name"],
        host=db_config["host"]
    )

    try:
        start_time = time.time()
        users = data
        if users:
            user_data = [(user['first'], user['last']) for user in users]
            query = "INSERT INTO mocktest (givenname, familyname) VALUES ($1, $2)"
            await connection.executemany(query, user_data)
            end_time = time.time()
    finally:
        await connection.close()

    insertion_time = end_time - start_time
    logger.info("Inserted %s users into the database in %s seconds", len(user_data), insertion_time)


@flow(name="Fetch And Insert", log_prints=True)
def fetch_customers():
    data = fetch_data()
    insert_data_into_db(data)


if __name__ == "__main__":
    fetch_customers.serve(name="fetch_and_insert")
