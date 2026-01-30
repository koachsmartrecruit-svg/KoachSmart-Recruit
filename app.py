from core.app_factory import create_app
from core.extensions import socketio

# Create Flask app using factory
app = create_app()

# Application entrypoint
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)