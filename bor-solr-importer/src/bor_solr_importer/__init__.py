# Copyright © 2023 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The BOR API service.

This module is the API for the BC Registries Registry Search system.
"""
import os

from flask import Flask

from bor_solr_importer.bor_api.services import solr
from bor_solr_importer.bor_api.services.authz import auth_cache
from bor_solr_importer.config import DevelopmentConfig, ProductionConfig, UnitTestingConfig
from bor_solr_importer.services import btr_db, lear_db, oracle_db
from bor_solr_importer.version import __version__
from structured_logging import StructuredLogging


def _get_build_openshift_commit_hash():
    return os.getenv("OPENSHIFT_BUILD_COMMIT", None)


def get_run_version():
    """Return a formatted version string for this service."""
    commit_hash = _get_build_openshift_commit_hash()
    if commit_hash:
        return f"{__version__}-{commit_hash}"
    return __version__


def register_shellcontext(app):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {"app": app}

    app.shell_context_processor(shell_context)


def create_app(config_name: str = os.getenv("DEPLOYMENT_ENV", "production") or "production"):
    """Return a configured Flask App using the Factory method."""
    config = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": UnitTestingConfig,
    }
    app = Flask(__name__)
    app.config.from_object(config.get(config_name, ProductionConfig))
    app.logger = StructuredLogging(app).get_logger()

    oracle_db.init_app(app)
    solr.init_app(app)
    auth_cache.init_app(app)

    if app.config["INCLUDE_LEAR_LOAD"]:
        lear_db.init_app(app)
    if app.config["INCLUDE_BTR_LOAD"]:
        btr_db.init_app(app)

    register_shellcontext(app)

    return app
