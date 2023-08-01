FROM solr:9.2.1
USER root

ARG VCS_REF="missing"
ARG BUILD_DATE="missing"
ARG ENVIRONMENT="dev"
ARG CORE="bor"
ARG LEADER_URL="missing"
ARG SOLR_OPTS_VAR='$SOLR_OPTS'

ENV VCS_REF=${VCS_REF}
ENV BUILD_DATE=${BUILD_DATE}
ENV ENVIRONMENT=${ENVIRONMENT}
ENV CORE=${CORE}
ENV LEADER_URL=${LEADER_URL}

LABEL org.label-schema.vcs-ref=${VCS_REF} \
    org.label-schema.build-date=${BUILD_DATE}

# copy files into leader / follower configsets
COPY ./solr/bor/conf /opt/solr-9.2.1/server/solr/configsets/bor/conf
COPY ./solr/bor/conf /opt/solr-9.2.1/server/solr/configsets/bor_follower/conf
# copy bor_follower specific config into configset
COPY ./solr/bor_follower/conf/solrconfig.xml /opt/solr-9.2.1/server/solr/configsets/bor_follower/conf/solrconfig.xml
# copy in starting core
COPY ./solr/bor/conf /var/solr/data/${CORE}/conf
COPY ./solr/${CORE}/core.properties /var/solr/data/${CORE}/core.properties
# copy core specific config into starting core
COPY ./solr/${CORE}/conf/solrconfig.xml /var/solr/data/${CORE}/conf/solrconfig.xml
# copy solr.xml (will be used by both leader and followers)
COPY ./solr/solr.xml /opt/solr-9.2.1/server/solr/solr.xml
# solr env overrides
RUN echo "" >> /etc/default/solr.in.sh
RUN echo SOLR_OPTS=\"$SOLR_OPTS_VAR -Dsolr.environment=$ENVIRONMENT\" >> /etc/default/solr.in.sh
RUN echo SOLR_OPTS=\"$SOLR_OPTS_VAR -Dsolr.leaderUrl=$LEADER_URL\" >> /etc/default/solr.in.sh
RUN echo SOLR_OPTS=\"$SOLR_OPTS_VAR -Dsolr.disable.allowUrls=true\" >> /etc/default/solr.in.sh
# jvm memory
RUN echo SOLR_JAVA_MEM=\"-Xms1024m -Xmx1024m\" >> /etc/default/solr.in.sh

RUN chmod -R 777 /var/solr/data
RUN chmod -R 777 /opt/solr-9.2.1

USER 1001

EXPOSE 8983
