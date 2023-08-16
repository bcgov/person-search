.PHONY: build
.PHONY: build-leader
.PHONY: build-follower
.PHONY: setup

DOCKER_NAME_LEADER:=bor-solr-leader
DOCKER_NAME_FOLLOWER:=bor-solr-follower

#################################################################################
# COMMANDS -- Setup                                                             #
#################################################################################

#################################################################################
# COMMANDS - CD                                                                 #

# expects the following provided:
# export TAG_NAME=$TAG_NAME
# export LEADER_URL=$LEADER_URL
#################################################################################
build: build-leader build-follower
build-follower:
	docker build . -t $(DOCKER_NAME_FOLLOWER) \
	    --platform linux/amd64 \
	    --build-arg VCS_REF=$(shell git rev-parse --short HEAD) \
	    --build-arg BUILD_DATE=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ") \
			--build-arg CORE=bor_follower

build-leader:
	docker build . -t $(DOCKER_NAME_LEADER) \
	    --platform linux/amd64 \
	    --build-arg VCS_REF=$(shell git rev-parse --short HEAD) \
	    --build-arg BUILD_DATE=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ") \
			--build-arg CORE=bor

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
