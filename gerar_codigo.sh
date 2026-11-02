#!/bin/sh
cd "$(dirname "$0")"
python -m grpc_tools.protoc -I protos --python_out=. --pyi_out=. --grpc_python_out=. \
  protos/nomes.proto protos/biblioteca.proto protos/dicionario.proto
