#!/bin/bash

# Stop the containers
docker-compose down -v
docker-compose rm -sfv

# Remove the katana-container-log file
file=katana-container-logs
if [[ -L "$file" ]]; then
    rm -f $file
fi

# Remove the katana-log files
file1=katana-nbi/katana.log*
file2=katana-mngr/katana.log*
rm -f $file1 $file2

# Remove Kafka data
rm -rf zk-kafka/* || echo "Warning: Need root permission for removing Kafka and Zookeeper files - Try again with sudo"
