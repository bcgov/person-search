# Application Name

BC Beneficial Ownership Registry SOLR

## Technology Stack Used

- Apache Solr
- Docker

### Development Setup

1. Pull the base solr docker image

- `docker pull solr:9.10.1`

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

### VM Deployment

The Solr cluster runs on GCP Compute Engine VMs (`yfjq17-<env>`). Instance templates are created/refreshed via `bor-solr/create-templates.sh`; a blue-green deploy script is provided at `bor-solr/deploy-vm.sh`:

- `./create-templates.sh [dev|test|prod]` — recreate the leader (and follower for test/prod) instance templates from `startupscript.txt`, backing up any existing template to `<name>-old`. Machine types and JVM heap derive from per-env values in the script.
- the deploy script creates a new leader VM (and follower for test/prod) from instance templates
- waits for the new VMs to become healthy before swapping backends
- triggers the `bor-solr-importer-<env>` job in OpenShift to reindex into the new leader, pausing the sync schedulers around the import
- sets the follower's replication `leaderUrl` to the new leader's internal IP and waits for replication
- deletes the old VMs only after everything succeeds

**Prerequisites:** `gcloud` (authenticated), `oc` (authenticated), `docker`, `make`.

**Actions:**

| Command | Purpose |
| --- | --- |
| `./deploy-vm.sh build` | DEV only: build + push `bor-solr-leader` / `bor-solr-follower` images to `northamerica-northeast1-docker.pkg.dev/c4hnrd-tools/vm-repo` |
| `./deploy-vm.sh tag` | Tag the `dev` images for `test` / `prod` |
| `./deploy-vm.sh deploy` | Deploy new leader (DEV: leader only) or leader + follower (TEST/PROD), reindex, wire up replication |
| `./deploy-vm.sh deploy-follower` | TEST/PROD only: replace the follower against the existing leader |

**Options (deploy / deploy-follower):**

- `--leader-machine-type <type>` — override leader machine type (e.g. `e2-standard-4`)
- `--follower-machine-type <type>` — override follower machine type

**Configuration** (edit at the top of `deploy-vm.sh`):

- `ENV` — `dev` / `test` / `prod`
- `LEADER_TEMPLATE_VERSION` / `FOLLOWER_TEMPLATE_VERSION` — suffix on the base instance templates, if any (e.g. `v2`, `v8cpu`)

The instance templates, backend services (`bor-solr-leader-svc-<env>` / `bor-solr-follower-svc-<env>`), load balancers, instance groups and the `bor-solr-importer-<env>` cronjob/secret must already exist in the respective GCP/OpenShift projects.
