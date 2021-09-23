#!/usr/bin/env python3

import os
import requests
import pandas as pd
import argparse
from urllib import parse
from dotenv import load_dotenv
import concurrent.futures
from bs4 import BeautifulSoup
import random

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
parser.add_argument('-s',
                    '--saida',
                    type=str,
                    default="verbetes.csv",
                    action="store",
                    help="Nome do arquivo CSV de saída que conterá os valores \
                    extraídos.")
args = parser.parse_args()
devEnv = (os.getenv("ENVIRONMENT") == "dev")
API_ENDPOINT = "https://pt.wikipedia.org/w/api.php?action=query&prop=revisions%7Ccategories&titles={tituloArtigo}&rvprop=user%7Ccomment%7Ctags%7Croles%7Ctags%7Ccontent%7Ctimestamp&rvslots=*&rvlimit=max&format=json&continue="
MATRIZ_BRASIL = "https://ptwikis.toolforge.org/Matriz:Brasil&q{qualidade}i{importancia}"


def geraLista():
    if devEnv:
        print("Criando lista de artigos...")

    ELEMENTO_ARTIGOS = "a"
    SELETOR_ARTIGOS = {
        "class": "ext"
    }
    dataLista = []
    for q in range(int(os.getenv("MAX_QUALIDADE"))):
        for i in range(int(os.getenv("MAX_IMPORTANCIA"))):
            pagMatriz = requests.get(MATRIZ_BRASIL
                                     .format(
                                         qualidade=q + 1,
                                         importancia=i + 1
                                     ))
            soup = BeautifulSoup(pagMatriz.content, "html.parser")
            links = soup.findAll(
                ELEMENTO_ARTIGOS,
                SELETOR_ARTIGOS
            )[::3]
            rands = random.sample(
                links,
                int(os.getenv("NUM_CLASSIFICACAO"))
            )
            for a in rands:
                dataLista.append({
                    "Nome": a.text,
                    "Qualidade": q + 1,
                    "Importância": i + 1
                })
    if devEnv:
        print("Lista de artigos criada!")

    return pd.DataFrame(
        data=dataLista,
    )


def scrapeVerbete(titulo):
    if devEnv:
        print(f'Extraíndo informação do artigo "{titulo}"...')
    page = requests.get(API_ENDPOINT
                        .format(tituloArtigo=parse.quote(titulo)))
    try:
        contribuicoes = page.json()
    except Exception as e:
        if devEnv:
            print("Erro {err} no artigo {titulo}".
                  format(err=e, titulo=titulo))
        return False

    listagem = list(contribuicoes["query"]["pages"].values())[0]

    try:
        revisoes = listagem["revisions"]
    except KeyError:
        if devEnv:
            print(f'Revisões não bem definidas em "{titulo}"!')
        revisoes = []

    try:
        categorias = listagem["categories"]
    except KeyError:
        if devEnv:
            print(f'Categorias não bem definidas em "{titulo}"!')
        categorias = []

    return {
        "revisoes": revisoes,
        "categorias": categorias
    }


def main():
    if args.lista:
        dfArtigos = pd.read_csv(args.lista)
    else:
        dfArtigos = geraLista()
        if devEnv:
            dfArtigos.to_csv("listaGerada.csv")
    dataSaida = []

    for idx, verbete in dfArtigos.iterrows():
        infos = scrapeVerbete(verbete["Nome"])
        if not infos or len(infos["revisoes"]) < int(
                os.getenv("MIN_REVISOES")
        ):
            if devEnv:
                print(f'Erro no verbete {verbete["Nome"]},\
            número de revisões: {len(infos["revisoes"]) if infos else None}')
            continue
        with concurrent.futures.ThreadPoolExecutor() as p:
            p.map(
                lambda contribuicao: dataSaida.append({
                    "Nome": verbete["Nome"],
                    "Qualidade": verbete["Qualidade"],
                    "Importância": verbete["Importância"],
                    "Categorias": ", ".join(
                        [
                            categoria["title"]
                            .replace("Categoria:", "")
                            .replace("Categoria:!", "")
                            for categoria in infos["categorias"]
                        ]
                    ),
                    "Usuário": contribuicao["user"],
                    "Funções": ", ".join(contribuicao["roles"]),
                    "Tags": ", ".join(contribuicao["tags"]),
                    "Comentário": contribuicao["comment"],
                    "Conteúdo": list(contribuicao["slots"].values())[0]["*"],
                    "Data": contribuicao["timestamp"],
                }),
                infos["revisoes"]
            )
    dfSaida = pd.DataFrame(
        data=dataSaida,
    )
    dfSaida.to_csv(args.saida)


if __name__ == "__main__":
    main()
