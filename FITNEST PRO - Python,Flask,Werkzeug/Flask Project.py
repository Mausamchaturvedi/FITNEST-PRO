from flask import Flask, request, redirect, session, render_template_string, flash, jsonify
import sqlite3, os, json
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app=Flask(__name__)
app.secret_key=os.environ.get('FITNEST_SECRET','change-me-in-production')
DB='fitnest_pro.db'

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
    c=conn()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT,age INTEGER,height REAL,weight REAL,goal TEXT,activity TEXT,role TEXT DEFAULT 'user');
    CREATE TABLE IF NOT EXISTS weight_logs(id INTEGER PRIMARY KEY,user_id INTEGER,weight REAL,note TEXT,logged TEXT);
    CREATE TABLE IF NOT EXISTS workouts(id INTEGER PRIMARY KEY,user_id INTEGER,category TEXT,exercise TEXT,sets INTEGER,reps TEXT,logged TEXT);
    CREATE TABLE IF NOT EXISTS meals(id INTEGER PRIMARY KEY,user_id INTEGER,meal_type TEXT,food TEXT,calories INTEGER,protein REAL,carbs REAL,fats REAL,logged TEXT);
    CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY,user_id INTEGER,title TEXT,target REAL,current REAL DEFAULT 0,unit TEXT,due TEXT,status TEXT DEFAULT 'Active');
    CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY,user_id INTEGER,title TEXT,kind TEXT,when_at TEXT,done INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS water_logs(id INTEGER PRIMARY KEY,user_id INTEGER,amount_ml INTEGER,logged TEXT);
    CREATE TABLE IF NOT EXISTS body_measurements(id INTEGER PRIMARY KEY,user_id INTEGER,waist REAL,chest REAL,arms REAL,thighs REAL,hips REAL,note TEXT,logged TEXT);
    CREATE TABLE IF NOT EXISTS reward_points(id INTEGER PRIMARY KEY,user_id INTEGER,points INTEGER,reason TEXT,logged TEXT);
    ''')
    # Lightweight schema migration: preserve existing user records while adding newer fields.
    user_columns = {row['name'] for row in c.execute('PRAGMA table_info(users)').fetchall()}
    migrations = {
        'name': "TEXT DEFAULT ''", 'email': "TEXT", 'password': "TEXT DEFAULT ''",
        'age': 'INTEGER DEFAULT 25', 'height': 'REAL DEFAULT 170',
        'weight': 'REAL DEFAULT 70', 'goal': "TEXT DEFAULT 'Maintain'",
        'activity': "TEXT DEFAULT 'Moderate'", 'role': "TEXT DEFAULT 'user'"
    }
    for column, definition in migrations.items():
        if column not in user_columns:
            c.execute(f'ALTER TABLE users ADD COLUMN {column} {definition}')
    c.execute("UPDATE users SET role='user' WHERE role IS NULL OR role=''")
    c.execute("UPDATE users SET goal='Maintain' WHERE goal IS NULL OR goal=''")
    c.execute("UPDATE users SET activity='Moderate' WHERE activity IS NULL OR activity=''")
    if not c.execute("SELECT id FROM users WHERE email='admin@fitnest.local'").fetchone():
        c.execute("INSERT INTO users(name,email,password,age,height,weight,goal,activity,role) VALUES(?,?,?,?,?,?,?,?,?)",('FIT-NEST Admin','admin@fitnest.local',generate_password_hash('Admin@12345'),25,170,70,'Maintain','Moderate','admin'))
    c.commit(); c.close()
init_db()

def current():
    if session.get('uid'):
        c=conn(); u=c.execute('SELECT * FROM users WHERE id=?',(session['uid'],)).fetchone(); c.close(); return u
def login_required(f):
    @wraps(f)
    def wrap(*a,**kw):
        if not current(): flash('Please sign in first.','warning'); return redirect('/login')
        return f(*a,**kw)
    return wrap
def page(title,body):
    return render_template_string(BASE,title=title,body=body,u=current())
def timestamp(): return datetime.now().strftime('%Y-%m-%d %H:%M')
def n(v,default=0):
    try:return float(v)
    except:return default
def calorie_estimate(u):
    w=n(u['weight'],70); h=n(u['height'],170); age=n(u['age'],25)
    bmr=10*w+6.25*h-5*age+(5 if u['goal'] else -78)
    factor={'Sedentary':1.2,'Light':1.375,'Moderate':1.55,'Active':1.725,'Very active':1.9}.get(u['activity'],1.55)
    target=int(bmr*factor)
    if u['goal']=='Lose weight': target=max(1200,target-300)
    if u['goal']=='Build muscle': target+=250
    return target,int(w*1.6)

BASE = '''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{title}} · FIT-NEST Pro</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet"><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background:#0b1020;color:#edf2ff;font-family:Inter,system-ui}.navbar{background:#10192b!important;border-bottom:1px solid #293650}.navbar-brand{font-weight:900}.mint{color:#40e0b0}.wrap{max-width:1200px;margin:auto;padding:28px 18px 55px}.hero,.panel,.stat{background:#151e32;border:1px solid #2b3955;border-radius:22px;padding:23px;box-shadow:0 10px 28px #0002}.hero{padding:40px;background:radial-gradient(circle at 85% 0,#5035a4,transparent 38%),linear-gradient(135deg,#192743,#121a2c)}.hero h1{font-size:clamp(2.4rem,5vw,4rem);font-weight:900;letter-spacing:-2px}.grad{background:linear-gradient(90deg,#b7a3ff,#40e0b0);color:transparent;background-clip:text}.muted{color:#a8b5d0}.eyebrow{color:#40e0b0;font-size:.72rem;font-weight:800;letter-spacing:1.5px}.stat{height:100%;transition:.2s}.stat:hover,.panel:hover{border-color:#65759a}.number{font-size:2rem;font-weight:900}.btn-primary{background:linear-gradient(135deg,#8c63ff,#6045e8);border:0}.btn-success{background:#13a783;border:0}.form-control,.form-select{background:#0f1728;color:#edf2ff;border-color:#33425f;border-radius:12px}.form-control:focus,.form-select:focus{background:#0f1728;color:white;border-color:#8c63ff;box-shadow:0 0 0 .2rem #8c63ff33}.form-control::placeholder{color:#8190ac}.table{color:#edf2ff}.table td,.table th{border-color:#2a3855}.progress{height:9px;background:#293650}.progress-bar{background:linear-gradient(90deg,#8c63ff,#40e0b0)}.pill{background:#273653;color:#d6e0f5;border-radius:20px;padding:5px 10px;font-size:.8rem}.iconbox{background:#2a2451;color:#c5b4ff;border-radius:14px;width:44px;height:44px;display:grid;place-items:center;font-size:1.3rem}.footer{text-align:center;color:#71809e;margin-top:35px;font-size:.8rem}

/* FIT-NEST PRO responsive visual refresh */
:root{color-scheme:dark}
*{box-sizing:border-box}
html{scroll-behavior:smooth;overflow-x:hidden}
body{min-width:320px;overflow-x:hidden;line-height:1.6;background:radial-gradient(ellipse at 10% 0%,#182342 0%,#0b1020 42%,#080d19 100%)}
.navbar{backdrop-filter:blur(18px);padding:.8rem 0;z-index:1030}
.navbar .container-fluid{max-width:1600px}
.navbar-brand{font-size:1.2rem;letter-spacing:.3px;white-space:nowrap}
.navbar-nav{gap:.25rem!important}
.navbar .nav-link{padding:.55rem .75rem!important;border-radius:10px;color:#aebbd4!important;font-weight:600;font-size:.91rem;transition:background .2s,color .2s}
.navbar .nav-link:hover,.navbar .nav-link:focus{color:#fff!important;background:#8c63ff22}
.navbar .btn{border-radius:11px;padding:.55rem .9rem;font-weight:700}
.wrap{width:min(100%,1420px);max-width:1420px;margin-inline:auto;padding:clamp(18px,3vw,38px) clamp(14px,2.5vw,32px) 65px}
.hero{position:relative;overflow:hidden;border-radius:28px;padding:clamp(24px,4vw,52px);margin-bottom:26px;box-shadow:0 20px 60px #0004,inset 0 1px #ffffff0c}
.hero:after{content:"";position:absolute;width:280px;height:280px;border-radius:50%;right:-95px;bottom:-155px;background:#40e0b033;filter:blur(2px);pointer-events:none}
.hero h1{line-height:1.08;margin-bottom:1rem}
.panel,.stat{border-radius:22px;box-shadow:0 12px 35px #0003;transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease}
.panel:hover,.stat:hover{transform:translateY(-3px);border-color:#6859a8;box-shadow:0 16px 40px #0004}
.panel h2,.panel h3,.panel h4{letter-spacing:-.35px}
.row{--bs-gutter-x:1.25rem;--bs-gutter-y:1.25rem}
.btn{transition:transform .16s ease,filter .16s ease,box-shadow .16s ease}
.btn:hover{transform:translateY(-1px);filter:brightness(1.08)}
.btn-primary{box-shadow:0 7px 20px #7854ed30}
.form-control,.form-select{min-height:46px}
textarea.form-control{min-height:110px}
.table-responsive{border-radius:14px}
.table{vertical-align:middle}
.table thead th{color:#aebbd4;font-size:.78rem;text-transform:uppercase;letter-spacing:.7px}
.card,.modal-content{background:#151e32;color:#edf2ff;border-color:#2b3955;border-radius:20px}
.alert{border-radius:14px}
canvas{max-width:100%}
.footer{padding:20px 0}
@media(max-width:1199.98px){.navbar-expand-xxl .navbar-collapse{padding-top:.65rem}.navbar-nav{align-items:stretch!important}.navbar .nav-link{padding:.55rem .8rem!important}.navbar-nav .btn{margin:.25rem 0}}
@media(max-width:767.98px){.wrap{padding:18px 13px 45px}.hero{border-radius:20px;padding:25px 20px}.hero h1{letter-spacing:-1px;font-size:clamp(2rem,9vw,3rem)}.panel,.stat{padding:18px;border-radius:18px}.number{font-size:1.65rem}.navbar .container-fluid{padding-inline:14px!important}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
</style></head><body><nav class="navbar navbar-expand-xxl navbar-dark sticky-top"><div class="container-fluid px-4"><a class="navbar-brand" href="/"> <i class="bi bi-activity mint"></i> FIT-NEST <span class="mint">PRO</span></a><button class="navbar-toggler" data-bs-toggle="collapse" data-bs-target="#nav"><span class="navbar-toggler-icon"></span></button><div class="collapse navbar-collapse" id="nav"><ul class="navbar-nav ms-auto align-items-lg-center gap-lg-2">{% if u %}<li><a class="nav-link" href="/dashboard">Dashboard</a></li><li><a class="nav-link" href="/workouts">Workouts</a></li><li><a class="nav-link" href="/nutrition">Nutrition</a></li><li><a class="nav-link" href="/planner">Smart Planner</a></li><li><a class="nav-link" href="/assistant">Assistant</a></li><li><a class="nav-link" href="/progress">Progress</a></li><li><a class="nav-link" href="/goals">Goals</a></li><li><a class="nav-link" href="/reminders">Reminders</a></li><li><a class="nav-link" href="/water">Water</a></li><li><a class="nav-link" href="/timer">Timer</a></li><li><a class="nav-link" href="/measurements">Measurements</a></li><li><a class="nav-link" href="/rewards">Rewards</a></li>{% if u.role=='admin' %}<li><a class="nav-link" href="/admin">Admin</a></li><li><a class="nav-link" href="/admin/analytics">Analytics</a></li>{% endif %}<li><a class="btn btn-sm btn-outline-light" href="/profile">{{u.name}}</a></li><li><a class="btn btn-sm btn-danger" href="/logout">Logout</a></li>{% else %}<li><a class="nav-link" href="/login">User sign in</a></li><li><a class="nav-link" href="/admin/login">Admin sign in</a></li><li><a class="btn btn-sm btn-primary" href="/register">Get started</a></li>{% endif %}</ul></div></div></nav><div class="wrap">{% for cat,msg in get_flashed_messages(with_categories=true) %}<div class="alert alert-{{cat}} alert-dismissible fade show">{{msg}}<button class="btn-close" data-bs-dismiss="alert"></button></div>{% endfor %}{{body|safe}}<div class="footer">FIT-NEST Pro</div></div><script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script></body></html>'''

EXERCISES={'Chest':['Bench Press','Incline Press','Push-ups'],'Back':['Lat Pulldown','Seated Row','Deadlift'],'Shoulders':['Overhead Press','Lateral Raise'],'Biceps':['Barbell Curl','Hammer Curl'],'Triceps':['Pushdown','Dips'],'Legs':['Squats','Leg Press','Lunges'],'Core':['Plank','Crunches']}

@app.route('/')
def home():
    if session.get('uid'): return redirect('/dashboard')
    return page('Welcome','''<section class="hero"><div class="eyebrow">YOUR PERSONAL FITNESS ECOSYSTEM</div><h1 class="mt-3">Build strength.<br><span class="grad">Track progress.</span><br>Own your journey.</h1><p class="muted fs-5 mt-3">Training, nutrition, goals and insights in one focused fitness companion.</p><a href="/register" class="btn btn-primary btn-lg mt-3 me-2">Start your journey <i class="bi bi-arrow-right"></i></a><a href="/login" class="btn btn-outline-light btn-lg mt-3">Sign in</a></section><div class="row g-3 mt-2"><div class="col-md-4"><div class="stat"><div class="iconbox"><i class="bi bi-barbell"></i></div><h5 class="mt-3">Training plans</h5><p class="muted">Exercise library and logs.</p></div></div><div class="col-md-4"><div class="stat"><div class="iconbox"><i class="bi bi-egg-fried"></i></div><h5 class="mt-3">Nutrition insights</h5><p class="muted">Meal diary and macros.</p></div></div><div class="col-md-4"><div class="stat"><div class="iconbox"><i class="bi bi-graph-up"></i></div><h5 class="mt-3">Progress analytics</h5><p class="muted">Visualize weight trends.</p></div></div></div>''')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form.get('name','').strip();email=request.form.get('email','').strip().lower();pw=request.form.get('password','');h=n(request.form.get('height'));w=n(request.form.get('weight'));age=int(n(request.form.get('age')))
        if not name or len(pw)<8 or h<=0 or w<=0: flash('Please complete valid details (password 8+ characters).','warning')
        else:
            c=conn()
            try:c.execute('INSERT INTO users(name,email,password,age,height,weight,goal,activity,role) VALUES(?,?,?,?,?,?,?,?,?)',(name,email,generate_password_hash(pw),age,h,w,request.form.get('goal','Maintain'),request.form.get('activity','Moderate'),'user'));c.commit();flash('Account created. Sign in now.','success');return redirect('/login')
            except sqlite3.IntegrityError:flash('Email already registered.','danger')
            finally:c.close()
    return page('Register','''<div class="row justify-content-center"><div class="col-lg-7"><div class="panel"><h2 class="fw-bold">Create account</h2><form method="post" class="row g-3"><div class="col-md-6"><label>Name</label><input class="form-control" name="name" required></div><div class="col-md-6"><label>Email</label><input class="form-control" type="email" name="email" required></div><div class="col-md-6"><label>Password (8+)</label><input class="form-control" type="password" name="password" minlength="8" required></div><div class="col-md-6"><label>Age</label><input class="form-control" type="number" name="age" required></div><div class="col-md-6"><label>Height cm</label><input class="form-control" type="number" step=".1" name="height" required></div><div class="col-md-6"><label>Weight kg</label><input class="form-control" type="number" step=".1" name="weight" required></div><div class="col-md-6"><label>Goal</label><select class="form-select" name="goal"><option>Maintain</option><option>Lose weight</option><option>Build muscle</option><option>Improve endurance</option></select></div><div class="col-md-6"><label>Activity</label><select class="form-select" name="activity"><option>Sedentary</option><option>Light</option><option selected>Moderate</option><option>Active</option><option>Very active</option></select></div><div class="col-12"><button class="btn btn-primary w-100">Create account</button></div></form></div></div></div>''')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        c=conn();x=c.execute('SELECT * FROM users WHERE email=?',(request.form.get('email','').lower().strip(),)).fetchone();c.close()
        if x and check_password_hash(x['password'],request.form.get('password','')):
            if x['role']=='admin':
                flash('This is an administrator account. Please use Admin Sign in.','warning');return redirect('/admin/login')
            session.clear();session['uid']=x['id'];flash('Welcome back!','success');return redirect('/dashboard')
        flash('Invalid user credentials.','danger')
    return page('User Login','''<div class="row justify-content-center"><div class="col-md-5"><div class="panel"><div class="eyebrow">MEMBER ACCESS</div><h2 class="fw-bold">User sign in</h2><p class="muted">Sign in to your personal fitness account.</p><form method="post"><label>Email</label><input class="form-control mb-3" type="email" name="email" autocomplete="username" required><label>Password</label><input class="form-control mb-3" type="password" name="password" autocomplete="current-password" required><button class="btn btn-primary w-100">Sign in as user</button></form><p class="muted small mt-3">New to FIT-NEST PRO? <a href="/register">Create a user account</a></p><p class="muted small mt-2">Administrator? <a href="/admin/login">Use Admin Sign in</a></p></div></div></div>''')

@app.route('/admin/login',methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        c=conn();x=c.execute('SELECT * FROM users WHERE email=?',(request.form.get('email','').lower().strip(),)).fetchone();c.close()
        if x and x['role']=='admin' and check_password_hash(x['password'],request.form.get('password','')):
            session.clear();session['uid']=x['id'];flash('Administrator access granted.','success');return redirect('/admin')
        flash('Invalid administrator credentials.','danger')
    return page('Admin Login','''<div class="row justify-content-center"><div class="col-md-5"><div class="panel"><div class="eyebrow">RESTRICTED ACCESS</div><h2 class="fw-bold">Admin sign in</h2><p class="muted">This portal is only for FIT-NEST administrators.</p><form method="post"><label>Admin email</label><input class="form-control mb-3" type="email" name="email" autocomplete="username" required><label>Password</label><input class="form-control mb-3" type="password" name="password" autocomplete="current-password" required><button class="btn btn-primary w-100">Sign in as admin</button></form><p class="muted small mt-3"><a href="/login">Back to User Sign in</a></p></div></div></div>''')
@app.route('/logout')
def logout():session.clear();return redirect('/')

@app.route('/dashboard')
@login_required
def dashboard():
    x=current();c=conn();day=date.today().isoformat();nw=c.execute('SELECT COUNT(*) n FROM workouts WHERE user_id=? AND substr(logged,1,10)=?',(x['id'],day)).fetchone()['n'];m=c.execute('SELECT COALESCE(SUM(calories),0) cal,COALESCE(SUM(protein),0) p FROM meals WHERE user_id=? AND substr(logged,1,10)=?',(x['id'],day)).fetchone();logs=c.execute('SELECT * FROM weight_logs WHERE user_id=? ORDER BY id DESC LIMIT 5',(x['id'],)).fetchall();c.close()
    bmi=round(n(x['weight'])/(n(x['height'])/100)**2,1) if n(x['height']) else 0;kcal,prot=calorie_estimate(x);history=''.join(f"<tr><td>{r['weight']} kg</td><td>{r['logged']}</td></tr>" for r in logs) or '<tr><td colspan=2>No weigh-ins yet.</td></tr>'
    return page('Dashboard',f'''<div class="eyebrow">YOUR CONTROL CENTER</div><h1 class="fw-bold">Welcome, {x['name'].split()[0]} <span class="grad">👋</span></h1><p class="muted">Small actions. Strong habits. Real progress.</p><div class="row g-3"><div class="col-md-3"><div class="stat"><span class="muted">BMI estimate</span><div class="number">{bmi or '—'}</div></div></div><div class="col-md-3"><div class="stat"><span class="muted">Workouts today</span><div class="number">{nw}</div></div></div><div class="col-md-3"><div class="stat"><span class="muted">Calories today</span><div class="number">{int(m['cal'])}</div></div></div><div class="col-md-3"><div class="stat"><span class="muted">Protein today</span><div class="number">{round(m['p'],1)}g</div></div></div></div><div class="row g-3 mt-1"><div class="col-lg-7"><div class="panel"><h3>Quick actions</h3><div class="row g-2 mt-2">{''.join(f'<div class="col-6 col-md-4"><a class="btn {cl} w-100 py-3" href="{url}"><i class="bi {ico} d-block fs-4"></i>{label}</a></div>' for label,url,cl,ico in [('Workouts','/workouts','btn-primary','bi-barbell'),('Nutrition','/nutrition','btn-success','bi-egg-fried'),('Progress','/progress','btn-outline-light','bi-graph-up'),('Goals','/goals','btn-outline-light','bi-bullseye'),('Reminders','/reminders','btn-outline-light','bi-bell')])}</div><h4 class="mt-4">Recent weigh-ins</h4><table class="table"><thead><tr><th>Weight</th><th>Date</th></tr></thead><tbody>{history}</tbody></table></div></div><div class="col-lg-5"><div class="panel"><div class="eyebrow">DAILY ESTIMATE</div><div class="number">{kcal} kcal</div><p class="muted">Estimated calories; not medical guidance.</p>Protein reference: <b>{prot} g/day</b></div></div></div>''')

@app.route('/workouts')
@login_required
def workouts():
    cat=request.args.get('category','All');cards=''
    for group,items in EXERCISES.items():
        if cat not in ('All',group):continue
        forms=''.join(f'''<form method="post" action="/workout/log" class="border-top border-secondary pt-3 mt-3"><input type="hidden" name="category" value="{group}"><input type="hidden" name="exercise" value="{exercise}"><div class="d-flex gap-2 align-items-center flex-wrap"><b class="flex-grow-1">{exercise}</b><input class="form-control" style="width:75px" type="number" name="sets" value="3" min="1" max="20"><input class="form-control" style="width:90px" name="reps" value="10"><button class="btn btn-sm btn-success">Log</button></div></form>''' for exercise in items)
        cards+=f'<div class="col-lg-6"><div class="panel"><div class="eyebrow">TRAINING SPLIT</div><h3>{group}</h3>{forms}</div></div>'
    opts=''.join(f'<option {"selected" if cat==z else ""}>{z}</option>' for z in ['All']+list(EXERCISES))
    return page('Workouts',f'<h1 class="fw-bold">Exercise library</h1><p class="muted">Adjust sets and reps and log completed exercises.</p><form class="mb-3"><select class="form-select" name="category" style="max-width:240px" onchange="this.form.submit()">{opts}</select></form><div class="row g-3">{cards}</div><a class="btn btn-outline-light mt-3" href="/workout/history">Workout history</a>')
@app.route('/workout/log',methods=['POST'])
@login_required
def workout_log():
    g=request.form.get('category');e=request.form.get('exercise')
    if g not in EXERCISES or e not in EXERCISES[g]:flash('Invalid exercise.','danger');return redirect('/workouts')
    c=conn();c.execute('INSERT INTO workouts(user_id,category,exercise,sets,reps,logged) VALUES(?,?,?,?,?,?)',(session['uid'],g,e,max(1,min(20,int(n(request.form.get('sets'),3)))),request.form.get('reps','10')[:25],timestamp()));c.execute('INSERT INTO reward_points(user_id,points,reason,logged) VALUES(?,?,?,?)',(session['uid'],10,'Workout logged: '+e,timestamp()));c.commit();c.close();flash('Exercise logged! +10 reward points earned.','success');return redirect('/workouts')
@app.route('/workout/history')
@login_required
def workout_history():
    c=conn();rs=c.execute('SELECT * FROM workouts WHERE user_id=? ORDER BY id DESC LIMIT 150',(session['uid'],)).fetchall();c.close();rows=''.join(f"<tr><td>{r['logged']}</td><td>{r['category']}</td><td>{r['exercise']}</td><td>{r['sets']} × {r['reps']}</td></tr>" for r in rs) or '<tr><td colspan=4>No history yet.</td></tr>'
    return page('Workout history',f"<div class='panel'><h2>Workout history</h2><table class='table'><thead><tr><th>Date</th><th>Category</th><th>Exercise</th><th>Sets×reps</th></tr></thead><tbody>{rows}</tbody></table></div>")

@app.route('/nutrition',methods=['GET','POST'])
@login_required
def nutrition():
    target,pt=calorie_estimate(current());day=date.today().isoformat()
    if request.method=='POST':
        food=request.form.get('food','').strip();cal=int(n(request.form.get('calories')));p=n(request.form.get('protein'));carb=n(request.form.get('carbs'));fat=n(request.form.get('fats'))
        if food and min(cal,p,carb,fat)>=0:
            c=conn();c.execute('INSERT INTO meals(user_id,meal_type,food,calories,protein,carbs,fats,logged) VALUES(?,?,?,?,?,?,?,?)',(session['uid'],request.form.get('meal_type'),food,cal,p,carb,fat,timestamp()));c.commit();c.close();flash('Meal logged.','success');return redirect('/nutrition')
        flash('Check values.','warning')
    c=conn();rs=c.execute('SELECT * FROM meals WHERE user_id=? AND substr(logged,1,10)=? ORDER BY id DESC',(session['uid'],day)).fetchall();tot=c.execute('SELECT COALESCE(SUM(calories),0) cal,COALESCE(SUM(protein),0) p,COALESCE(SUM(carbs),0) cb,COALESCE(SUM(fats),0) ft FROM meals WHERE user_id=? AND substr(logged,1,10)=?',(session['uid'],day)).fetchone();c.close()
    rows=''.join(f"<tr><td>{r['meal_type']}</td><td>{r['food']}</td><td>{r['calories']}</td><td>{r['protein']}g</td><td><form method='post' action='/meal/{r['id']}/delete'><button class='btn btn-sm btn-outline-danger'>Remove</button></form></td></tr>" for r in rs) or '<tr><td colspan=5>No meals logged today.</td></tr>'
    return page('Nutrition',f'''<h1 class="fw-bold">Nutrition planner</h1><p class="muted">Meal diary and daily macro estimates.</p><div class="row g-3"><div class="col-lg-4"><div class="panel"><h3>Add meal</h3><form method="post"><label>Type</label><select class="form-select mb-3" name="meal_type"><option>Breakfast</option><option>Lunch</option><option>Dinner</option><option>Snack</option></select><label>Food/dish</label><input class="form-control mb-3" name="food" required><div class="row g-2"><div class="col-6"><label>Calories</label><input class="form-control" type="number" name="calories" min="0" required></div><div class="col-6"><label>Protein g</label><input class="form-control" type="number" step=".1" name="protein" value="0" min="0"></div><div class="col-6"><label>Carbs g</label><input class="form-control" type="number" step=".1" name="carbs" value="0" min="0"></div><div class="col-6"><label>Fats g</label><input class="form-control" type="number" step=".1" name="fats" value="0" min="0"></div></div><button class="btn btn-success w-100 mt-3">Add meal</button></form><small class="muted">Nutrition numbers are user-entered estimates.</small></div></div><div class="col-lg-8"><div class="row g-3"><div class="col-md-6"><div class="stat">Calories <div class="number">{int(tot['cal'])}/{target}</div><div class="progress"><div class="progress-bar" style="width:{min(100,100*tot['cal']/target)}%"></div></div></div></div><div class="col-md-6"><div class="stat">Protein <div class="number">{round(tot['p'],1)}/{pt}g</div><div class="progress"><div class="progress-bar" style="width:{min(100,100*tot['p']/pt)}%"></div></div></div></div><div class="col-12"><div class="panel"><div class="d-flex gap-4">Carbs <b>{round(tot['cb'],1)}g</b> Fats <b>{round(tot['ft'],1)}g</b></div><h3 class="mt-3">Today's food diary</h3><table class="table"><thead><tr><th>Type</th><th>Food</th><th>kcal</th><th>Protein</th><th></th></tr></thead><tbody>{rows}</tbody></table></div></div></div></div></div>''')
@app.route('/meal/<int:mid>/delete',methods=['POST'])
@login_required
def meal_delete(mid):
    c=conn();c.execute('DELETE FROM meals WHERE id=? AND user_id=?',(mid,session['uid']));c.commit();c.close();return redirect('/nutrition')

@app.route('/progress',methods=['GET','POST'])
@login_required
def progress():
    if request.method=='POST':
        w=n(request.form.get('weight'));note=request.form.get('note','')[:150]
        if 25<=w<=350:
            c=conn();c.execute('INSERT INTO weight_logs(user_id,weight,note,logged) VALUES(?,?,?,?)',(session['uid'],w,note,timestamp()));c.execute('UPDATE users SET weight=? WHERE id=?',(w,session['uid']));c.commit();c.close();flash('Weight log saved.','success');return redirect('/progress')
        flash('Weight must be 25–350 kg.','warning')
    c=conn();rs=c.execute('SELECT * FROM weight_logs WHERE user_id=? ORDER BY id',(session['uid'],)).fetchall();c.close();labels=json.dumps([r['logged'] for r in rs]);data=json.dumps([r['weight'] for r in rs]);rows=''.join(f"<tr><td>{r['logged']}</td><td>{r['weight']} kg</td><td>{r['note']}</td></tr>" for r in rs[::-1]) or '<tr><td colspan=3>No weigh-ins yet.</td></tr>'
    x=current();bmi=n(x['weight'])/(n(x['height'])/100)**2 if n(x['height']) else 0
    return page('Progress',f'''<h1 class="fw-bold">Progress analytics</h1><p class="muted">Bodyweight chart and historical logs.</p><div class="row g-3"><div class="col-lg-8"><div class="panel"><h3>Weight trend</h3><canvas id="chart" height="130"></canvas></div></div><div class="col-lg-4"><div class="panel"><h3>Add weigh-in</h3><form method="post"><label>Weight kg</label><input class="form-control mb-3" type="number" step=".1" name="weight" min="25" max="350" required><label>Note</label><input class="form-control mb-3" name="note"><button class="btn btn-primary w-100">Save</button></form><hr><span class="muted">BMI estimate</span><div class="number">{round(bmi,1) if bmi else '—'}</div><small class="muted">BMI is not a diagnosis.</small></div></div><div class="col-12"><div class="panel"><h3>Weigh-in history</h3><table class="table"><thead><tr><th>Date</th><th>Weight</th><th>Note</th></tr></thead><tbody>{rows}</tbody></table></div></div></div><script>new Chart(document.getElementById('chart'),{{type:'line',data:{{labels:{labels},datasets:[{{label:'Weight kg',data:{data},tension:.3,fill:true}}]}},options:{{responsive:true,plugins:{{legend:{{labels:{{color:'#edf2ff'}}}}}},scales:{{x:{{ticks:{{color:'#a8b5d0'}}}},y:{{ticks:{{color:'#a8b5d0'}}}}}}}}}});</script>''')

@app.route('/goals',methods=['GET','POST'])
@login_required
def goals():
    if request.method=='POST':
        title=request.form.get('title','').strip();target=n(request.form.get('target'));unit=request.form.get('unit','')[:20];due=request.form.get('due') or None
        if title and target>0:
            c=conn();c.execute('INSERT INTO goals(user_id,title,target,current,unit,due) VALUES(?,?,?,?,?,?)',(session['uid'],title,target,0,unit,due));c.commit();c.close();flash('Goal created.','success');return redirect('/goals')
        flash('Provide goal title and target.','warning')
    c=conn();rs=c.execute('SELECT * FROM goals WHERE user_id=? ORDER BY id DESC',(session['uid'],)).fetchall();c.close();cards=''
    for g in rs:
        pct=min(100,100*g['current']/g['target']) if g['target'] else 0
        cards+=f'''<div class="col-md-6"><div class="panel"><div class="d-flex justify-content-between"><div><span class="pill">{g['status']}</span><h4 class="mt-2">{g['title']}</h4><p class="muted">{g['current']}/{g['target']} {g['unit']} due {g['due'] or '—'}</p></div><form method="post" action="/goal/{g['id']}/delete"><button class="btn btn-sm btn-outline-danger">Delete</button></form></div><div class="progress mb-3"><div class="progress-bar" style="width:{pct}%"></div></div><form method="post" action="/goal/{g['id']}/update" class="d-flex gap-2"><input class="form-control" type="number" step=".1" min="0" name="current" value="{g['current']}"><button class="btn btn-primary">Update</button></form></div></div>'''
    return page('Goals',f'''<h1 class="fw-bold">Your goals</h1><div class="row g-3"><div class="col-lg-4"><div class="panel"><h3>Create goal</h3><form method="post"><label>Title</label><input class="form-control mb-3" name="title" required><label>Target</label><input class="form-control mb-3" type="number" step=".1" min=".1" name="target" required><label>Unit</label><input class="form-control mb-3" name="unit" placeholder="kg, km, workouts"><label>Due date</label><input class="form-control mb-3" type="date" name="due"><button class="btn btn-success w-100">Create goal</button></form></div></div><div class="col-lg-8"><div class="row g-3">{cards or "<div class='panel muted'>No goals yet.</div>"}</div></div></div>''')
@app.route('/goal/<int:gid>/update',methods=['POST'])
@login_required
def goal_update(gid):
    c=conn();g=c.execute('SELECT * FROM goals WHERE id=? AND user_id=?',(gid,session['uid'])).fetchone()
    if g:
        v=max(0,n(request.form.get('current')));c.execute('UPDATE goals SET current=?,status=? WHERE id=? AND user_id=?',(v,'Completed' if v>=g['target'] else 'Active',gid,session['uid']));c.commit()
    c.close();return redirect('/goals')
@app.route('/goal/<int:gid>/delete',methods=['POST'])
@login_required
def goal_delete(gid):
    c=conn();c.execute('DELETE FROM goals WHERE id=? AND user_id=?',(gid,session['uid']));c.commit();c.close();return redirect('/goals')

@app.route('/reminders',methods=['GET','POST'])
@login_required
def reminders():
    if request.method=='POST':
        title=request.form.get('title','').strip();when=request.form.get('when');kind=request.form.get('kind')
        if title and when:
            c=conn();c.execute('INSERT INTO reminders(user_id,title,kind,when_at) VALUES(?,?,?,?)',(session['uid'],title,kind,when));c.commit();c.close();flash('Reminder saved (stored only; no push delivery).','success');return redirect('/reminders')
    c=conn();rs=c.execute('SELECT * FROM reminders WHERE user_id=? ORDER BY when_at',(session['uid'],)).fetchall();c.close();rows=''.join(f"<tr><td>{r['title']}</td><td>{r['kind']}</td><td>{r['when_at']}</td><td>{'Done' if r['done'] else 'Pending'}</td><td><form class='d-inline' method='post' action='/reminder/{r['id']}/toggle'><button class='btn btn-sm btn-outline-success'>Toggle</button></form><form class='d-inline' method='post' action='/reminder/{r['id']}/delete'><button class='btn btn-sm btn-outline-danger'>Delete</button></form></td></tr>" for r in rs) or '<tr><td colspan=5>No reminders yet.</td></tr>'
    return page('Reminders',f'''<div class="row g-3"><div class="col-lg-4"><div class="panel"><h2>Reminders</h2><form method="post"><label>Title</label><input class="form-control mb-3" name="title" required><label>Type</label><select class="form-select mb-3" name="kind"><option>Workout</option><option>Hydration</option><option>Meal</option><option>General</option></select><label>Date/time</label><input class="form-control mb-3" type="datetime-local" name="when" required><button class="btn btn-primary w-100">Save</button></form><small class="muted">Stored in app; no push notifications.</small></div></div><div class="col-lg-8"><div class="panel"><h3>Schedule</h3><table class="table"><thead><tr><th>Title</th><th>Type</th><th>When</th><th>Status</th><th></th></tr></thead><tbody>{rows}</tbody></table></div></div></div>''')
@app.route('/reminder/<int:rid>/toggle',methods=['POST'])
@login_required
def reminder_toggle(rid):
    c=conn();r=c.execute('SELECT done FROM reminders WHERE id=? AND user_id=?',(rid,session['uid'])).fetchone()
    if r:c.execute('UPDATE reminders SET done=? WHERE id=? AND user_id=?',(1-r['done'],rid,session['uid']));c.commit()
    c.close();return redirect('/reminders')
@app.route('/reminder/<int:rid>/delete',methods=['POST'])
@login_required
def reminder_delete(rid):
    c=conn();c.execute('DELETE FROM reminders WHERE id=? AND user_id=?',(rid,session['uid']));c.commit();c.close();return redirect('/reminders')

@app.route('/admin')
@login_required
def admin():
    x=current()
    if x['role']!='admin':flash('Admin access only.','danger');return redirect('/dashboard')
    c=conn();rs=c.execute('SELECT id,name,email,role,weight FROM users ORDER BY id DESC').fetchall();nw=c.execute('SELECT COUNT(*) n FROM workouts').fetchone()['n'];nm=c.execute('SELECT COUNT(*) n FROM meals').fetchone()['n'];c.close()
    rows=''.join(f"<tr><td>{r['id']}</td><td>{r['name']}</td><td>{r['email']}</td><td>{r['role']}</td><td>{r['weight']}kg</td></tr>" for r in rs)
    return page('Admin',f'''<h1 class="fw-bold">Admin dashboard</h1><div class="row g-3 mt-1"><div class="col-md-4"><div class="stat">Accounts<div class="number">{len(rs)}</div></div></div><div class="col-md-4"><div class="stat">Workout logs<div class="number">{nw}</div></div></div><div class="col-md-4"><div class="stat">Meal records<div class="number">{nm}</div></div></div></div><div class="panel mt-3"><h3>Registered users</h3><table class="table"><thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Weight</th></tr></thead><tbody>{rows}</tbody></table></div>''')

@app.route('/api/me')
@login_required
def api_me():
    x=current();return jsonify(dict(id=x['id'],name=x['name'],email=x['email'],goal=x['goal'],weight=x['weight'],height=x['height']))
@app.route('/api/summary')
@login_required
def api_summary():
    c=conn();w=c.execute('SELECT substr(logged,1,10) day,COUNT(*) workouts FROM workouts WHERE user_id=? GROUP BY day ORDER BY day DESC LIMIT 30',(session['uid'],)).fetchall();m=c.execute('SELECT substr(logged,1,10) day,SUM(calories) calories,SUM(protein) protein FROM meals WHERE user_id=? GROUP BY day ORDER BY day DESC LIMIT 30',(session['uid'],)).fetchall();c.close();return jsonify(workouts=[dict(r) for r in w],nutrition=[dict(r) for r in m])


@app.route('/planner', methods=['GET','POST'])
@login_required
def planner():
    u=current(); result=None
    if request.method=='POST':
        goal=request.form.get('goal','Maintain')
        activity=request.form.get('activity','Moderate')
        diet=request.form.get('diet','Vegetarian')
        weight=n(u['weight'],70); height=n(u['height'],170); age=n(u['age'],25)
        bmi=weight/((height/100)**2) if height>0 else 0
        bmr=10*weight+6.25*height-5*age+5
        mult={'Sedentary':1.2,'Light':1.375,'Moderate':1.55,'Active':1.725,'Very Active':1.9}.get(activity,1.55)
        tdee=int(bmr*mult)
        calories=max(1200,tdee-350 if goal=='Lose' else tdee+250 if goal=='Gain' else tdee)
        protein=int(weight*1.6 if goal=='Gain' else weight*1.3)
        meals=('Breakfast: oats with milk/curd and fruit; Lunch: dal, rice/roti, vegetables and curd; Snack: roasted chana or paneer; Dinner: paneer/tofu, vegetables and roti.'
               if diet=='Vegetarian' else 'Breakfast: eggs or oats with milk; Lunch: lean protein with rice/roti and vegetables; Snack: yogurt or nuts; Dinner: lean protein, vegetables and roti.')
        plan=[('Monday','Upper body','Chest press, row, shoulder press, curls','3 sets × 8–12 reps'),('Tuesday','Lower body','Squats, lunges, hip hinge, calf raises','3 sets × 8–12 reps'),('Wednesday','Recovery','20–30 min walk + mobility','Light'),('Thursday','Upper body','Incline press, lat pulldown, lateral raises, triceps','3 sets × 8–12 reps'),('Friday','Lower + core','Leg press, hip hinge, plank','3 sets × 8–12 reps'),('Saturday','Cardio','Walk or cycle at comfortable pace','20–35 min'),('Sunday','Rest','Rest, hydrate, sleep','Recovery')]
        rows=''.join(f'<tr><td>{d}</td><td><b>{f}</b><br>{x}</td><td>{r}</td></tr>' for d,f,x,r in plan)
        result=f'''<div class="row g-3 mt-2"><div class="col-md-4"><div class="stat"><div class="muted">Estimated daily calories</div><div class="number">{calories:,}</div><small class="muted">kcal/day</small></div></div><div class="col-md-4"><div class="stat"><div class="muted">Suggested protein</div><div class="number">{protein} g</div><small class="muted">daily estimate</small></div></div><div class="col-md-4"><div class="stat"><div class="muted">BMI estimate</div><div class="number">{bmi:.1f}</div></div></div></div><div class="panel mt-3"><h3>Weekly workout plan</h3><div class="table-responsive"><table class="table"><thead><tr><th>Day</th><th>Focus / exercises</th><th>Volume</th></tr></thead><tbody>{rows}</tbody></table></div></div><div class="panel mt-3"><h3>Starter meal suggestions ({diet})</h3><p>{meals}</p><small class="muted">Portions are not specified; adjust to individual needs. Estimates are not medical advice.</small></div>'''
    body='''<div class="hero"><div class="eyebrow">PERSONALIZED FITNESS</div><h1>Smart <span class="grad">Planner</span></h1><p class="muted">Starter plan based on profile and selections. Calorie estimates are educational, not medical advice.</p></div><div class="panel mt-4"><form method="post" class="row g-3"><div class="col-md-4"><label class="form-label">Fitness goal</label><select class="form-select" name="goal"><option>Lose</option><option>Maintain</option><option>Gain</option></select></div><div class="col-md-4"><label class="form-label">Activity level</label><select class="form-select" name="activity"><option>Sedentary</option><option>Light</option><option selected>Moderate</option><option>Active</option><option>Very Active</option></select></div><div class="col-md-4"><label class="form-label">Diet preference</label><select class="form-select" name="diet"><option>Vegetarian</option><option>Non-vegetarian</option></select></div><div class="col-12"><button class="btn btn-primary">Generate my plan</button></div></form></div>'''
    if result: body+=result
    return page('Smart Planner',body)

@app.route('/assistant', methods=['GET','POST'])
@login_required
def assistant():
    answer=''
    if request.method=='POST':
        q=(request.form.get('question') or '').strip().lower()
        if any(k in q for k in ['chest','pector','push']):
            answer='Chest starter: chest press, incline press and cable fly. Begin with 2–3 sets of 8–12 controlled reps, manageable load, and 60–120 seconds rest.'
        elif any(k in q for k in ['back','lat','pull']):
            answer='Back starter: lat pulldown, seated row and light hip-hinge movement. Use controlled technique for 2–3 sets of 8–12 reps. Stop for sharp pain.'
        elif any(k in q for k in ['leg','squat','quad']):
            answer='Leg starter: bodyweight/goblet squat, leg press and calf raise. Start light, focus on form and use 2–3 sets of 8–12 reps.'
        elif any(k in q for k in ['diet','meal','protein','food']):
            answer='Balanced meals can include protein (dal, paneer, tofu, curd, beans, eggs or lean meat as preferred), vegetables/fruit and whole-grain carbohydrates. Track portions in Nutrition.'
        elif any(k in q for k in ['weight','bmi','calorie']):
            answer='BMI and calorie numbers are rough estimates, not diagnoses. Choose gradual sustainable habits; consult a clinician or dietitian for individual health concerns.'
        elif any(k in q for k in ['beginner','start','routine','workout']):
            answer='Beginner idea: 2–3 full-body sessions weekly with rest days. Practice squat, push, pull, hip hinge and core at comfortable effort; prioritize technique and recovery.'
        else:
            answer='I can offer starter tips on beginner workouts, exercise categories, balanced meal ideas, protein basics, calories and tracking. Try asking about chest, legs, protein foods or beginner workout.'
    body='''<div class="hero"><div class="eyebrow">FITNESS KNOWLEDGE</div><h1>FIT-NEST <span class="grad">Assistant</span></h1><p class="muted">Built-in rule-based fitness helper; it does not connect to an external AI service.</p></div><div class="panel mt-4"><form method="post"><label class="form-label">What would you like help with?</label><input class="form-control mb-3" name="question" placeholder="e.g. beginner workout, chest exercises, protein foods..." required><button class="btn btn-primary">Ask assistant</button></form></div>'''
    if answer: body+=f'<div class="panel mt-3"><div class="eyebrow">ASSISTANT RESPONSE</div><p class="mt-2">{answer}</p></div>'
    return page('Fitness Assistant',body)

# === Added feature modules ===
@app.route('/water', methods=['GET','POST'])
@login_required
def water_tracker():
    day=date.today().isoformat(); target=2500
    if request.method=='POST':
        amount=int(n(request.form.get('amount'),0))
        if 50<=amount<=2000:
            c=conn(); c.execute('INSERT INTO water_logs(user_id,amount_ml,logged) VALUES(?,?,?)',(session['uid'],amount,timestamp())); c.commit(); c.close(); flash(f'{amount} ml water added.','success'); return redirect('/water')
        flash('Enter an amount between 50 and 2000 ml.','warning')
    c=conn(); total=c.execute("SELECT COALESCE(SUM(amount_ml),0) total FROM water_logs WHERE user_id=? AND substr(logged,1,10)=?",(session['uid'],day)).fetchone()['total']; logs=c.execute("SELECT * FROM water_logs WHERE user_id=? AND substr(logged,1,10)=? ORDER BY id DESC",(session['uid'],day)).fetchall(); c.close()
    rows=''.join(f"<tr><td>{r['logged']}</td><td>{r['amount_ml']} ml</td><td><form method='post' action='/water/{r['id']}/delete'><button class='btn btn-sm btn-outline-danger'>Delete</button></form></td></tr>" for r in logs) or '<tr><td colspan=3>No entries today.</td></tr>'
    pct=min(100,100*total/target)
    body=f"<h1 class='fw-bold'>Water intake tracker</h1><p class='muted'>App reference target: {target} ml. Individual hydration needs vary.</p><div class='row g-3'><div class='col-md-5'><div class='stat'><div class='muted'>Today's intake</div><div class='number'>{total:,} ml</div><div class='progress mt-3'><div class='progress-bar' style='width:{pct}%'></div></div><p class='muted mt-2'>{pct:.0f}% of target</p><form method='post'><label>Amount (ml)</label><input class='form-control my-2' name='amount' type='number' min='50' max='2000' step='50' value='250' required><button class='btn btn-primary w-100'>Add water</button></form></div></div><div class='col-md-7'><div class='panel'><h3>Today's log</h3><table class='table'><thead><tr><th>Time</th><th>Amount</th><th></th></tr></thead><tbody>{rows}</tbody></table></div></div></div>"
    return page('Water Tracker',body)

@app.route('/water/<int:wid>/delete',methods=['POST'])
@login_required
def water_delete(wid):
    c=conn(); c.execute('DELETE FROM water_logs WHERE id=? AND user_id=?',(wid,session['uid'])); c.commit(); c.close(); return redirect('/water')

@app.route('/timer')
@login_required
def workout_timer():
    body="""<div class='hero'><div class='eyebrow'>TRAINING TOOL</div><h1>Workout <span class='grad'>Timer</span></h1><p class='muted'>Exercise countdown and rest interval timer.</p></div><div class='panel mt-4 text-center'><div class='row g-3 justify-content-center'><div class='col-md-4'><label>Minutes</label><input class='form-control' id='mins' type='number' min='0' max='180' value='1'></div><div class='col-md-4'><label>Seconds</label><input class='form-control' id='secs' type='number' min='0' max='59' value='0'></div></div><div class='display-1 fw-bold my-4' id='clock'>01:00</div><button class='btn btn-primary me-2' onclick='startTimer()'>Start</button><button class='btn btn-outline-light me-2' onclick='pauseTimer()'>Pause</button><button class='btn btn-outline-light' onclick='resetTimer()'>Reset</button><p class='muted mt-3' id='status'>Ready</p></div><script>let remaining=60,interval=null;function show(){document.getElementById('clock').textContent=String(Math.floor(remaining/60)).padStart(2,'0')+':'+String(remaining%60).padStart(2,'0')}function resetTimer(){pauseTimer();remaining=Math.max(0,parseInt(document.getElementById('mins').value||0)*60+parseInt(document.getElementById('secs').value||0));show();document.getElementById('status').textContent='Ready'}function startTimer(){if(interval)return;if(remaining<=0)resetTimer();document.getElementById('status').textContent='Timer running';interval=setInterval(()=>{if(remaining>0){remaining--;show()}else{pauseTimer();document.getElementById('status').textContent='Time complete!'}},1000)}function pauseTimer(){clearInterval(interval);interval=null;document.getElementById('status').textContent='Paused'}resetTimer();</script>"""
    return page('Workout Timer',body)

@app.route('/measurements',methods=['GET','POST'])
@login_required
def measurements():
    keys=('waist','chest','arms','thighs','hips')
    if request.method=='POST':
        vals=[n(request.form.get(k)) for k in keys]; note=(request.form.get('note') or '')[:200]
        if all(0<=v<=250 for v in vals) and any(v>0 for v in vals):
            c=conn(); c.execute('INSERT INTO body_measurements(user_id,waist,chest,arms,thighs,hips,note,logged) VALUES(?,?,?,?,?,?,?,?)',(session['uid'],*vals,note,timestamp())); c.commit(); c.close(); flash('Measurements saved.','success'); return redirect('/measurements')
        flash('Enter at least one measurement from 0 to 250 cm.','warning')
    c=conn(); rs=c.execute('SELECT * FROM body_measurements WHERE user_id=? ORDER BY id DESC LIMIT 100',(session['uid'],)).fetchall(); c.close()
    rows=''.join(f"<tr><td>{r['logged']}</td><td>{r['waist']}</td><td>{r['chest']}</td><td>{r['arms']}</td><td>{r['thighs']}</td><td>{r['hips']}</td><td>{r['note']}</td></tr>" for r in rs) or '<tr><td colspan=7>No measurements recorded.</td></tr>'
    inputs=''.join(f"<label>{label} (cm)</label><input class='form-control mb-3' type='number' step='0.1' min='0' max='250' name='{key}' value='0'>" for key,label in [('waist','Waist'),('chest','Chest'),('arms','Arms'),('thighs','Thighs'),('hips','Hips')])
    body=f"<h1 class='fw-bold'>Body measurement tracker</h1><p class='muted'>Record circumferences in centimeters to monitor changes.</p><div class='row g-3'><div class='col-lg-4'><div class='panel'><h3>Add measurement</h3><form method='post'>{inputs}<label>Note</label><input class='form-control mb-3' name='note'><button class='btn btn-primary w-100'>Save measurements</button></form></div></div><div class='col-lg-8'><div class='panel'><h3>Measurement history</h3><div class='table-responsive'><table class='table'><thead><tr><th>Date</th><th>Waist</th><th>Chest</th><th>Arms</th><th>Thighs</th><th>Hips</th><th>Note</th></tr></thead><tbody>{rows}</tbody></table></div></div></div></div>"
    return page('Measurements',body)

@app.route('/rewards')
@login_required
def rewards():
    c=conn(); total=c.execute('SELECT COALESCE(SUM(points),0) total FROM reward_points WHERE user_id=?',(session['uid'],)).fetchone()['total']; count=c.execute('SELECT COUNT(*) n FROM workouts WHERE user_id=?',(session['uid'],)).fetchone()['n']; logs=c.execute('SELECT * FROM reward_points WHERE user_id=? ORDER BY id DESC LIMIT 30',(session['uid'],)).fetchall(); c.close()
    badges=[('First Rep',count>=1,'Log your first exercise'),('10 Workouts',count>=10,'Log 10 exercise entries'),('25 Workouts',count>=25,'Log 25 exercise entries'),('100 Points',total>=100,'Earn 100 points'),('500 Points',total>=500,'Earn 500 points')]
    bhtml=''.join(f"<div class='col-md-4'><div class='stat'><div class='iconbox'><i class='bi {'bi-award-fill' if ok else 'bi-lock'}'></i></div><h5 class='mt-3'>{name}</h5><p class='muted'>{desc}</p><span class='pill'>{'Unlocked' if ok else 'Locked'}</span></div></div>" for name,ok,desc in badges)
    rows=''.join(f"<tr><td>{r['logged']}</td><td>{r['reason']}</td><td>+{r['points']}</td></tr>" for r in logs) or '<tr><td colspan=3>No points earned yet.</td></tr>'
    return page('Rewards',f"<h1 class='fw-bold'>Gamification & rewards</h1><div class='row g-3 mt-1'><div class='col-md-4'><div class='stat'>Total points<div class='number'>{total}</div></div></div><div class='col-md-4'><div class='stat'>Workout entries<div class='number'>{count}</div></div></div><div class='col-md-4'><div class='stat'>Points per exercise log<div class='number'>10</div></div></div></div><h3 class='mt-4'>Achievement badges</h3><div class='row g-3'>{bhtml}</div><div class='panel mt-3'><h3>Points history</h3><table class='table'><thead><tr><th>Date</th><th>Activity</th><th>Points</th></tr></thead><tbody>{rows}</tbody></table></div>")

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    u=current()
    if u['role']!='admin': flash('Admin access only.','danger'); return redirect('/dashboard')
    c=conn(); cats=c.execute('SELECT category,COUNT(*) n FROM workouts GROUP BY category ORDER BY n DESC').fetchall(); days=c.execute("SELECT substr(logged,1,10) day,COUNT(*) n FROM workouts GROUP BY day ORDER BY day DESC LIMIT 14").fetchall(); totals=c.execute('SELECT (SELECT COUNT(*) FROM users) users,(SELECT COUNT(*) FROM workouts) workouts,(SELECT COUNT(*) FROM meals) meals,(SELECT COUNT(*) FROM water_logs) water').fetchone(); c.close()
    labels=json.dumps([r['category'] for r in cats]); vals=json.dumps([r['n'] for r in cats]); dlabels=json.dumps([r['day'] for r in days[::-1]]); dvals=json.dumps([r['n'] for r in days[::-1]])
    body=f"<h1 class='fw-bold'>Advanced admin analytics</h1><div class='row g-3 mt-1'><div class='col-md-3'><div class='stat'>Users<div class='number'>{totals['users']}</div></div></div><div class='col-md-3'><div class='stat'>Workout logs<div class='number'>{totals['workouts']}</div></div></div><div class='col-md-3'><div class='stat'>Meal records<div class='number'>{totals['meals']}</div></div></div><div class='col-md-3'><div class='stat'>Water entries<div class='number'>{totals['water']}</div></div></div></div><div class='row g-3 mt-1'><div class='col-lg-6'><div class='panel'><h3>Workouts by category</h3><canvas id='cats' height='220'></canvas></div></div><div class='col-lg-6'><div class='panel'><h3>Daily workout activity (last 14 days)</h3><canvas id='daily' height='220'></canvas></div></div></div><script>new Chart(document.getElementById('cats'),{{type:'bar',data:{{labels:{labels},datasets:[{{label:'Workout logs',data:{vals}}}]}},options:{{responsive:true,plugins:{{legend:{{labels:{{color:'#edf2ff'}}}}}},scales:{{x:{{ticks:{{color:'#a8b5d0'}}}},y:{{ticks:{{color:'#a8b5d0'}}}}}}}}}});new Chart(document.getElementById('daily'),{{type:'line',data:{{labels:{dlabels},datasets:[{{label:'Workout entries',data:{dvals},tension:.3}}]}},options:{{responsive:true,plugins:{{legend:{{labels:{{color:'#edf2ff'}}}}}},scales:{{x:{{ticks:{{color:'#a8b5d0'}}}},y:{{ticks:{{color:'#a8b5d0'}}}}}}}}}});</script>"
    return page('Admin Analytics',body)

if __name__=='__main__': app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1')
