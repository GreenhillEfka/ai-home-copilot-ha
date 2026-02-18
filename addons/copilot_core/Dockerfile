ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python runtime and dependencies
RUN apk add --no-cache python3 py3-pip graphviz curl && \
    pip3 install --no-cache-dir \
        flask==3.0.2 \
        flask-compress==1.14 \
        waitress==3.0.0 \
        python-ulid==2.7.0 \
        pyyaml==6.0.1 \
        psutil==6.1.0 \
        neo4j==5.26.0 \
        pydantic==2.12.5 \
        requests==2.31.0

WORKDIR /usr/src/app
COPY rootfs/usr/src/app /usr/src/app

EXPOSE 8909 8099

# Start script that launches Ollama + PilotSuite
COPY rootfs/usr/src/app/start_dual.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]
