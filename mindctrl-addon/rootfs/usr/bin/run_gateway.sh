#!/usr/bin/env bashio

echo "Starting MLflow Deployment Server in $PWD"
# TODO: add the replay env var to k8s spec
export MINDCTRL_CONFIG_REPLAY=${MINDCTRL_CONFIG_REPLAY:="false"}
export MINDCTRL_REPLAY_DIR=${MINDCTRL_REPLAY_DIR:="/replays"}
export MINDCTRL_RECORDING_DIR=${MINDCTRL_RECORDING_DIR:="/recordings"}
export MLFLOW_DEPLOYMENTS_CONFIG=${MLFLOW_DEPLOYMENTS_CONFIG:="/config/route-config.yaml"}

if bashio::supervisor.ping; then
  bashio::log.info "Supervisor is running, setting config from supervisor"
  export OPENAI_API_KEY="$(bashio::config 'OPENAI_API_KEY')"
else
    bashio::log.info "Supervisor is not running, setting config from environment"
    printenv
fi

# TODO: remove after replay server is built into mindctrl
export PYTHONPATH="/.context/services/deployments"

bashio::log.info "MINDCTRL_CONFIG_REPLAY: $MINDCTRL_CONFIG_REPLAY"
bashio::log.info "MINDCTRL_REPLAY_DIR: $MINDCTRL_REPLAY_DIR"
bashio::log.info "MINDCTRL_RECORDING_DIR: $MINDCTRL_RECORDING_DIR"
bashio::log.info "MLFLOW_DEPLOYMENTS_CONFIG: $MLFLOW_DEPLOYMENTS_CONFIG"
ls -la /
ls -la $MINDCTRL_REPLAY_DIR
ls -la $MINDCTRL_RECORDING_DIR
ls -la $MLFLOW_DEPLOYMENTS_CONFIG
#TODO: convert --replay into an enum and pass it down like another config
bashio::log.info "Starting MLflow Deployment Server with Dapr..."
if [ "$MINDCTRL_CONFIG_REPLAY" == "true" ]; then
    bashio::log.red "MINDCTRL_CONFIG_REPLAY is set to true. Running replay server in replay mode"
    # https://github.com/dapr/dashboard/issues/195
    s6-notifyoncheck dapr run --app-id deployments --app-port 5001 --app-protocol http \
      --enable-api-logging --enable-app-health-check --log-level warn --app-health-check-path /health --dapr-http-port 5501 -- \
      python3 /.context/services/deployments/replay_server.py --replay --config-path /.context/services/deployments/route-config.yaml --port 5001 --host 0.0.0.0
else
    bashio::log.red "MINDCTRL_CONFIG_REPLAY is not set to true. Running replay server in live mode"
    # https://github.com/dapr/dashboard/issues/195
    s6-notifyoncheck dapr run --app-id deployments --app-port 5001 --app-protocol http \
      --enable-api-logging --enable-app-health-check --log-level warn --app-health-check-path /health --dapr-http-port 5501 -- \
      python3 /.context/services/deployments/replay_server.py --config-path /.context/services/deployments/route-config.yaml --port 5001 --host 0.0.0.0
fi
