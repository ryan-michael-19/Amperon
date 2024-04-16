Delete or move Weather.db (ideally there would be a test enviornment where we could refresh the database).

Run `docker compose up`

Wait for scrape to finish. Export Weather.db to csv as a test artifact and ensure it has weather data from yesterday to five days in the future. Some coordinates may be missing due to how aggressively the tomorrow.io throttles requests. Ideally these test artifacts would be attached to a work ticket (Jira issue etc.), which would signify that ticket is ready for code review.

If there were a test enviornment separate from the production enviornment, we could set up a container that runs with the from_file flag, and run it on a test enviornment with json files. This ensures we are testing with the same input on each run. From there we would be able to write an expected test output and ensure running on the test input creates the same test output whenever the code changes.