
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


def login_editor(client):
    login = client.get('/auth/login')
    login.form['username'] = 'editor@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()
