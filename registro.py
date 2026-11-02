import argparse
import logging
import signal
import threading

import grpc

import const
import nomes_pb2
import nomes_pb2_grpc


def registrar(endereco_ns, nome, ip, porta):
    with grpc.insecure_channel(endereco_ns) as canal:
        stub = nomes_pb2_grpc.ServicoNomesStub(canal)
        msg = nomes_pb2.BindMsg(name=nome, address=nomes_pb2.AddressMsg(ipaddress=ip, portnumber=porta))
        if stub.Bind(msg).status == 'OK':
            logging.info("bind '%s' -> %s:%s", nome, ip, porta)
        else:
            stub.Rebind(msg)
            logging.info("nome já existia; rebind '%s' -> %s:%s", nome, ip, porta)


def remover(endereco_ns, nome, ip, porta):
    try:
        with grpc.insecure_channel(endereco_ns) as canal:
            stub = nomes_pb2_grpc.ServicoNomesStub(canal)
            atual = stub.Lookup(nomes_pb2.NameMsg(name=nome), timeout=3)
            if (atual.ipaddress, atual.portnumber) != (ip, porta):
                logging.info("'%s' já aponta para outro endereço; sem unbind", nome)
                return
            stub.Unbind(nomes_pb2.NameMsg(name=nome), timeout=3)
            logging.info("unbind '%s'", nome)
    except grpc.RpcError as e:
        logging.warning("não foi possível fazer unbind: %s", e.code())


def executar_registrado(server, endereco_ns, nome, ip, porta):
    registrar(endereco_ns, nome, ip, porta)
    parar = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: parar.set())
    signal.signal(signal.SIGTERM, lambda *_: parar.set())
    parar.wait()
    remover(endereco_ns, nome, ip, porta)
    server.stop(0)


def argumentos_servidor(descricao):
    parser = argparse.ArgumentParser(description=descricao)
    parser.add_argument("--porta", default="0",
                        help="porta de escuta; 0 (padrão) = o sistema operacional escolhe uma livre")
    parser.add_argument("--ip", default="localhost",
                        help="IP desta máquina, visível para o cliente (é o que vai no bind)")
    parser.add_argument("--ns", default=f"{const.NS_IPADDR}:{const.NS_PORT}",
                        help="endereço ip:porta do Serviço de Nomes")
    return parser.parse_args()
