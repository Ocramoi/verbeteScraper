import os
import requests
import pandas as pd
from urllib import parse
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import random
from typing import Union, Callable
from dataclasses import dataclass

load_dotenv()
devEnv = (os.getenv("ENVIRONMENT") == "dev")
API_ENDPOINT = "https://pt.wikipedia.org/w/api.php?action=query&prop=revisions%7Ccategories%7Ccontributors&titles={tituloArtigo}&rvprop=user%7Ccomment%7Ctags%7Croles%7Ctags%7Ccontent%7Ctimestamp&rvslots=*&rvlimit=max&format=json&continue="
MATRIZ_BRASIL = "https://ptwikis.toolforge.org/Matriz:{matriz}&q{qualidade}i{importancia}"


@dataclass
class Verbete:
    Titulo: str
    Revisoes: [object]
    Categorias: [object]
    NumContribuidores: int


def filtroComentarios(v: Verbete) -> bool:
    for rev in v.Revisoes:
        if rev["comment"] != "":
            return False
    return True


def filtroContribuidores(v: Verbete) -> bool:
    return v.NumContribuidores == 1


def geraLista(
        maxArtigos: Union[str, int] = int(os.getenv("NUM_CLASSIFICACAO")),
        matrizes: [str] = ["Brasil"]
):
    if devEnv:
        print("Criando lista de artigos...")

    ELEMENTO_ARTIGOS = "a"
    SELETOR_ARTIGOS = {
        "class": "ext"
    }
    dataLista = []
    for matriz in matrizes:
        for q in range(int(os.getenv("MAX_QUALIDADE"))):
            for i in range(int(os.getenv("MAX_IMPORTANCIA"))):
                pagMatriz = requests.get(MATRIZ_BRASIL
                                         .format(
                                             matriz=matriz,
                                             qualidade=q + 1,
                                             importancia=i + 1
                                         ))
                soup = BeautifulSoup(pagMatriz.content, "html.parser")
                links = soup.findAll(
                    ELEMENTO_ARTIGOS,
                    SELETOR_ARTIGOS
                )[::3]
                if maxArtigos != 'max':
                    rands = random.sample(
                        links,
                        min(maxArtigos, len(links))
                    )
                else:
                    rands = links
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


def scrapeVerbete(
        titulo: str,
        filtro: Callable[[object], bool]
) -> Union[Verbete, None]:
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
            print(f'Revisões mal definidas em "{titulo}"!')
        revisoes = []

    try:
        categorias = listagem["categories"]
    except KeyError:
        if devEnv:
            print(f'Categorias mal definidas em "{titulo}"!')
        categorias = []

    nContributors = len(
        listagem["contributors"]
    )
    if "anoncontributors" in list(listagem.keys()):
        nContributors += listagem["anoncontributors"]

    extraido = Verbete(
        Titulo=titulo,
        Revisoes=revisoes,
        Categorias=categorias,
        NumContribuidores=nContributors
    )

    if filtro(extraido):
        if devEnv:
            print(f'Extraíndo informação do artigo "{titulo}"...')
        return extraido
    return False
