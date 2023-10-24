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


@view_config(route_name='root', renderer='json')
def root(request):
    return {
        'message': 'Server Running!',
        'description': 'Hello World!'
    }


def auth_jwt_verify(request):
    authorization_header = request.cookies.get('token')
    if authorization_header:
        try:
            decoded_user = jwt.decode(
                authorization_header, 'secret', algorithms=['HS256'])
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
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
    }
    jwt_token = jwt.encode(payload, 'secret', algorithm='HS256')

    refresh_payload = {
        'sub': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
    }
    refresh_token = jwt.encode(
        refresh_payload, 'refresh_secret', algorithm='HS256')

    return jwt_token, refresh_token


@view_config(route_name='login', renderer='json')
def login(request):
    auth_user = auth_jwt_verify(request)
    if auth_user:
        return {
            'message': 'error',
            'description': 'Already logged in'
        }

    login = request.POST['login']
    password = request.POST['password']

    with connection.cursor() as cursor:
        sql = "SELECT id, username, password FROM users WHERE username=%s AND password=%s"
        cursor.execute(sql, (login, password))
        user = cursor.fetchone()

    if user:
        jwt_token, refresh_token = create_tokens(user['id'])
        with connection.cursor() as cursor:
            sql = "INSERT INTO tokens (user_id, refresh_token, jwt_token) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user['id'], refresh_token, jwt_token))
            connection.commit()
        request.response.set_cookie(
            'token', jwt_token, max_age=180, httponly=True)  # 3 minutes

        return {
            'message': 'ok',
            'token': jwt_token,
            'description': 'login success!'
        }
    else:
        return {
            'messeage': 'error',
            'description': 'login failed!'
        }


@view_config(route_name='hello', renderer="json")
def hello(request):
    auth_user = auth_jwt_verify(request)
    print(auth_user)
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


@view_config(route_name='logout', renderer='json')
def logout(request):
    auth_user = auth_jwt_verify(request)
    authorization_header = request.cookies.get('token')
    if auth_user:
        with connection.cursor() as cursor:
            sql = "DELETE FROM tokens WHERE jwt_token=%s"
            cursor.execute(sql, (authorization_header,))
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
        config.add_route('root', '/')
        config.add_route('login', '/login')
        config.add_route('logout', '/logout')
        config.add_route('hello', '/welcome')
        config.scan()
        config.set_authorization_policy(ACLAuthorizationPolicy())
        config.add_static_view(name='static', path='static')
        config.include('pyramid_jwt')
        config.set_jwt_authentication_policy(
            config.get_settings()['jwt.secret'])

        app = config.make_wsgi_app()
    # Menjalankan aplikasi pada server lokal
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()
