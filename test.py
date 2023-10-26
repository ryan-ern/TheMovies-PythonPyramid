import unittest
from pyramid import testing
from app import index, login, logout, register, home, movie_create, movie_update, movie_delete


class TestAppViews(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    # index
    def test_index_view(self):
        request = testing.DummyRequest()
        response = index(request)
        self.assertEqual(response['message'], 'Server Running!')
        self.assertEqual(response['description'], 'Hello World!')

    # login berhasil
    def test_login_view_success(self):
        request = testing.DummyRequest(
            post={'username': 'user1', 'password': 'user1'})
        response = login(request)
        self.assertEqual(response['message'], 'ok')
        self.assertIn('token', response)
        self.assertEqual(response['description'], 'login success!')

    # login gagal
    def test_login_view_failed(self):
        request = testing.DummyRequest(
            post={'username': 'xxx', 'password': 'xxx'})
        response = login(request)
        self.assertEqual(response['message'], 'error')
        self.assertEqual(response['description'], 'login failed!')

    # logout
    def test_logout_view(self):
        request = testing.DummyRequest(cookies={
                                       'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEwLCJleHAiOjE2OTgyOTY2MTB9.cIWcBFZuko2ZC1Uqoakj0jM4y8BLtHhTnh4Z2yVsrG8'})
        response = logout(request)
        self.assertEqual(response['message'], 'ok')
        self.assertEqual(response['description'], 'Successfully logged out')

    # Register Berhasil
    def test_register_view_success(self):
        request = testing.DummyRequest(
            post={'username': 'testuser', 'password': 'testpassword'})
        response = register(request)
        self.assertEqual(response['message'], 'ok')
        self.assertEqual(response['username'], 'testuser')
        self.assertEqual(response['description'], 'Registrasi Berhasil')

    # Register gagal
    def test_register_view_empty_fields(self):
        from app import register
        request = testing.DummyRequest(
            post={'username': '', 'password': ''})
        response = register(request)
        self.assertEqual(response['message'], 'error')
        self.assertEqual(response['description'],
                         'Username atau password tidak boleh kosong!')

    # Home dengan auth
    def test_home_view_authenticated(self):
        request = testing.DummyRequest()
        request.cookies['token'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEwLCJleHAiOjE2OTgyOTY2MTB9.cIWcBFZuko2ZC1Uqoakj0jM4y8BLtHhTnh4Z2yVsrG8'
        response = home(request)
        self.assertEqual(response['message'], 'ok')
        self.assertEqual(response['description'], 'Get data success!')
        self.assertIn('data', response)

    # Home tanpa auth
    def test_home_view_unauthenticated(self):
        request = testing.DummyRequest()
        response = home(request)
        self.assertEqual(response['message'], 'Unauthorized')
        self.assertEqual(response['description'], 'token not found')
        self.assertEqual(request.response.status_code, 401)

    # create data dengan auth
    def test_movie_create_view_authenticated(self):
        request = testing.DummyRequest(
            post={'judul': 'Test Movie', 'genre': 'Action', 'tahun': '2023', 'director': 'Director Name'})
        request.cookies['token'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEwLCJleHAiOjE2OTgyOTY2MTB9.cIWcBFZuko2ZC1Uqoakj0jM4y8BLtHhTnh4Z2yVsrG8'
        response = movie_create(request)
        self.assertEqual(response['message'], 'ok')
        self.assertEqual(response['description'], 'berhasil buat data')
        self.assertIn('data', response)

    # update data dengan auth
    def test_movie_update_view_authenticated(self):
        request = testing.DummyRequest(
            post={'id': '1', 'judul': 'Updated Movie', 'genre': 'Sci-Fi', 'tahun': '2022', 'director': 'New Director Name'})
        request.cookies['token'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEwLCJleHAiOjE2OTgyOTY2MTB9.cIWcBFZuko2ZC1Uqoakj0jM4y8BLtHhTnh4Z2yVsrG8'
        response = movie_update(request)
        self.assertEqual(response['message'], 'ok')
        self.assertEqual(response['description'], 'berhasil perbarui data')
        self.assertIn('data', response)

    # delete data dengan auth
    def test_movie_delete_view_authenticated(self):
        request = testing.DummyRequest(
            post={'id': '1'})
        request.cookies['token'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEwLCJleHAiOjE2OTgyOTY2MTB9.cIWcBFZuko2ZC1Uqoakj0jM4y8BLtHhTnh4Z2yVsrG8'
        response = movie_delete(request)
        self.assertEqual(response['message'], 'ok')
        self.assertEqual(response['description'], 'hapus data berhasil')
        self.assertIn('data', response)

    def test_movie_delete_view_unauthenticated(self):
        request = testing.DummyRequest(
            post={'id': '1'})
        response = movie_delete(request)
        self.assertEqual(response['message'], 'Unauthorized')
        self.assertEqual(response['description'], 'token not found')
        self.assertEqual(request.response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
