#!/bin/bash -eu

# RUN-LOCAL
# Run a client/server connection locally

MAX_RETRIES=4
RETRY_DELAY=2

NEXPYRO=$( cd $( dirname $0 ) ; /bin/pwd )
DAEMON=${NEXPYRO}/StartFileBrowser.py
# CLIENT=${NEXPYRO}/client.py
CLIENT=${NEXPYRO}/FileBrowserClient.py
# DAEMON=${NEXPYRO}/FileBrowserServer.py
# CLIENT=${NEXPYRO}/FileBrowserClient.py


NEXPY_SRC=$( cd ${NEXPYRO}/.. ; /bin/pwd )

PYTHON="python -u"
export PYTHONPATH=${NEXPY_SRC}

ARGS=${*}

message()
{
  echo "run.sh: ${*}"
}

# Start daemon
start_daemon() {
  TMPFILE=$( mktemp )
  echo "TMPFILE=${TMPFILE}"
  ( ${PYTHON} ${DAEMON} | tee ${TMPFILE} | sed 's/^/S: /' 2>&1 ) &
  DAEMON_PID=${!}
  message "Daemon running: pid: ${DAEMON_PID}"
  # echo "DAEMON_PID: ${DAEMON_PID}"
}

shutdown_daemon()
{
  PID=$1
  echo "Killing: ${PID}"
  kill ${PID} || true
  sleep 1
  kill -s KILL ${PID} || true
}

for ((i=1; i<=MAX_RETRIES; i++)); do
  start_daemon
  sleep 1
  URI=$(grep "URI:" ${TMPFILE} | cut -d ' ' -f 2)
  if [[ ${URI} == PYRO* ]]; then
    echo "URI: ${URI}"
    break
  else
    echo "Daemon startup failed! Attempt $i of $MAX_RETRIES."
    shutdown_daemon ${DAEMON_PID}
    if [[ $i -eq $MAX_RETRIES ]]; then
      echo "Failed to start daemon after $MAX_RETRIES attempts."
      exit 1
    fi
    sleep $RETRY_DELAY
  fi
done

COMMANDS_FILE="/tmp/test_commands.txt"
cat << EOF > $COMMANDS_FILE
nxinit /home/chopper.nxs
nxtree
nxfilename
nxgetmode
nxsetmode rw
nxgetitem entry
nxgetitem entry/sample
nxgetitem entry/sample/temperature
nxgetvalue entry/sample/temperature
nxgetvalue entry/data/data
nxgetvalue entry/data/data 0
nxgetvalue entry/data/data 0 0 
nxsetitem entry/sample/newitem 12.5
nxtree
nxsetvalue entry/sample/temperature 75.1
nxtree
nxupdate entry/sample/temperature entry/sample/temperature
nxtree
exit
EOF

# Start client in different directory (/tmp)
if ! ( cd /tmp ; ${PYTHON} ${CLIENT} ${ARGS} ${URI} < $COMMANDS_FILE )
then
  message "Client failed!"
fi

shutdown_daemon

# rm ${TMPFILE}
wait
exit 0
