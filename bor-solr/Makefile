.PHONY: build
.PHONY: build-leader
.PHONY: build-follower

DOCKER_NAME_LEADER:=bor-solr-leader
DOCKER_NAME_FOLLOWER:=bor-solr-follower

#################################################################################
# COMMANDS -- Setup                                                             #
#################################################################################

#################################################################################
# COMMANDS - CI                                                                 #

# expects the following provided:
# export TAG_NAME=$TAG_NAME
# export LEADER_URL=$LEADER_URL
#################################################################################

## Build the docker container for both the leader and follower cores
build: build-leader build-follower

build-leader:
ifeq ($(TAG_NAME),)
TAG_NAME=dev
endif
	docker build . -t $(DOCKER_NAME_LEADER) \
	    --platform linux/amd64 \
	    --build-arg VCS_REF=$(shell git rev-parse --short HEAD) \
	    --build-arg BUILD_DATE=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ") \
			--build-arg ENVIRONMENT=$(TAG_NAME) \
			--build-arg CORE=bor

build-follower:
ifeq ($(TAG_NAME),)
TAG_NAME=dev
endif
ifeq ($(LEADER_URL),)
LEADER_URL=http://localhost:8883/solr/bor
endif
	docker build . -t $(DOCKER_NAME_FOLLOWER) \
	    --platform linux/amd64 \
	    --build-arg VCS_REF=$(shell git rev-parse --short HEAD) \
	    --build-arg BUILD_DATE=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ") \
			--build-arg ENVIRONMENT=$(TAG_NAME) \
			--build-arg CORE=bor_follower \
			--build-arg LEADER_URL=$(LEADER_URL)
# gcloud compute ssh bor-solr-follower-1 --zone=northamerica-northeast1-a --project=yfjq17-dev --command='docker stop $(docker ps -a -q)'
# gcloud compute ssh bor-solr-follower-1 --zone=northamerica-northeast1-a --project=yfjq17-dev --command='docker rm $(docker stop $(docker ps -a -q))'
# gcloud compute ssh bor-solr-follower-1 --zone=northamerica-northeast1-a --project=yfjq17-dev --command="docker run -p 8983:8983 --name bor-solr northamerica-northeast1-docker.pkg.dev/yfjq17-tools/bor-solr-dev/bor-solr-dev solr-precreate bor_follower /opt/solr-9.2.1/server/solr/configsets/bor_follower"
#################################################################################
# COMMANDS - Local                                                              #
#################################################################################

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################
.PHONY: help

.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
