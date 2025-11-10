from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
from datetime import datetime
import json

# Cargar variables del entorno - Solo desarrollo
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-production')

# Configuración para Vercel 
print("=" * 60)
print("🚀 Iniciando aplicación en Vercel")
print("📍 Entorno:", os.environ.get('FLASK_ENV', 'production'))
print("🔑 SUPABASE_URL:", os.environ.get('SUPABASE_URL', 'No configurada'))
print("=" * 60)

# =============================================================================
# BASE DE DATOS SIMULADA
# =============================================================================

users_db = {
    'admin-user': {
        'id': 'admin-user',
        'email': 'admin@kendo.com',
        'role': 'admin',
        'password': 'admin123'
    },
    'client-user': {
        'id': 'client-user', 
        'email': 'cliente@kendo.com',
        'role': 'client',
        'password': 'cliente123'
    }
}

repair_requests_db = [
    {
        'id': 1,
        'user_id': 'client-user',
        'user_email': 'cliente@kendo.com',
        'equipment_type': 'Men (Máscara)',
        'description': 'Reparación de rejilla frontal dañada',
        'status': 'pendiente',
        'created_at': '2024-01-15 10:30:00'
    },
    {
        'id': 2,
        'user_id': 'client-user',
        'user_email': 'cliente@kendo.com', 
        'equipment_type': 'Shinai (Espada)',
        'description': 'Cambio de tsuru (cuerda) y reparación de empuñadura',
        'status': 'en_proceso',
        'created_at': '2024-01-10 14:20:00'
    },
    {
        'id': 3, 
        'user_id': 'client-user',
        'user_email': 'cliente@kendo.com',
        'equipment_type': 'Do (Peto)',
        'description': 'Ajuste de correas y limpieza general',
        'status': 'completado',
        'created_at': '2024-01-05 09:15:00'
    }
]

# Contador para nuevos IDs de solicitudes
next_request_id = 4

# =============================================================================
# SISTEMA DE ACTIVIDAD DE USUARIOS
# =============================================================================

# Datos de actividad de usuarios (simulados)
user_activity_db = [
    {
        'id': 1,
        'user_id': 'client-user',
        'user_email': 'cliente@kendo.com',
        'action': 'login',
        'description': 'Inició sesión en el sistema',
        'timestamp': '2024-01-15 09:30:00',
        'ip_address': '192.168.1.100'
    },
    {
        'id': 2,
        'user_id': 'client-user', 
        'user_email': 'cliente@kendo.com',
        'action': 'create_request',
        'description': 'Creó nueva solicitud: Men (Máscara)',
        'timestamp': '2024-01-15 10:15:00',
        'ip_address': '192.168.1.100'
    },
    {
        'id': 3,
        'user_id': 'admin-user',
        'user_email': 'admin@kendo.com',
        'action': 'status_update',
        'description': 'Actualizó estado de solicitud #1 a "en_proceso"',
        'timestamp': '2024-01-15 11:20:00',
        'ip_address': '192.168.1.50'
    },
    {
        'id': 4,
        'user_id': 'new-user',
        'user_email': 'nuevo@kendo.com',
        'action': 'register',
        'description': 'Nuevo usuario registrado en el sistema',
        'timestamp': '2024-01-15 14:45:00',
        'ip_address': '192.168.1.75'
    },
    {
        'id': 5,
        'user_id': 'client-user',
        'user_email': 'cliente@kendo.com',
        'action': 'view_dashboard',
        'description': 'Consultó el dashboard de solicitudes',
        'timestamp': '2024-01-15 16:30:00',
        'ip_address': '192.168.1.100'
    }
]

next_activity_id = 6

# Función para registrar actividad
def log_activity(user_id, user_email, action, description, ip_address="0.0.0.0"):
    global next_activity_id
    activity = {
        'id': next_activity_id,
        'user_id': user_id,
        'user_email': user_email,
        'action': action,
        'description': description,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip_address': ip_address
    }
    user_activity_db.append(activity)
    next_activity_id += 1
    print(f"📊 ACTIVIDAD: {user_email} - {action} - {description}")
    return activity

# =============================================================================
# RUTAS DE LA APLICACIÓN
# =============================================================================

@app.route('/favicon.ico')
def favicon_ico():
    return redirect(url_for('static', filename='images/favicon.png'))

@app.route('/favicon.png')
def favicon_png():
    return redirect(url_for('static', filename='images/favicon.png'))

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    return redirect(url_for('static', filename='images/favicon.png'))

@app.route('/')
def index():
    # Registrar actividad de visita a la página principal
    if 'user_id' in session:
        log_activity(
            session['user_id'],
            session['user_email'],
            'view_homepage', 
            'Visitó la página principal',
            request.remote_addr
        )
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Buscar usuario
        user = None
        for user_data in users_db.values():
            if user_data['email'] == email and user_data['password'] == password:
                user = user_data
                break
        
        if user:
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            
            # REGISTRAR ACTIVIDAD DE LOGIN
            log_activity(
                user['id'], 
                user['email'], 
                'login', 
                'Inició sesión en el sistema',
                request.remote_addr
            )
            
            flash(f'¡Bienvenido {user["email"]}!', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            # Registrar intento fallido de login
            log_activity(
                'unknown',
                email,
                'login_failed', 
                'Intento fallido de inicio de sesión',
                request.remote_addr
            )
            flash('Email o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('register.html')
        
        # Verificar si el email ya existe
        for user_data in users_db.values():
            if user_data['email'] == email:
                flash('Este email ya está registrado', 'error')
                return render_template('register.html')
        
        # Crear nuevo usuario
        new_user_id = f'user-{len(users_db) + 1}'
        users_db[new_user_id] = {
            'id': new_user_id,
            'email': email,
            'password': password,
            'role': 'client'
        }
        
        session['user_id'] = new_user_id
        session['user_email'] = email
        session['user_role'] = 'client'
        
        # REGISTRAR ACTIVIDAD DE REGISTRO
        log_activity(
            new_user_id,
            email,
            'register', 
            'Nuevo usuario registrado en el sistema',
            request.remote_addr
        )
        
        flash('¡Registro exitoso! Bienvenido al sistema.', 'success')
        return redirect(url_for('user_dashboard'))
    
    return render_template('register.html')

@app.route('/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # REGISTRAR ACTIVIDAD DE VISITA AL DASHBOARD
    log_activity(
        session['user_id'],
        session['user_email'],
        'view_dashboard', 
        'Consultó el dashboard de solicitudes',
        request.remote_addr
    )
    
    # Filtrar solicitudes del usuario actual
    user_requests = [req for req in repair_requests_db if req['user_id'] == session['user_id']]
    
    return render_template('dashboard.html', requests=user_requests)

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('Acceso denegado. Se requieren privilegios de administrador.', 'error')
        return redirect(url_for('login'))
    
    # REGISTRAR ACTIVIDAD DE VISITA AL PANEL ADMIN
    log_activity(
        session['user_id'],
        session['user_email'],
        'view_admin_panel', 
        'Accedió al panel de administración',
        request.remote_addr
    )
    
    # Ordenar actividad por timestamp (más reciente primero) y tomar últimas 15
    sorted_activity = sorted(user_activity_db, key=lambda x: x['timestamp'], reverse=True)
    recent_activities = sorted_activity[:15]
    
    return render_template('admin.html', 
                         requests=repair_requests_db,
                         users=users_db.values(),
                         activities=recent_activities)

@app.route('/create_request', methods=['GET', 'POST'])
def create_request():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        equipment_type = request.form['equipment_type']
        description = request.form['description']
        
        global next_request_id
        new_request = {
            'id': next_request_id,
            'user_id': session['user_id'],
            'user_email': session['user_email'],
            'equipment_type': equipment_type,
            'description': description,
            'status': 'pendiente',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        repair_requests_db.append(new_request)
        
        # REGISTRAR ACTIVIDAD DE CREACIÓN DE SOLICITUD
        log_activity(
            session['user_id'],
            session['user_email'],
            'create_request', 
            f'Creó nueva solicitud: {equipment_type}',
            request.remote_addr
        )
        
        next_request_id += 1
        flash('Solicitud de reparación creada exitosamente', 'success')
        return redirect(url_for('user_dashboard'))
    
    return render_template('create_request.html')

@app.route('/update_status/<int:request_id>', methods=['POST'])
def update_status(request_id):
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    new_status = request.json.get('status')
    
    # Buscar y actualizar la solicitud en la base de datos simulada
    request_updated = False
    for request_item in repair_requests_db:
        if request_item['id'] == request_id:
            old_status = request_item['status']
            request_item['status'] = new_status
            request_updated = True
            
            # REGISTRAR ACTIVIDAD DE ACTUALIZACIÓN DE ESTADO
            log_activity(
                session['user_id'],
                session['user_email'],
                'status_update', 
                f'Actualizó estado de solicitud #{request_id} de "{old_status}" a "{new_status}"',
                request.remote_addr
            )
            print(f"✅ Solicitud #{request_id} actualizada: {old_status} → {new_status}")
            break
    
    if request_updated:
        return jsonify({
            'success': True, 
            'new_status': new_status,
            'message': f'Estado actualizado a {new_status}'
        })
    else:
        return jsonify({'error': 'Solicitud no encontrada'}), 404

@app.route('/logout')
def logout():
    # REGISTRAR ACTIVIDAD DE LOGOUT
    if 'user_id' in session:
        log_activity(
            session['user_id'],
            session['user_email'],
            'logout', 
            'Cerró sesión en el sistema',
            request.remote_addr
        )
    
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('index'))

# =============================================================================
# API PARA OBTENER DATOS (Para AJAX)
# =============================================================================

@app.route('/api/requests')
def api_requests():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    if session.get('user_role') == 'admin':
        return jsonify(repair_requests_db)
    else:
        user_requests = [req for req in repair_requests_db if req['user_id'] == session['user_id']]
        return jsonify(user_requests)

@app.route('/api/activities')
def api_activities():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    # Ordenar actividad por timestamp (más reciente primero)
    sorted_activity = sorted(user_activity_db, key=lambda x: x['timestamp'], reverse=True)
    return jsonify(sorted_activity[:20])  # Últimas 20 actividades

# =============================================================================
# INICIALIZACIÓN
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Taller de Reparaciones Kendo - Sistema Iniciado")
    print("📍 Servidor corriendo en: http://127.0.0.1:5000")
    print("👤 Credenciales de prueba:")
    print("   Admin:    admin@kendo.com / admin123")
    print("   Cliente:  cliente@kendo.com / cliente123")
    print("📊 Sistema de actividad de usuarios: ACTIVADO")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

# Para Vercel
app = app