FROM ghcr.io/openclaw/openclaw-agent:latest
ENV AGENT_ID="pilot_agent"
COPY run.sh /init.d/run.sh
RUN chmod +x /init.d/run.sh
CMD ["/init.d/run.sh"]
