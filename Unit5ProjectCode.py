import wsgiref.simple_server
import urllib.parse
import sqlite3
import http.cookies
import random

connection = sqlite3.connect('users.db')
stmt = "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
cursor = connection.cursor()
result = cursor.execute(stmt)
r = result.fetchall()
if (r == []):
    exp = 'CREATE TABLE users (username,password)'
    connection.execute(exp)
outcome=''


def application(environ, start_response):
    headers = [('Content-Type', 'text/html; charset=utf-8')]

    path = environ['PATH_INFO']
    params = urllib.parse.parse_qs(environ['QUERY_STRING'])
    un = params['username'][0] if 'username' in params else None
    pw = params['password'][0] if 'password' in params else None

    if path == '/register' and un and pw:
        user = cursor.execute('SELECT * FROM users WHERE username = ?', [un]).fetchall()
        if user:
            start_response('200 OK', headers)
            return ['Sorry, username {} is taken'.format(un).encode()]
        else:
            cursor.execute('INSERT INTO users VALUES (?, ?)', [un, pw])
            connection.commit()
            start_response('200 OK', headers)
            return ['User {} was created successfully. <a href="/account">Account</a>'.format(un).encode()]

    elif path == '/login' and un and pw:
        user = cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', [un, pw]).fetchall()

        if user:
            headers.append(('Set-Cookie', 'session={}:{}'.format(un, pw)))
            start_response('200 OK', headers)
            return ['User {} successfully logged in. <a href="/account">Account</a>'.format(un).encode()]
        else:
            start_response('200 OK', headers)
            return ['Incorrect username or password'.encode()]

    elif path == '/logout':
        headers.append(('Set-Cookie', 'session=0; expires=Thu, 01 Jan 1970 00:00:00 GMT'))
        start_response('200 OK', headers)
        return ['Logged out. <a href="/">Login</a>'.encode()]

    elif path == '/account':
        start_response('200 OK', headers)
        if 'HTTP_COOKIE' not in environ:
            return ['Not logged in <a href="/">Login</a>'.encode()]

        cookies = http.cookies.SimpleCookie()
        cookies.load(environ['HTTP_COOKIE'])
        if 'session' not in cookies:
            return ['Not logged in <a href="/">Login</a>'.encode()]

        [un, pw] = cookies['session'].value.split(':')
        user = cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', [un, pw]).fetchall()


        if user:
            correct = 0
            wrong = 0
            cookies = http.cookies.SimpleCookie()
            if 'HTTP_COOKIE' in environ:
                headers.append(('Set-Cookie', 'score={}:{}'.format(correct, wrong)))
                cookies.load(environ['HTTP_COOKIE'])

            page = '<!DOCTYPE html><html><head><title>Multiply with Score</title></head><body>'
            if 'factor1' in params and 'factor2' in params and 'answer' in params:
                factor1 = params['factor1'][0] if 'factor1' in params else None
                factor2 = params['factor2'][0] if 'factor2' in params else None
                answer = params['answer'][0] if 'answer' in params else None

                if int(factor1) * int(factor2) == int(answer):
                    if 'score' in cookies:
                        correct = int(cookies['score'].value.split(':')[0])
                        wrong = int(cookies['score'].value.split(':')[1])

                    correct = correct + 1
                    wrong = wrong + 0
                    page += '''<h2> <p style="background-color: lightgreen">Correct, {} X {} = {}</p>'''.format(factor1, factor2, answer)
                elif int(factor1) * int(factor2) != int(answer):
                    if 'score' in cookies:
                        wrong = int(cookies['score'].value.split(':')[1])
                        correct = int(cookies['score'].value.split(':')[0])
                    wrong = wrong + 1
                    correct = correct + 0
                    page += '''<h2> <p style="background-color: red"> Wrong, {} X {} = {}</p>'''.format(factor1,factor2,answer)
                elif 'reset' in params:
                    correct = 0
                    wrong = 0

                headers.append(('Set-Cookie', 'score={}:{}'.format(correct, wrong)))


            f1 = random.randrange(10) + 1
            f2 = random.randrange(10) + 1

            page = page + '<h1>What is {} x {}</h1>'.format(f1, f2)
            answer = [ f1*f2, f1+f2*2*2 , f1+f2 ,abs(f1-f2+3)]
            random.shuffle(answer)

            page += '''<h2> A: <a href="/account?factor1={}&amp;factor2={}&amp;answer={}">{}</a><br>'''.format(f1,f2,answer[0], answer[0])
            page += '''<h2> B: <a href="/account?factor1={}&amp;factor2={}&amp;answer={}">{}</a><br>'''.format(f1, f2,answer[1] , answer[1])
            page += '''<h2> C: <a href="/account?factor1={}&amp;factor2={}&amp;answer={}">{}</a><br>'''.format(f1, f2,answer[2], answer[2])
            page += '''<h2> D: <a href="/account?factor1={}&amp;factor2={}&amp;answer={}">{}</a><br>'''.format(f1, f2,answer[3], answer[3])

            page += '''<h2>Score</h2>
                   Correct: {}<br>
                   Wrong: {}<br>
                   <a href="/account?reset=true">Reset</a>
                   </body></html>'''.format(correct, wrong)

            return [page.encode()]
        else:
            return ['Not logged in. <a href="/">Login</a>'.encode()]
    elif path == '/':
        page = '''<!DOCTYPE html>
                <html>
                <head><title>User Form</title></head>
                <body>
                <form action="/login" style="background-color:gold">
                <h1>Login</h1>
                Username <input type="text" name="username"><br>
                Password <input type="password" name="password"><br>
                <input type="submit" value="Log in">
                </form>
                <form action="/register" style="background-color:gold">
                <h1>Register</h1>
                Username <input type="text" name="username"><br>
                Password <input type="password" name="password"><br>
                <input type="submit" value="Register">
                </form>
                </body><html>'''.format(environ['QUERY_STRING'] )

        start_response('200 OK', headers)
        return [page.encode()]

    else:
        start_response('404 Not Found', headers)
        return ['Status 404: Resource not found'.encode()]


httpd = wsgiref.simple_server.make_server('', 8000, application)
httpd.serve_forever()
