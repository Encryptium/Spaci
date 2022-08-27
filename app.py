from flask import Flask, render_template, redirect, session, jsonify, request
from flask_socketio import SocketIO, emit, join_room, send
from werkzeug.security import generate_password_hash, check_password_hash
import firebase_admin
from firebase_admin import credentials, initialize_app, firestore
import os
import uuid
import json

cred = credentials.Certificate("firebase/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# initialize the database
db = firestore.client()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
socket = SocketIO(app)

@app.before_request
def make_session_permanent():
  session.permanent = True


# deticated function for getting workspace
def get_workspace(workspace_id):
	workspace = db.collection('workspaces').document(workspace_id).get()
	return workspace.to_dict()

def verify_module_config(workspace_id, module_id):
	workspace = get_workspace(workspace_id)
	spaci_config = workspace['config']

	if module_id not in spaci_config or spaci_config[module_id] is not True:
		return False

	return True

def get_all_user_workspaces(email):
	workspaces = []
	# select all workspaces with user email as collaborator
	workspace_ref = db.collection('workspaces').where('collaborators', 'array_contains', email).stream()
	for workspace in workspace_ref:
		workspaces.append(workspace.to_dict())
		
	return workspaces

def should_continue_to_workspace(workspace_id, email):
	if 'logged_in' not in session:
		return False

	workspace = get_workspace(workspace_id)
	if workspace['collaborators'].count(email) == 0:
		return False
	else:
		return True


@socket.on("join")
def handle_user_join(data):
	workspace = data['workspace']
	join_room(workspace)

@socket.on("message")
def broadcast_message(data):
	workspace = data['workspace'] # Get workspace id from json data

	# return if it's just spaces
	if data['message_data']['message'].isspace() or not len(data['message_data']['message']):
		return

	workspace_ref = db.collection('workspaces').document(workspace)
	workspace_ref.update({
		"chat": firestore.ArrayUnion(
			[
				{
					"sender": data['message_data']['sender'],
					"message": data['message_data']['message']
				}
			]
		)
	})

	send(data['message_data'], to=workspace) # broadcast the data.message_data part to everyone
	

@app.route('/')
def index():
	if 'logged_in' not in session:
		return render_template('index.html')

	if len(get_all_user_workspaces(session['email'])) == 0:
		return redirect("/new")
	else:
		if 'workspace_id' not in session:
			session['workspace_id'] = get_all_user_workspaces(session['email'])[0]['id']
		else:
			return redirect(f"/workspaces/{session['workspace_id']}")

	return redirect('/')
			

@app.route('/new', methods=['GET', 'POST'])
def create_workspace():
	if 'logged_in' not in session:
		return redirect('/')

	"""
	Create a new project
	"""
	if request.method == 'GET':
		# workspace_name = request.form['workspace_name']
		# workspace_description = request.form['workspace_description']
		# workspace_id = str(uuid.uuid4())

		workspace_name = "Untitled"
		workspace_description = ""
		workspace_id = str(uuid.uuid4())

		# create a new project
		workspace_ref = db.collection('workspaces').document(workspace_id)
		workspace_ref.set({
			'name': workspace_name,
			'description': workspace_description,
			'id': workspace_id,
			'collaborators': [session['email']],
			'tasks': [],
			'chat': [
				{
					"name": "Spaci Messenger",
					"message": "This is the start of your chat!"
				}
			],
			'config': {"adding_modules_enabled": False, "chat_enabled": True, "planning_enabled": True, "sharing_enabled": True, "tasks_enabled": True}
		})

		return redirect(f'/workspaces/{workspace_id}/chat')

	return redirect('/')


@app.route('/workspaces')
def workspaces():
	return redirect('/')

# @app.route('/workspaces')
# def workspaces():
# 	if 'logged_in' not in session:
# 		return redirect('/')

# 	"""
# 	Get all workspaces with user email as collaborator
# 	"""
# 	workspaces = []
# 	user_email = session['email']
# 	# select all workspaces with user email as collaborator
# 	workspace_ref = db.collection('workspaces').where('collaborators', 'array_contains', user_email).stream()
# 	for workspace in workspace_ref:
# 		workspaces.append(workspace.to_dict())

# 	return render_template('workspaces.html', workspaces=workspaces)


# workspace pages
@app.route('/workspaces/<workspace_id>')
def workspace(workspace_id):
	if not should_continue_to_workspace(workspace_id, session['email']):
		return render_template('access_denied.html', workspace=get_workspace(workspace_id))

	session['workspace_id'] = workspace_id
	# redirect to chat if not logged in
	return redirect(f'/workspaces/{workspace_id}/chat')


@app.route('/workspaces/<workspace_id>/chat')
def chat(workspace_id):
	if not should_continue_to_workspace(workspace_id, session['email']):
		return render_template('access_denied.html', workspace=get_workspace(workspace_id))

	if not verify_module_config(workspace_id, "chat_enabled"):
		return render_template('module_not_configured.html', workspace=get_workspace(workspace_id)) 

	session['workspace_id'] = workspace_id


	return render_template('chat.html', workspace=get_workspace(workspace_id), workspaces=get_all_user_workspaces(session['email']))


@app.route('/workspaces/<workspace_id>/plan')
def plan(workspace_id):
	if not should_continue_to_workspace(workspace_id, session['email']):
		return render_template('access_denied.html', workspace=get_workspace(workspace_id))

	if not verify_module_config(workspace_id, "planning_enabled"):
		return render_template('module_not_configured.html', workspace=get_workspace(workspace_id)) 

	session['workspace_id'] = workspace_id


	return render_template('plan.html', workspace=get_workspace(workspace_id), workspaces=get_all_user_workspaces(session['email']))


@app.route('/workspaces/<workspace_id>/tasks')
def tasks(workspace_id):
	if not should_continue_to_workspace(workspace_id, session['email']):
		return render_template('access_denied.html', workspace=get_workspace(workspace_id))

	if not verify_module_config(workspace_id, "tasks_enabled"):
		return render_template('module_not_configured.html', workspace=get_workspace(workspace_id)) 

	session['workspace_id'] = workspace_id

	
	return render_template('tasks.html', workspace=get_workspace(workspace_id), workspaces=get_all_user_workspaces(session['email']))

@app.route('/workspaces/<workspace_id>/share', methods=['GET', 'POST'])
def share(workspace_id):
	if not should_continue_to_workspace(workspace_id, session['email']):
		return render_template('access_denied.html', workspace=get_workspace(workspace_id))

	if not verify_module_config(workspace_id, "sharing_enabled"):
		return render_template('module_not_configured.html', workspace=get_workspace(workspace_id)) 

	session['workspace_id'] = workspace_id

	"""
	Share a workspace with another user
	"""
	workspace_ref = db.collection('workspaces').document(workspace_id)
	collaborators = workspace_ref.get().to_dict()['collaborators']

	return render_template('share.html', workspace=get_workspace(workspace_id), workspaces=get_all_user_workspaces(session['email']), collaborators=collaborators)

	if request.method == 'POST':
		email = request.form['email']
		# add user to collaborators
		workspace_ref.update({
			'collaborators': firestore.ArrayUnion([email])
		})

		return redirect(f'/{workspace_id}/chat')

	return redirect('/')

@app.route('/workspaces/<workspace_id>/settings', methods=['GET', 'POST'])
def settings(workspace_id):

	if request.method == 'POST':
		workspace_name = request.form.get('name')

		try:
			spaci_config = json.loads(request.form.get('spaci-config'))
		except:
			return redirect('settings')

		workspace_ref = db.collection('workspaces').document(workspace_id)
		workspace_ref.update({
			'name': workspace_name,
			'config': spaci_config
		})
	
	return render_template('settings.html', workspace=get_workspace(workspace_id), workspaces=get_all_user_workspaces(session['email']))

@app.route('/delete-workspace')
def delete_workspace():
	workspace_id = request.args.get('workspace_id')

	db.collection('workspaces').document(workspace_id).delete()
	session.pop('workspace_id', None)

	return redirect('/')

# login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if 'logged_in' in session:
		return redirect('/')

	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		user = db.collection('users').where('email', '==', email).get()
		for doc in user:
			if check_password_hash(doc.to_dict()['password'], password):
				session['email'] = doc.to_dict()['email']
				session['logged_in'] = True
				return redirect('/')
		return redirect('/login')

	return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
	if 'logged_in' in session:
		return redirect('/')

	if request.method == 'POST':
		email = request.form['email']

		# If passwords match, encrypt password
		if request.form['password'] == request.form['password_confirmation']:
			password = generate_password_hash(request.form['password'])
		else:
			return redirect('/register')

		# Store new user in db
		user = db.collection('users').where('email', '==', email).get()
		for doc in user:
			return redirect('/register')
		user = db.collection('users').add({
			'email': email,
			'password': password
		})

		# login
		session['email'] = email
		session['logged_in'] = True
		return redirect('/login')

	return render_template('register.html')

# logout
@app.route('/logout')
def logout():
	session.clear()
	return redirect('/')


# APIs
@app.route('/api/v1/chat')
def past_chat_messages():
	workspace_id = request.args.get("id")

	if not should_continue_to_workspace(workspace_id, session['email']):
		return jsonify({})
		
	# get last 10 chat messages
	chat_messages = db.collection('workspaces').document(workspace_id).get().to_dict()['chat'][-25:]
	return jsonify(chat_messages)

@app.route('/api/v1/email')
def return_user_email():
	if 'logged_in' not in session:
		return jsonify({"email": None})
	return jsonify({"email": session['email']})

@app.route('/api/v1/invite', methods=['POST'])
def invite():
	email = request.form.get("email")
	workspace_id = session['workspace_id']

	if not should_continue_to_workspace(workspace_id, session['email']):
		return jsonify({"success": False})
		
	# add user to collaborators
	workspace_ref = db.collection('workspaces').document(workspace_id)
	workspace_ref.update({
		'collaborators': firestore.ArrayUnion([email])
	})

	return jsonify({"success": True})

# remove collaborator
@app.route('/api/v1/remove-collaborator', methods=['POST'])
def remove_collaborator():
	email = request.get_json()['collaboratorId']
	workspace_id = session['workspace_id']

	if not should_continue_to_workspace(workspace_id, session['email']):
		return jsonify({"success": False})
		
	# add user to collaborators
	workspace_ref = db.collection('workspaces').document(workspace_id)
	workspace_ref.update({
		'collaborators': firestore.ArrayRemove([email])
	})

	return jsonify({"success": True})


@app.route('/api/v1/complete-task')
def complete_task():
	task_index = int(request.args.get('task_index'))
	workspace_id = session['workspace_id']

	if not should_continue_to_workspace(workspace_id, session['email']):
		return jsonify({"success": False})

	tasks = get_workspace(workspace_id)['tasks']
	del tasks[task_index]
	print(tasks)

	workspace_ref = db.collection('workspaces').document(workspace_id)
	workspace_ref.update({
		'tasks': tasks
	})
	return jsonify({'success': True})

@app.route('/api/v1/add-task', methods=['POST'])
def add_task():
	title = request.form.get('title')
	description = request.form.get('description')
	workspace_id = session['workspace_id']

	if not should_continue_to_workspace(workspace_id, session['email']):
		return jsonify({"success": False})

	workspace_ref = db.collection('workspaces').document(workspace_id)
	workspace_ref.update({
		'tasks': firestore.ArrayUnion([{"title": title, "description": description}])
	})

	return jsonify({"success": True})


if __name__ == '__main__':
  socket.run(app, host="0.0.0.0", port=8080, debug=True)
