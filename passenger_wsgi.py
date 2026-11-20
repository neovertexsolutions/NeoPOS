"""
passenger_wsgi.py - WSGI entry point for Phusion Passenger (cPanel / CloudLinux / Shared Hosting).
"""
import os
import sys

# 1. Ensure project root directory is on Python search path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2. Virtual environment auto-detection (for cPanel "Setup Python App")
for venv_name in ('.venv', 'venv', 'virtualenv'):
    venv_dir = os.path.join(BASE_DIR, venv_name)
    if os.path.isdir(venv_dir):
        # Linux/Unix standard: <venv>/lib/pythonX.Y/site-packages
        lib_dir = os.path.join(venv_dir, 'lib')
        if os.path.isdir(lib_dir):
            for entry in os.listdir(lib_dir):
                site_packages = os.path.join(lib_dir, entry, 'site-packages')
                if os.path.isdir(site_packages) and site_packages not in sys.path:
                    sys.path.insert(0, site_packages)
        # Windows standard: <venv>/Lib/site-packages
        win_sp = os.path.join(venv_dir, 'Lib', 'site-packages')
        if os.path.isdir(win_sp) and win_sp not in sys.path:
            sys.path.insert(0, win_sp)

# 3. Configure Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 4. Import the Django WSGI application
try:
    from config.wsgi import application
except Exception:
    # If a critical import error occurs at boot, output the traceback cleanly
    import traceback
    startup_traceback = traceback.format_exc()
    sys.stderr.write(f"Passenger Startup Error:\n{startup_traceback}\n")

    def application(environ, start_response):
        status = '500 Internal Server Error'
        output = f"Passenger WSGI Startup Error:\n\n{startup_traceback}".encode('utf-8')
        response_headers = [
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Content-Length', str(len(output)))
        ]
        start_response(status, response_headers)
        return [output]
