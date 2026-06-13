from __future__ import annotations

import unittest

from claude_auth.session import session_name_for_email


class SessionTests(unittest.TestCase):
    def test_session_name_is_stable_and_email_case_insensitive(self) -> None:
        first = session_name_for_email("User@Example.com")
        second = session_name_for_email(" user@example.COM ")

        self.assertEqual(first, second)
        self.assertRegex(first, r"^claude-auth-[0-9a-f]{16}$")


if __name__ == "__main__":
    unittest.main()
