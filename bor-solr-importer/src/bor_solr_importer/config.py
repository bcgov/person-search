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


class Config():  # pylint: disable=too-few-public-methods
    """Base class configuration that should set reasonable defaults.

    Used as the base for all the other configurations.
    """

    DEBUG = False
    DEVELOPMENT = False
    TESTING = False

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

    SOLR_SVC_LEADER_CORE = os.getenv('SOLR_SVC_LEADER_CORE', 'bor')
    SOLR_SVC_FOLLOWER_CORE = os.getenv('SOLR_SVC_FOLLOWER_CORE', 'bor_follower')
    SOLR_SVC_LEADER_URL = os.getenv('SOLR_SVC_LEADER_URL', 'http://localhost:8883/solr')
    SOLR_SVC_FOLLOWER_URL = os.getenv('SOLR_SVC_FOLLOWER_URL', 'http://localhost:8884/solr')

    BOR_API_URL = os.getenv('BOR_API_INTERNAL_URL', 'http://')
    BOR_API_V1 = os.getenv('BOR_API_VERSION', '')

    POD_NAMESPACE = os.getenv('POD_NAMESPACE', 'unknown')

    LD_SDK_KEY = os.getenv('LD_SDK_KEY', None)
    SENTRY_DSN = os.getenv('SENTRY_DSN', None)
    SENTRY_TSR = os.getenv('SENTRY_TSR', '1.0')

    BATCH_SIZE_SOLR = int(os.getenv('SOLR_BATCH_UPDATE_SIZE', '1000'))
    REINDEX_CORE = os.getenv('REINDEX_CORE', 'False') == 'True'
    PRELOADER_JOB = os.getenv('PRELOADER_JOB', 'False') == 'True'
    RESYNC_OFFSET = os.getenv('RESYNC_OFFSET', '130')

    CORP_NUM_LIMITS_START = int(os.getenv('CORP_NUM_LIMITS_START', '0'))
    CORP_NUM_LIMITS_END = int(os.getenv('CORP_NUM_LIMITS_END', '10'))
    DEBUG_IDENTIFIERS = os.getenv('DEBUG_IDENTIFIERS', '')
    if DEBUG_IDENTIFIERS:
        DEBUG_IDENTIFIERS = DEBUG_IDENTIFIERS.split(',')

    IS_PARTIAL_IMPORT = DEBUG_IDENTIFIERS or CORP_NUM_LIMITS_START != 0 or CORP_NUM_LIMITS_END != 10

    # ORACLE - CDEV/CTST/CPRD
    ORACLE_USER = os.getenv('ORACLE_USER', '')
    ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD', '')
    ORACLE_DB_NAME = os.getenv('ORACLE_DB_NAME', '')
    ORACLE_HOST = os.getenv('ORACLE_HOST', '')
    ORACLE_PORT = int(os.getenv('ORACLE_PORT', '1521'))

    # POSTGRESQL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DB_LOCATION = os.getenv('DATABASE_LOCATION', 'OCP')

    DB_USER = os.getenv('DATABASE_USERNAME', '')
    DB_PASSWORD = os.getenv('DATABASE_PASSWORD', '')
    DB_NAME = os.getenv('DATABASE_NAME', '')
    DB_HOST = os.getenv('DATABASE_HOST_LEAR', '')
    DB_PORT = os.getenv('DATABASE_PORT', '5432')

    if DB_LOCATION == 'GCP':
        DB_USER = os.getenv('DATABASE_USERNAME_GCP', '')
        DB_PASSWORD = os.getenv('DATABASE_PASSWORD_GCP', '')
        DB_NAME = os.getenv('DATABASE_NAME_GCP', '')
        DB_HOST = os.getenv('DATABASE_HOST_GCP', '')
        DB_PORT = os.getenv('DATABASE_PORT_GCP', '5432')

    if DB_UNIX_SOCKET := os.getenv('DATABASE_UNIX_SOCKET', None):
        SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?host={DB_UNIX_SOCKET}'
    else:
        SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    # Connection pool settings
    DB_MIN_POOL_SIZE = os.getenv('DATABASE_MIN_POOL_SIZE', '2')
    DB_MAX_POOL_SIZE = os.getenv('DATABASE_MAX_POOL_SIZE', '10')
    DB_CONN_WAIT_TIMEOUT = os.getenv('DATABASE_CONN_WAIT_TIMEOUT', '5')
    DB_CONN_TIMEOUT = os.getenv('DATABASE_CONN_TIMEOUT', '900')

    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        # 'echo_pool': 'debug',
        'pool_size': int(DB_MIN_POOL_SIZE),
        'max_overflow': (int(DB_MAX_POOL_SIZE) - int(DB_MIN_POOL_SIZE)),
        'pool_recycle': int(DB_CONN_TIMEOUT),
        'pool_timeout': int(DB_CONN_WAIT_TIMEOUT)
    }

    # Service account details
    ACCOUNT_SVC_AUTH_URL = os.getenv('KEYCLOAK_AUTH_TOKEN_URL')
    ACCOUNT_SVC_CLIENT_ID = os.getenv('NDS_SERVICE_ACCOUNT_CLIENT_ID')
    ACCOUNT_SVC_CLIENT_SECRET = os.getenv('NDS_SERVICE_ACCOUNT_SECRET')

    # External API Timeouts
    try:
        ACCOUNT_SVC_TIMEOUT = int(os.getenv('AUTH_API_TIMEOUT', '20'))
    except:  # pylint: disable=bare-except; # noqa: B901, E722
        ACCOUNT_SVC_TIMEOUT = 20


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
    # SOLR
    SOLR_SVC_URL = os.getenv('SOLR_SVC_TEST_URL', 'http://')
    # POSTGRESQL
    DB_USER = os.getenv('DATABASE_TEST_USERNAME', '')
    DB_PASSWORD = os.getenv('DATABASE_TEST_PASSWORD', '')
    DB_NAME = os.getenv('DATABASE_TEST_NAME', '')
    DB_HOST = os.getenv('DATABASE_TEST_HOST', '')
    DB_PORT = os.getenv('DATABASE_TEST_PORT', '5432')
    SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{password}@{host}:{port}/{name}'.format(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        name=DB_NAME,
    )


class ProductionConfig(Config):  # pylint: disable=too-few-public-methods
    """Config object for production environment."""

    DEBUG = False
    DEVELOPMENT = False
    TESTING = False


config = {  # pylint: disable=invalid-name; Keeping name consistent with our other apps
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'unitTesting': UnitTestingConfig,
}
