from locust import HttpUser, task, between

class PetstoreLoadTest(HttpUser):
    # 1. Simulate human reading time
    wait_time = between(1, 5)

    # 2. Define the action the user will take
    @task
    def get_available_pets(self):
        # 3. self.client acts just like the 'requests' library, but it tracks metrics automatically!
        # We use name="..." to group our metrics cleanly in the reports.
        self.client.get(
            url="/pet/findByStatus?status=available",
            name="Get Available Pets"
        )