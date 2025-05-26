# Copyright © 2023 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""All of the configuration for the service is captured here.

All items are loaded, or have Constants defined here that
are loaded into the Flask configuration.
All modules and lookups get their configuration from the
Flask config, rather than reading environment variables directly
or by accessing this configuration directly.
"""
import os

from dotenv import find_dotenv, load_dotenv

# this will load all the envars from a .env file located in the project root (api)
load_dotenv(find_dotenv())


class Config:  # pylint: disable=too-few-public-methods
    """Base class configuration that should set reasonable defaults.

    Used as the base for all the other configurations.
    """

    DEBUG = False
    DEVELOPMENT = False
    TESTING = False

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

    SOLR_SVC_LEADER_CORE = os.getenv("SOLR_SVC_LEADER_CORE", "bor")
    SOLR_SVC_FOLLOWER_CORE = os.getenv("SOLR_SVC_FOLLOWER_CORE", "bor_follower")
    SOLR_SVC_LEADER_URL = os.getenv("SOLR_SVC_LEADER_URL", "http://localhost:8883/solr")
    SOLR_SVC_FOLLOWER_URL = os.getenv("SOLR_SVC_FOLLOWER_URL", "http://localhost:8884/solr")
    HAS_FOLLOWER = SOLR_SVC_FOLLOWER_URL != SOLR_SVC_LEADER_URL

    BOR_API_URL = os.getenv("BOR_API_INTERNAL_URL", "http://")
    BOR_API_V1 = os.getenv("BOR_API_VERSION", "")

    BATCH_SIZE_SOLR = int(os.getenv("SOLR_BATCH_UPDATE_SIZE", "1000"))
    BATCH_SIZE_SOLR_SI = int(os.getenv("SOLR_BATCH_UPDATE_SIZE_SI", "1000"))
    REINDEX_CORE = os.getenv("REINDEX_CORE", "False") == "True"
    PRELOADER_JOB = os.getenv("PRELOADER_JOB", "False") == "True"
    INCLUDE_BTR_LOAD = os.getenv("INCLUDE_BTR_LOAD", "False") == "True"
    INCLUDE_COLIN_LOAD = os.getenv("INCLUDE_COLIN_LOAD", "True") == "True"
    INCLUDE_LEAR_LOAD = os.getenv("INCLUDE_LEAR_LOAD", "True") == "True"
    RESYNC_OFFSET = os.getenv("RESYNC_OFFSET", "130")

    BTR_BATCH_LIMIT = int(os.getenv("BTR_BATCH_LIMIT", "100000"))

    MODERNIZED_LEGAL_TYPES = os.getenv("MODERNIZED_LEGAL_TYPES", "BEN,CBEN,CP,GP,SP").upper().split(",")

    CORP_NUM_LIMITS_START = int(os.getenv("CORP_NUM_LIMITS_START", "0"))
    CORP_NUM_LIMITS_END = int(os.getenv("CORP_NUM_LIMITS_END", "10"))

    DEBUG_IDENTIFIERS = os.getenv("DEBUG_IDENTIFIERS", "")
    if DEBUG_IDENTIFIERS:
        DEBUG_IDENTIFIERS = DEBUG_IDENTIFIERS.split(",")

    IS_PARTIAL_IMPORT = (DEBUG_IDENTIFIERS or
                         CORP_NUM_LIMITS_START != 0 or
                         CORP_NUM_LIMITS_END != 10 or  # noqa: PLR2004
                         not INCLUDE_COLIN_LOAD or
                         not INCLUDE_LEAR_LOAD)

    # ORACLE - CDEV/CTST/CPRD
    ORACLE_USER = os.getenv("ORACLE_USER", "")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
    ORACLE_DB_NAME = os.getenv("ORACLE_DB_NAME", "")
    ORACLE_HOST = os.getenv("ORACLE_HOST", "")
    ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1521"))

    # POSTGRESQL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DB_USER = os.getenv("DATABASE_USERNAME", "")
    DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
    DB_NAME = os.getenv("DATABASE_NAME", "")
    DB_HOST = os.getenv("DATABASE_HOST_LEAR", "")
    DB_PORT = os.getenv("DATABASE_PORT", "5432")

    BTR_DB_USER = os.getenv("DATABASE_USERNAME_BTR", "")
    BTR_DB_PASSWORD = os.getenv("DATABASE_PASSWORD_BTR", "")
    BTR_DB_NAME = os.getenv("DATABASE_NAME_BTR", "")
    BTR_DB_HOST = os.getenv("DATABASE_HOST_BTR", "")
    BTR_DB_PORT = os.getenv("DATABASE_PORT_BTR", "5432")

    # Connection pool settings
    DB_MIN_POOL_SIZE = os.getenv("DATABASE_MIN_POOL_SIZE", "2")
    DB_MAX_POOL_SIZE = os.getenv("DATABASE_MAX_POOL_SIZE", "10")
    DB_CONN_WAIT_TIMEOUT = os.getenv("DATABASE_CONN_WAIT_TIMEOUT", "5")
    DB_CONN_TIMEOUT = os.getenv("DATABASE_CONN_TIMEOUT", "900")

    SQLALCHEMY_ENGINE_OPTIONS = {  # noqa: RUF012
        "pool_pre_ping": True,
        "pool_size": int(DB_MIN_POOL_SIZE),
        "max_overflow": (int(DB_MAX_POOL_SIZE) - int(DB_MIN_POOL_SIZE)),
        "pool_recycle": int(DB_CONN_TIMEOUT),
        "pool_timeout": int(DB_CONN_WAIT_TIMEOUT)
    }

    # Service account details
    ACCOUNT_SVC_AUTH_URL = os.getenv("ACCOUNT_SVC_AUTH_URL")
    ACCOUNT_SVC_CLIENT_ID = os.getenv("ACCOUNT_SVC_CLIENT_ID")
    ACCOUNT_SVC_CLIENT_SECRET = os.getenv("ACCOUNT_SVC_CLIENT_SECRET")

    # External API Timeouts
    try:
        ACCOUNT_SVC_TIMEOUT = int(os.getenv("ACCOUNT_SVC_TIMEOUT", "20"))
    except:  # pylint: disable=bare-except;
        ACCOUNT_SVC_TIMEOUT = 20

    # Cache stuff
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    try:
        CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))
    except (TypeError, ValueError):
        CACHE_DEFAULT_TIMEOUT = 300

    # Updated during the import for tracking performance
    TIME_WAITED_DATA_DB_SELECT_COLIN = 0
    TIME_WAITED_DATA_PARSING_COLIN = 0

    TIME_WAITED_DATA_DB_SELECT_LEAR = 0
    TIME_WAITED_DATA_PARSING_LEAR = 0

    TIME_WAITED_DATA_DB_SELECT_BTR = 0
    TIME_WAITED_DATA_PARSING_BTR = 0

    TIME_WAITED_IMPORT_API_CALL_PARTIAL = 0
    TIME_WAITED_IMPORT_API_CALL_FULL = 0
    TIME_WAITED_IMPORT_API_CALL_ERROR = 0

    TIME_WAITED_AUTH_TOKEN_CALL = 0


class DevelopmentConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for development environment."""

    DEBUG = True
    DEVELOPMENT = True
    TESTING = False


class UnitTestingConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for unit testing environment."""

    DEBUG = True
    DEVELOPMENT = False
    TESTING = True

    SOLR_SVC_LEADER_CORE = os.getenv("TEST_SOLR_SVC_LEADER_CORE", "bor")
    SOLR_SVC_FOLLOWER_CORE = os.getenv("TEST_SOLR_SVC_FOLLOWER_CORE", "bor_follower")
    SOLR_SVC_LEADER_URL = os.getenv("TEST_SOLR_SVC_LEADER_URL", "http://test.SOLR_SVC_LEADER_URL.fake")
    SOLR_SVC_FOLLOWER_URL = os.getenv("TEST_SOLR_SVC_FOLLOWER_URL", "http://test.SOLR_SVC_FOLLOWER_URL.fake")
    HAS_FOLLOWER = SOLR_SVC_FOLLOWER_URL != SOLR_SVC_LEADER_URL

    BOR_API_URL = "http://test.BOR_API_URL.fake"

    # ORACLE - CDEV/CTST/CPRD
    ORACLE_USER = os.getenv("ORACLE_TEST_USER", "")
    ORACLE_PASSWORD = os.getenv("ORACLE_TEST_PASSWORD", "")
    ORACLE_DB_NAME = os.getenv("ORACLE_TEST_DB_NAME", "")
    ORACLE_HOST = os.getenv("ORACLE_TEST_HOST", "")
    ORACLE_PORT = int(os.getenv("ORACLE_TEST_PORT", "1521"))

    DB_USER = os.getenv("DATABASE_TEST_USERNAME", "")
    DB_PASSWORD = os.getenv("DATABASE_TEST_PASSWORD", "")
    DB_NAME = os.getenv("DATABASE_TEST_NAME", "")
    DB_HOST = os.getenv("DATABASE_TEST_HOST_LEAR", "")
    DB_PORT = os.getenv("DATABASE_TEST_PORT", "5432")

    BTR_DB_USER = os.getenv("DATABASE_TEST_USERNAME_BTR", "")
    BTR_DB_PASSWORD = os.getenv("DATABASE_TEST_PASSWORD_BTR", "")
    BTR_DB_NAME = os.getenv("DATABASE_TEST_NAME_BTR", "")
    BTR_DB_HOST = os.getenv("DATABASE_TEST_HOST_BTR", "")
    BTR_DB_PORT = os.getenv("DATABASE_TEST_PORT_BTR", "5432")

    # Service account details
    ACCOUNT_SVC_AUTH_URL = "http://test.ACCOUNT_SVC_AUTH_URL.fake"


class ProductionConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for production environment."""

    DEBUG = False
    DEVELOPMENT = False
    TESTING = False
