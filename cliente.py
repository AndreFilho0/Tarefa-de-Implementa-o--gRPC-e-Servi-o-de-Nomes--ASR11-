import argparse
import sys

import grpc

import biblioteca_pb2
import biblioteca_pb2_grpc
import const
import dicionario_pb2
import dicionario_pb2_grpc
import nomes_pb2
import nomes_pb2_grpc


def lookup(endereco_ns, nome):
    with grpc.insecure_channel(endereco_ns) as canal:
        stub = nomes_pb2_grpc.ServicoNomesStub(canal)
        resp = stub.Lookup(nomes_pb2.NameMsg(name=nome))
    if not resp.ipaddress:
        sys.exit(f"Serviço '{nome}' não encontrado no Serviço de Nomes")
    endereco = f"{resp.ipaddress}:{resp.portnumber}"
    print(f"lookup('{nome}') -> {endereco}")
    return endereco


def mostrar_livros(stub):
    for l in stub.ListarLivros(biblioteca_pb2.Vazio()).livros:
        print(f"    #{l.id} {l.titulo} ({l.autor}) - {'disponível' if l.disponivel else 'emprestado'}")


def usar_biblioteca(endereco):
    with grpc.insecure_channel(endereco) as canal:
        stub = biblioteca_pb2_grpc.BibliotecaStub(canal)
        novo = stub.CadastrarLivro(biblioteca_pb2.NovoLivro(titulo="O Hobbit", autor="J. R. R. Tolkien"))
        print(f"  CadastrarLivro -> #{novo.id} {novo.titulo}")
        print("  Emprestar #1   ->", stub.Emprestar(biblioteca_pb2.LivroId(id=1)).mensagem)
        print("  Emprestar #1   ->", stub.Emprestar(biblioteca_pb2.LivroId(id=1)).mensagem)
        print("  Emprestar #99  ->", stub.Emprestar(biblioteca_pb2.LivroId(id=99)).mensagem)
        print("  ListarLivros:")
        mostrar_livros(stub)
        print("  Devolver #1    ->", stub.Devolver(biblioteca_pb2.LivroId(id=1)).mensagem)


def usar_dicionario(endereco):
    with grpc.insecure_channel(endereco) as canal:
        stub = dicionario_pb2_grpc.DicionarioStub(canal)
        for palavra in ["gRPC", "lookup"]:
            r = stub.Buscar(dicionario_pb2.Palavra(palavra=palavra))
            print(f"  Buscar '{palavra}' ->", r.definicao if r.encontrada else "(não encontrada)")
        r = stub.Adicionar(dicionario_pb2.Verbete(
            palavra="lookup", definicao="Operação do serviço de nomes que devolve o endereço de um nome."))
        print("  Adicionar 'lookup' ->", r.mensagem)
        r = stub.Buscar(dicionario_pb2.Palavra(palavra="lookup"))
        print("  Buscar 'lookup' ->", r.definicao)
        print("  ListarPalavras ->", ", ".join(stub.ListarPalavras(dicionario_pb2.Vazio()).palavras))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Cliente dos serviços gRPC")
    parser.add_argument("--ns", default=f"{const.NS_IPADDR}:{const.NS_PORT}",
                        help="endereço ip:porta do Serviço de Nomes")
    args = parser.parse_args()

    print("== Biblioteca ==")
    usar_biblioteca(lookup(args.ns, "Biblioteca"))
    print("== Dicionário ==")
    usar_dicionario(lookup(args.ns, "Dicionario"))
