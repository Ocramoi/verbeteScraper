#!/usr/bin/env python3

import os
import pandas as pd
import argparse
from dotenv import load_dotenv
import concurrent.futures
from typing import Callable

import scraper

load_dotenv()

parser = argparse.ArgumentParser(prog="wikiscrape",
                                 description="Extrai contribuições de verbetes\
                                 da Wikipedia [PT], exportando-os em tabelas",
                                 epilog="Marco Toledo - 2021")
parser.add_argument('-l',
                    '--lista',
                    type=str,
                    required=False,
                    action="store",
                    help="Arquivo CSV contendo os artigos dos quais as \
                    informações devem ser extraídas.")
parser.add_argument('-m',
                    '--matrizes',
                    type=str,
                    required=False,
                    action="store",
                    help="Arquivo de texto com a lista de temas das matrizes \
                    das quais extrair artigos, separadas linha a linha. Por \
                    padrão, apenas 'Brasil'.")
parser.add_argument('-s',
                    '--saida',
                    type=str,
                    default="verbetes.csv",
                    action="store",
                    help="Nome do arquivo CSV de saída que conterá os valores \
                    extraídos.")
parser.add_argument('-u',
                    '--unico',
                    action="store_true",
                    help="Se opção selecionada, extrai todos os artigos com \
                    revisor único na tabela.")
parser.add_argument('-c',
                    '--comentarios',
                    action="store_true",
                    help="Se opção selecionada, extrai todos os artigos sem \
                    comentários em suas revisões na tabela.")

args = parser.parse_args()
devEnv = (os.getenv("ENVIRONMENT") == "dev")


def getFiltro() -> Callable[[scraper.Verbete], bool]:
    if args.unico:
        return scraper.filtroContribuidores
    elif args.comentarios:
        return scraper.filtroComentarios

    return lambda v: True


def getMatrizes() -> [str]:
    if not args.matrizes:
        return ["Brasil"]

    with open(args.matrizes) as arqM:
        ms = arqM.readlines()
    return [m.strip() for m in ms]


def main():
    if devEnv:
        if args.comentarios:
            print("Extraíndo verbetes sem comentários de revisão...")
        elif args.unico:
            print("Extraíndo verbetes com contribuidor único...")
        else:
            print("Extração padrão...")
    dataSaida = []

    if args.lista:
        dfArtigos = pd.read_csv(args.lista)
    else:
        if args.comentarios or args.unico:
            mArts = "max"
        else:
            mArts = int(os.getenv("NUM_CLASSIFICACAO"))
        matrizes = getMatrizes()

        dfArtigos = scraper.geraLista(
            maxArtigos=mArts,
            matrizes=matrizes
        )
        if devEnv:
            dfArtigos.to_csv("listaGerada.csv")

    for idx, verbete in dfArtigos.iterrows():
        infos = scraper.scrapeVerbete(
            verbete["Nome"],
            getFiltro()
        )
        if not infos:
            continue
        if len(infos.Revisoes) < int(
                os.getenv("MIN_REVISOES")
        ):
            if devEnv:
                print(f'Erro no verbete {verbete["Nome"]},\
            número de revisões: {len(infos.Revisoes) if infos else None}')
            continue
        with concurrent.futures.ThreadPoolExecutor() as p:
            p.map(
                lambda contribuicao: dataSaida.append({
                    "Nome": infos.Titulo,
                    "Qualidade": verbete["Qualidade"],
                    "Importância": verbete["Importância"],
                    "Categorias": ", ".join([
                            categoria["title"]
                            .replace("Categoria:!", "")
                            .replace("Categoria:", "")
                            for categoria in infos.Categorias
                        ]),
                    "Número de contribuidores do verbete":
                    infos.NumContribuidores,
                    "Usuário": contribuicao["user"],
                    "Funções": ", ".join(contribuicao["roles"]),
                    "Tags": ", ".join(contribuicao["tags"]),
                    "Comentário": contribuicao["comment"],
                    "Conteúdo": list(contribuicao["slots"].values())[0]["*"],
                    "Data": contribuicao["timestamp"],
                }),
                infos.Revisoes
            )
    dfSaida = pd.DataFrame(
        data=dataSaida,
    )
    dfSaida.to_csv(args.saida)


if __name__ == "__main__":
    main()
