import pytest
from flask import url_for

from udata.core.user.factories import UserFactory
from udata.tests.api import APITestCase


class UsersCsvExportAPITest(APITestCase):
    modules = []

    def test_csv_export_no_api_key(self):
        """Should return 401 when no API key is provided"""
        response = self.get(url_for("api.users_csv_export"))
        self.assert401(response)

    def test_csv_export_invalid_api_key(self):
        """Should return 401 when invalid API key is provided"""
        response = self.get(
            url_for("api.users_csv_export"),
            headers={"X-API-KEY": "invalid-key"}
        )
        self.assert401(response)

    def test_csv_export_with_query_param_invalid(self):
        """Should return 401 when invalid API key is provided via query param"""
        response = self.get(url_for("api.users_csv_export", **{"api-key": "invalid-key"}))
        self.assert401(response)

    @pytest.mark.options(CSV_EXPORT_API_KEY=None)
    def test_csv_export_no_configured_key(self):
        """Should return 503 when CSV_EXPORT_API_KEY is not configured"""
        response = self.get(
            url_for("api.users_csv_export"),
            headers={"X-API-KEY": "some-key"}
        )
        self.assert503(response)

    @pytest.mark.options(CSV_EXPORT_API_KEY="test-api-key-12345")
    def test_csv_export_success_header(self):
        """Should return CSV when valid API key is provided via header"""
        # Create some test users
        active_user = UserFactory(active=True)
        inactive_user = UserFactory(active=False)
        deleted_user = UserFactory(active=True)
        deleted_user.mark_as_deleted()

        response = self.get(
            url_for("api.users_csv_export"),
            headers={"X-API-KEY": "test-api-key-12345"}
        )
        
        self.assert200(response)
        self.assertEqual(response.content_type, "text/csv; charset=utf-8")
        
        # Check CSV content contains only active users
        csv_content = response.data.decode('utf-8')
        lines = csv_content.strip().split('\n')
        
        # Should have header + active users (active_user + any existing active users from other tests)
        self.assertTrue(len(lines) >= 2)  # At least header + 1 active user
        
        # Check that the CSV contains our active user ID
        self.assertIn(str(active_user.id), csv_content)
        # Check that inactive and deleted users are not included
        self.assertNotIn(str(inactive_user.id), csv_content)
        self.assertNotIn(str(deleted_user.id), csv_content)

    @pytest.mark.options(CSV_EXPORT_API_KEY="test-api-key-12345")
    def test_csv_export_success_query_param(self):
        """Should return CSV when valid API key is provided via query parameter"""
        active_user = UserFactory(active=True)
        
        response = self.get(url_for("api.users_csv_export", **{"api-key": "test-api-key-12345"}))
        
        self.assert200(response)
        self.assertEqual(response.content_type, "text/csv; charset=utf-8")
        
        # Check that the CSV contains our active user
        csv_content = response.data.decode('utf-8')
        self.assertIn(str(active_user.id), csv_content)

    @pytest.mark.options(CSV_EXPORT_API_KEY="test-api-key-12345")
    def test_csv_export_headers(self):
        """Should return proper CSV headers and filename"""
        response = self.get(
            url_for("api.users_csv_export"),
            headers={"X-API-KEY": "test-api-key-12345"}
        )
        
        self.assert200(response)
        self.assertEqual(response.content_type, "text/csv; charset=utf-8")
        
        # Check Content-Disposition header for proper filename
        content_disposition = response.headers.get('Content-Disposition')
        self.assertIsNotNone(content_disposition)
        self.assertIn('attachment', content_disposition)
        self.assertIn('active-users', content_disposition)
        self.assertIn('.csv', content_disposition) 