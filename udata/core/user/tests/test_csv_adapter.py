import pytest

from udata.core.user.factories import UserFactory
from udata.core.user.csv import UserCsvAdapter


class UserCsvTest:
    def test_user_csv_adapter(self):
        user = UserFactory(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            website='https://example.com',
            about='Test user'
        )

        adapter = UserCsvAdapter([user])
        header = adapter.header()
        rows = list(adapter.rows())
        
        assert len(rows) == 1
        
        # Check presence of main fields
        assert 'id' in header
        assert 'first_name' in header
        assert 'last_name' in header
        assert 'email' in header
        assert 'website' in header
        assert 'about' in header
        assert 'active' in header
        
        # Check that row contains expected data
        row = rows[0]
        id_idx = header.index('id')
        first_name_idx = header.index('first_name')
        last_name_idx = header.index('last_name')
        email_idx = header.index('email')
        website_idx = header.index('website')
        
        assert str(user.id) == row[id_idx]
        assert 'John' == row[first_name_idx]
        assert 'Doe' == row[last_name_idx]
        assert 'john.doe@example.com' == row[email_idx]
        assert 'https://example.com' == row[website_idx] 