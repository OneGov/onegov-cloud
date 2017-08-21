
def login_admin(client):
    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def login_publisher(client):
    login = client.get('/auth/login')
    login.form['username'] = 'publisher@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def login_editor_1(client):
    login = client.get('/auth/login')
    login.form['username'] = 'editor1@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def login_editor_2(client):
    login = client.get('/auth/login')
    login.form['username'] = 'editor2@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def login_editor_3(client):
    login = client.get('/auth/login')
    login.form['username'] = 'editor3@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()
