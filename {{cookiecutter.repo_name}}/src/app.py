import logging
import os

from src.create_app import create_app
from src.config import Config
from src import api



logger = logging.getLogger(__name__)
app = create_app(Config, dependency_container_packages=[api])

