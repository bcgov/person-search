# Application Name

BC Beneficial Ownership Registry SOLR

## Technology Stack Used

- Apache Solr
- Docker

### Development Setup

1. Pull the base solr docker image

- `docker pull solr:9.6.1`

2. Run your solr containers

- if first time or need to pickup new solr changes outside of /solr/bor directory:
  - Build leader image: `make build-local`
  - Run leader image: `docker run -d -p 8883:8983 --name bor-solr-leader-local bor-solr-local` (it will be available on port 8883)
    _NOTE: if you want the data to persist then add `-v $PWD/solr/bor:/var/solr/data` (do NOT do this for the solr instance used for api unit tests)_
  - Optional: setup follower node
    - Get leader IP: `docker inspect bor-solr-leader-local | grep IPAddress`
    - Use the docker IP to set the leader url: `export LEADER_URL=http://leader_IP:8883/solr/bor`
    - Build the follower image: `make build-follower`
    - Run follower image: `docker run -d -p 8884:8984 --name bor-solr-follower-local bor-solr-follower` (it will be available on port 8884)
    - Add docker network so that follower can poll from leader:
      - `docker network create solr`
      - `docker network connect solr bor-solr-leader-local`
      - `docker network connect solr bor-solr-follower-local`
- else
  - `docker start bor-solr-leader-local`

3. Check logs for errors

- `docker logs bor-solr-leader-local`

4. Go to admin UI in browser and check the solr core is there (it will be empty)

- http://localhost:8883/solr

5. Load the leader index with data

- Data import via the solr importer with REINDEX=True (for persistent index only)
  - see https://github.com/bcgov-registries/beneficial-ownership/tree/main/bor-solr-importer and you will need:
    - run local COLIN oracle db OR setup VPN connection to COLIN dev OR comment out the COLIN load
    - run local LEAR db OR port-forward to dev instance OR comment out LEAR load
- OR alternatively you can use the bor-api internal update calls to add businesses/parties (see the bor-api postman collection for examples)
