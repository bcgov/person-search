# Application Name

BC Beneficial Ownership Registry SOLR

## Technology Stack Used

- bitnami/solr
- Docker

### Development Setup

1. Pull the bitnami solr docker image

- `docker pull bitnami/solr:9.1.1`

2. Run your solr container

- if first time:
  - for a persistent index: `docker run -d -p 8883:8983 -v /<YOUR_PATH_TO_THIS_REPO>/beneficial-ownership/bor-solr/bitnami:/bitnami --name bor-solr-local bitnami/solr:9.1.1` (it will be available on port 8883)
  - for a temp index (changes will not persist -- use for bor-api unit tests):
    - `docker build . -t bor-solr-test`
    - `docker run -it --name=bor-solr-test -p 8899:8983 bor-solr-test` (it will be available on port 8899)
- else
  - `docker start bor-solr-local` or `docker start bor-solr-test`

3. Check logs for errors

- `docker logs bor-solr-local`

4. Go to admin UI in browser and check the solr core is there (it will be empty)

- http://localhost:8983/solr

5. Data import via the solr importer with REINDEX=True (for persistent index only)

- see https://github.com/bcgov-registries/beneficial-ownership/tree/main/bor-solr-importer and you will need:
  - run local COLIN oracle db OR setup VPN connection to COLIN dev OR comment out the COLIN load
  - run local LEAR db OR port-forward to dev instance OR comment out LEAR load

6. Stop the solr instance, make changes and reindex / rebuild the suggester

- `docker stop bor-solr-local`
- make changes
- `docker start bor-solr-local`
- reimport data with REINDEX=True (5.)
