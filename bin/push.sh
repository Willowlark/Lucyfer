#! /bin/bash
docker tag lucybot:latest willowlark/lucybot:latest
docker push willowlark/lucybot:latest
# podman tag lucybot:latest willowlark/lucybot:latest
# podman login -i willowlark -p aLpXFw8mt4K2Fvz
# podman push lucybot docker://docker.io/willowlark/lucybot:latest