"""Small smoke tests for the competition-critical ERP paths.

These tests use Flask's test client and the configured local MySQL database.
Run them from the project root while the seeded database is available.
"""

import unittest

from app import app


class ErpSmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def login(self, username="manager", password="manager123", role="Manager"):
        return self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password, "role": role},
        )

    def test_health_and_database(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/db-health").status_code, 200)

    def test_login_and_session(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.get("/api/auth/me").get_json()["authenticated"])

    def test_employee_cannot_change_master_product_data(self):
        self.login("employee", "employee123", "Employee")
        response = self.client.post(
            "/api/products",
            json={"code": "TEST-DENIED", "name": "Test", "category": "Test", "price": 1},
        )
        self.assertEqual(response.status_code, 403)

    def test_manager_can_read_core_modules(self):
        self.login()
        for endpoint in (
            "/api/products",
            "/api/materials",
            "/api/suppliers",
            "/api/purchases",
            "/api/boms",
            "/api/production",
            "/api/customers",
            "/api/sales",
            "/api/dashboard/summary",
            "/api/audit-logs",
            "/api/notifications",
        ):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.client.get(endpoint).status_code, 200)


if __name__ == "__main__":
    unittest.main()
