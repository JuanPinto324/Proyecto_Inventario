from app import create_app

app = create_app()

@app.errorhandler(403)
def forbidden(e):
    from flask import render_template
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found(e):
    from flask import redirect, url_for
    return redirect(url_for('dashboard.index'))

@app.route('/')
def root():
    from flask import redirect, url_for
    from flask_login import current_user
    if current_user.is_authenticated:
        if current_user.role in ('jefe', 'administrador'):
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('pos.index'))
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    app.run(debug=True)
