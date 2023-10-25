from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.authorization import ACLAuthorizationPolicy
import pymysql
import jwt
import datetime

# Koneksi ke database MySQL
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    db='pyramid-themovies',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)


@view_config(route_name='root', renderer='json',  request_method="GET")
def root(request):
    return {
        'message': 'Server Running!',
        'description': 'Hello World!'
    }


# middleware auth
def auth_jwt_verify(request):
    authentication_header = request.cookies.get('token')
    if authentication_header:
        try:
            decoded_user = jwt.decode(
                authentication_header, 'secret', algorithms=['HS256'])
            with connection.cursor() as cursor:
                sql = "SELECT jwt_token FROM tokens WHERE user_id=%s"
                cursor.execute(sql, (decoded_user['sub'],))
                result = cursor.fetchone()
            if result:
                return decoded_user
        except jwt.ExpiredSignatureError:
            request.response.status = 401  # Unauthorized
    return None


# Fungsi untuk membuat token baru dan refresh token
def create_tokens(user_id):
    payload = {
        'sub': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }
    jwt_token = jwt.encode(payload, 'secret', algorithm='HS256')

    refresh_payload = {
        'sub': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    refresh_token = jwt.encode(
        refresh_payload, 'refresh_secret', algorithm='HS256')

    return jwt_token, refresh_token


# fungsi endpoint login
@view_config(route_name='login', renderer='json',  request_method="POST")
def login(request):
    auth_user = auth_jwt_verify(request)
    if auth_user:
        return {
            'message': 'error',
            'description': 'Already logged in'
        }

    username = request.POST['username']
    password = request.POST['password']

    with connection.cursor() as cursor:
        sql = "SELECT id, username, password FROM users WHERE username=%s AND password=%s"
        cursor.execute(sql, (username, password))
        user = cursor.fetchone()

    if user:
        jwt_token, refresh_token = create_tokens(user['id'])
        with connection.cursor() as cursor:
            sql = "INSERT INTO tokens (user_id, refresh_token, jwt_token) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user['id'], refresh_token, jwt_token))
            connection.commit()
        request.response.set_cookie(
            'token', jwt_token, max_age=1800, httponly=True)  # 30 minutes

        return {
            'message': 'ok',
            'token': jwt_token,
            'description': 'login success!'
        }
    else:
        return {
            'message': 'error',
            'description': 'login failed!'
        }


# fungsi endpoint register
@view_config(route_name='registrasi', renderer="json", request_method="POST")
def register(request):
    username = request.POST['username']
    password = request.POST['password']
    if username == "" or password == "":
        return {'message': 'error', 'description': 'Username atau password tidak boleh kosong!'}
    else:
        with connection.cursor() as cursor:
            sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
            cursor.execute(sql, (username, password))
            connection.commit()
            if sql:
                return {
                    'message': 'ok',
                    'username': username,
                    'description': 'Registrasi Berhasil'
                }
            else:
                return {
                    'message': 'error',
                    'description': 'registrasi failed'
                }


# fungsi endpoint home/ Read Data
@view_config(route_name='home', renderer="json", request_method="GET")
def home(request):
    auth_user = auth_jwt_verify(request)
    if auth_user:
        # show from table movies
        with connection.cursor() as cursor:
            sql = "SELECT id,judul,tahun,director,genre FROM movies WHERE user_id=%s"
            cursor.execute(sql, (auth_user['sub'],))
            result = cursor.fetchall()

        data = {}
        for item in result:
            data[item['id']] = {
                'id': item['id'],
                'judul': item['judul'],
                'genre': item['genre'],
                'tahun': item['tahun'],
                'director': item['director'],
            }
        return {
            'message': 'ok',
            'description': 'Get data success!',
            'data': data
        }
    else:
        request.response.status = 401  # Unauthorized
        return {'message': 'Unauthorized', 'description': 'token not found'}


# fungsi endpoint creat data
@view_config(route_name='create-data', request_method='POST', renderer="json")
def movie_create(request):
    # create data movies
    auth_user = auth_jwt_verify(request)
    if auth_user:
        with connection.cursor() as cursor:
            sql = "INSERT INTO movies (judul, genre, tahun, director, user_id) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (request.POST['judul'], request.POST['genre'],
                           request.POST['tahun'], request.POST['director'], auth_user['sub'],))
            connection.commit()
        return {'message': 'ok', 'description': 'berhasil buat data', 'data': [request.POST['judul'], request.POST['genre'], request.POST['tahun'], request.POST['director']]}
    else:
        request.response.status = 401
        return {'message': 'Unauthorized', 'description': 'token not found'}


# fungsi endpoint update-data
@view_config(route_name='update-data', request_method='PUT', renderer="json")
def movie_update(request):
    # update data movies
    auth_user = auth_jwt_verify(request)
    if auth_user:
        with connection.cursor() as cursor:
            sql = "UPDATE movies SET judul=%s, genre=%s, tahun=%s, director=%s, user_id=%s WHERE id=%s"
            cursor.execute(sql, (request.POST['judul'], request.POST['genre'],
                           request.POST['tahun'], request.POST['director'],  auth_user['sub'], request.POST['id']))
            connection.commit()
        return {'message': 'ok', 'description': 'berhasil perbarui data', 'data': [request.POST['judul'], request.POST['genre'], request.POST['tahun'], request.POST['director'],]}
    else:
        request.response.status = 401
        return {'message': 'Unauthorized', 'description': 'token not found'}


# fungsi endpoint delete data
@view_config(route_name='delete-data', request_method='DELETE', renderer="json")
def movie_delete(request):
    # delete data movies
    auth_user = auth_jwt_verify(request)
    if auth_user:
        with connection.cursor() as cursor:
            sql = "SELECT id,judul,tahun,director,genre FROM movies WHERE user_id=%s"
            cursor.execute(sql, (auth_user['sub'],))
            result = cursor.fetchall()
            data = {}
            for item in result:
                data = {
                    'id': item['id'],
                    'judul': item['judul'],
                    'genre': item['genre'],
                    'tahun': item['tahun'],
                    'director': item['director'],
                }
            sql = "DELETE FROM movies WHERE id=%s"
            cursor.execute(sql, (request.POST['id']))
            connection.commit()
        return {'message': 'ok', 'description': 'hapus data berhasil', 'data': data}
    else:
        request.response.status = 401
        return {'message': 'Unauthorized', 'description': 'token not found'}


# fungsi endpoint logout
@view_config(route_name='logout', renderer='json', request_method="DELETE")
def logout(request):
    auth_user = auth_jwt_verify(request)
    authentication_header = request.cookies.get('token')
    if auth_user:
        with connection.cursor() as cursor:
            sql = "DELETE FROM tokens WHERE jwt_token=%s"
            cursor.execute(sql, (authentication_header))
            connection.commit()

        request.response.delete_cookie('token')
        return {
            'message': 'ok',
            'description': 'Successfully logged out'
        }
    return {
        'message': 'error',
        'description': 'Token not found'
    }


if __name__ == "__main__":
    with Configurator() as config:
        config = Configurator(settings={'jwt.secret': 'secret'})
        # konfigurasi endpoint
        config.add_route('root', '/')
        config.add_route('registrasi', '/register')
        config.add_route('login', '/login')
        config.add_route('logout', '/logout')
        config.add_route('home', '/home')
        config.add_route('create-data', '/create')
        config.add_route('update-data', '/update')
        config.add_route('delete-data', '/delete')
        config.scan()
        app = config.make_wsgi_app()
    # Menjalankan aplikasi pada server lokal
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()
