import sys
import os
import logging
import importlib.util

# Set up logging to print to stderr (visible in Render logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log the Python version and sys.path
logger.info(f"Python version: {sys.version}")
logger.info(f"sys.path: {sys.path}")

# Log the site-packages directory
site_packages = next(p for p in sys.path if 'site-packages' in p)
logger.info(f"Site-packages directory: {site_packages}")

# Log the contents of the site-packages directory
try:
    site_packages_contents = os.listdir(site_packages)
    logger.info(f"Site-packages contents: {site_packages_contents}")
except Exception as e:
    logger.error(f"Error listing site-packages contents: {str(e)}")

# Check if flask_wtf directory exists in site-packages
flask_wtf_path = os.path.join(site_packages, 'flask_wtf')
logger.info(f"flask_wtf directory exists: {os.path.exists(flask_wtf_path)}")
if os.path.exists(flask_wtf_path):
    try:
        flask_wtf_contents = os.listdir(flask_wtf_path)
        logger.info(f"flask_wtf directory contents: {flask_wtf_contents}")
    except Exception as e:
        logger.error(f"Error listing flask_wtf directory contents: {str(e)}")
else:
    logger.error("flask_wtf directory does not exist in site-packages")

# Check if flask_wtf/__init__.py exists
flask_wtf_init_path = os.path.join(flask_wtf_path, '__init__.py')
logger.info(f"flask_wtf/__init__.py exists: {os.path.exists(flask_wtf_init_path)}")

# Attempt to import flask_wtf in different ways
try:
    import flask_wtf
    logger.info(f"Successfully imported flask_wtf: {flask_wtf.__version__}")
except ImportError as e:
    logger.error(f"Failed to import flask_wtf (direct import): {str(e)}")

try:
    from flask_wtf import FlaskForm
    logger.info("Successfully imported FlaskForm from flask_wtf")
except ImportError as e:
    logger.error(f"Failed to import FlaskForm from flask_wtf: {str(e)}")

# Attempt to manually load flask_wtf module using importlib
try:
    spec = importlib.util.find_spec("flask_wtf")
    if spec is None:
        logger.error("importlib.util.find_spec('flask_wtf') returned None")
    else:
        logger.info(f"Found flask_wtf spec: {spec}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["flask_wtf"] = module
        spec.loader.exec_module(module)
        logger.info("Successfully loaded flask_wtf using importlib")
except Exception as e:
    logger.error(f"Failed to load flask_wtf using importlib: {str(e)}")

# Minimal Flask app
try:
    from flask import Flask
    logger.info("Successfully imported Flask")
except ImportError as e:
    logger.error(f"Failed to import Flask: {str(e)}")
    raise

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World! Flask-WTF import test."

if __name__ == '__main__':
    app.run(debug=True)