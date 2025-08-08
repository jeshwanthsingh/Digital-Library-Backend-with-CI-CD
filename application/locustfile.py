from locust import HttpUser, task, between

class MyWebsiteUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    @task
    def get_homepage(self):
        self.client.get("/") # Assuming your app's homepage is at the root

    # Add more tasks here to simulate other user behaviors
    # @task
    # def get_api_listings(self):
    #     self.client.get("/api/listings")
