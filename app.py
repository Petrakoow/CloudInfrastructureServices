from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache

import os


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI']='postgresql://user:password@db:5432/flask_db'
app.config['SQLACHEMY_TRACK_MODIFICATIONS']=False

app.config['CACHE_TYPE']='redis'
app.config['CACHE_REDIS_HOST']=os.getenv('REDIS_HOST', 'localhost')
app.config['CACHE_REDIS_PORT']=6379
app.config['CACHE_REDIS_DB']=0
app.config['CACHE_REDIS_URL']=f"redis://{app.config['CACHE_REDIS_HOST']}:{app.config['CACHE_REDIS_PORT']}/0"

db = SQLAlchemy(app)
migrate = Migrate(app, db)
cache = Cache(app)


class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	def __repr__(self):
		return f'<User {self.username}>'


# CRUD операции

# Создание нового пользователя
@app.route('/users', methods=['POST'])
def create_user():
	data = request.get_json()
	new_user = User(username=data['username'], email=data['email'])
	db.session.add(new_user)
	db.session.commit()
	return jsonify({'message': 'User created successfully', 'id': new_user.id}), 200

# Получение списка всех пользователей
@app.route('/users', methods=['GET'])
@cache.cached(timeout=60)
def get_users():
	users = User.query.all()
	users_list = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
	return jsonify(users_list)


# Обновление пользователя по id
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
	user = User.query.get(id)
	data = request.get_json()
	if not user:
		return jsonify({'message': 'User not found'}), 404
	user.username = data.get('username', user.username)
	user.email = data.get('email', user.email)
	db.session.commit()
	return jsonify({'message': 'User updated successfully'})


# Удаление пользователя по id
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
	user = User.query.get(id)
	if not user:
		return jsonify({'message': 'User not found'}), 404
	db.session.delete(user)
	db.session.commit()
	return jsonify({'message': 'User deleted successfully'})


# Кэширование данных

# Тестовое кэширование данных
@app.route('/data')
@cache.cached(timeout=60)
def get_data():
	return jsonify({'data': 'This is some data!'})


# Получение данных об определенном пользователе и кэширование их по ключу 'user_data'
@app.route('/user/<int:id>')
@cache.cached(timeout=120, key_prefix='user_data')
def get_user(id):
	user_data = {'id': id, 'name': f'User {id}'}
	return jsonify(user_data)


# Очистка кэша для определенного пользователя
@app.route('/clear_cache/<int:id>')
def clear_user_cache(id):
	cache.delete(f'user_data::{id}')
	return jsonify({'message': f'Cache for user {id} cleared'})


# Страницы приложения

# Главная страница
@app.route('/')
def home_page():
	return jsonify({'message': 'Welcome to main page'})


if __name__ == '__main__':
	app.run(host='0.0.0.0')
