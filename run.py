from app import create_app
import os

# Create the Flask app instance
app = create_app()

if __name__ == '__main__':
    # Run the Flask app with default host and port
    app.run(debug=True, host='127.0.0.1', port=int(os.getenv('PORT', 5000)), use_reloader=False)
