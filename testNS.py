import argparse

import grpc

import const
import nomes_pb2
import nomes_pb2_grpc


def run(endereco_ns):
    with grpc.insecure_channel(endereco_ns) as canal:
        stub = nomes_pb2_grpc.ServicoNomesStub(canal)

        def lookup():
            r = stub.Lookup(nomes_pb2.NameMsg(name='AppSvcTeste'))
            print(f"  Lookup  -> ip='{r.ipaddress}' porta='{r.portnumber}'")

        end1 = nomes_pb2.AddressMsg(ipaddress='10.0.0.1', portnumber='6000')
        end2 = nomes_pb2.AddressMsg(ipaddress='10.0.0.2', portnumber='7000')

        print("  Bind 10.0.0.1:6000          ->", stub.Bind(nomes_pb2.BindMsg(name='AppSvcTeste', address=end1)).status)
        lookup()
        print("  Bind repetido               ->", stub.Bind(nomes_pb2.BindMsg(name='AppSvcTeste', address=end2)).status)
        print("  Rebind 10.0.0.2:7000        ->", stub.Rebind(nomes_pb2.BindMsg(name='AppSvcTeste', address=end2)).status)
        lookup()
        print("  Unbind                      ->", stub.Unbind(nomes_pb2.NameMsg(name='AppSvcTeste')).status)
        lookup()
        print("  Unbind de nome inexistente  ->", stub.Unbind(nomes_pb2.NameMsg(name='AppSvcTeste')).status)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--ns", default=f"{const.NS_IPADDR}:{const.NS_PORT}")
    run(parser.parse_args().ns)
