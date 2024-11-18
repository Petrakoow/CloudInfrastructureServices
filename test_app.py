import pytest
from app import app, db, User


@pytest.fixture
def client():
	app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db:5432/flask_db'
	with app.test_client() as client:
		with app.app_context():
			db.create_all()
		yield client
		with app.app_context():
			db.session.remove()
			db.drop_all()


def test_cache(client):
	response1 = client.get('/data')
	response2 = client.get('/data')
	assert response1.data == response2.data


def test_404(client):
	response = client.get('/non_existing_route')
	assert response.status_code == 404


def test_create_user(client):
	data = {
		'username': 'Test User',
		'email': 'test_user@gmail.com'
	}
	response = client.post('/users', json=data)
	assert response.status_code == 200

	response_json = response.get_json()
	assert response_json['message'] == 'User created successfully'

	with app.app_context():
		user = User.query.filter_by(username='Test User').first()
		assert user is not None
		assert user.email == 'test_user@gmail.com'


def test_create_user_already_exist(client):
	data = {
		'username': 'Test User',
		'email': 'test_user@gmail.com'
	}
	response = client.post('/users', json=data)

	data_exist = {
		'username': 'Test User',
		'email': 'test_user@gmail.com'
	}
	response_exist = client.post('/users', json=data_exist)
	assert response_exist.status_code == 500


def test_get_all_users(client):
	data1 = {
		'username': 'Test User 1',
		'email': 'test_user_1@gmail.com'
	}
	data2 = {
		'username': 'Test User 2',
		'email': 'test_user_2@gmail.com'
	}
	client.post('/users', json=data1)
	client.post('/users', json=data2)

	response = client.get('/users')
	assert response.status_code == 200

	response_json = response.get_json()
	assert len(response_json) > 0

	usernames = [user['username'] for user in response_json]
	emails = [user['email'] for user in response_json]

	assert 'Test User 1' in usernames
	assert 'Test User 2' in usernames
	assert 'test_user_1@gmail.com' in emails
	assert 'test_user_2@gmail.com' in emails


def test_update_user_by_id(client):
	data = {
		'username': 'Test User',
		'email': 'test_user@gmail.com'
	}
	response = client.post('/users', json=data)
	assert response.status_code == 200

	response_json = response.get_json()
	user_id = response_json['id']
	
	new_data = {
		'username': 'New Test User',
		'email': 'new_test_user@gmail.com'
	}
	response = client.put(f'/users/{user_id}', json=new_data)
	assert response.status_code == 200

	response_json = response.get_json()
	assert response_json['message'] == 'User updated successfully'


def test_update_user_by_id_not_exists(client):
	data = {
		'username': 'Test User',
		'email': 'test_user@gmail.com'
	}
	response = client.put(f'/users/0', json=data)
	assert response.status_code == 404

	response_json = response.get_json()
	assert response_json['message'] == 'User not found'


def test_delete_user_by_id(client):
	data = {
		'username': 'Test User',
		'email': 'test_user@gmail.com'
	}
	response = client.post('/users', json=data)
	assert response.status_code == 200

	response_json = response.get_json()
	user_id = response_json['id']

	response = client.delete(f'/users/{user_id}')
	assert response.status_code == 200

	response_json = response.get_json()
	assert response_json['message'] == 'User deleted successfully'


def test_delete_user_by_id_not_exists(client):
	response = client.delete('/users/0')
	assert response.status_code == 404

	response_json = response.get_json()
	assert response_json['message'] == 'User not found'


def test_data_page(client):
	response = client.get('/data')
	assert response.status_code == 200
	assert b'This is some data!' in response.data


def test_get_user_with_cache(client):
	user_id = 1

	response = client.get(f'/user/{user_id}')
	assert response.status_code == 200
	response_json = response.get_json()
	assert response_json['id'] == user_id
	assert response_json['name'] == f'User {user_id}'

	response_cached = client.get(f'/user/{user_id}')
	assert response_cached.status_code == 200
	response_cached_json = response_cached.get_json()
	assert response_cached_json['id'] == user_id
	assert response_cached_json['name'] == f'User {user_id}'

	assert response.get_data() == response_cached.get_data()


def test_clear_user_cache(client):
	user_id = 1
	data = {
		'username': 'Test user',
		'email': 'test_user@gmail.com'
	}
	response_create_user = client.post('/users', json=data)
	assert response_create_user.status_code == 200
	response_create_user_json = response_create_user.get_json()
	assert response_create_user_json['id'] == user_id

	response = client.get(f'/user/{user_id}')
	assert response.status_code == 200
	response_json = response.get_json()
	assert response_json['id'] == user_id
	assert response_json['name'] == f'User {user_id}'

	response_clear_cache = client.get(f'/clear_cache/{user_id}')
	assert response_clear_cache.status_code == 200
	response_clear_cache_json = response_clear_cache.get_json()
	assert response_clear_cache_json['message'] == f'Cache for user {user_id} cleared'

	response_after_clear = client.get(f'/user/{user_id}')
	assert response_after_clear.status_code == 200
	response_after_clear_json = response_after_clear.get_json()
	assert response_after_clear_json['id'] == user_id
	assert response_after_clear_json['name'] == f'User {user_id}'


def test_home_page(client):
	response = client.get('/')
	assert response.status_code == 200
	assert b'Welcome' in response.data