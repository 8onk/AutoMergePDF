import logging
import bpy

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Debug mode property
bpy.types.Scene.debug_mode = bpy.props.BoolProperty(
    name="Debug Mode",
    description="Enable debug mode for detailed logging",
    default=False
)

def log_debug(message):
    """Log a debug message if debug mode is enabled."""
    if bpy.context.scene.debug_mode:
        logger.debug(message)

def log_info(message):
    """Log an info message."""
    logger.info(message)

def log_warning(message):
    """Log a warning message."""
    logger.warning(message)

def log_error(message):
    """Log an error message."""
    logger.error(message)

def log_exception(e):
    """Log an exception with traceback."""
    logger.exception(e)

def log_variable(name, value):
    """Log the value of a variable."""
    if bpy.context.scene.debug_mode:
        logger.debug(f"{name}: {value}")