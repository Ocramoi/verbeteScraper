# verbeteScraper

## Sobre
Extrai informações sobre revisões à artigos de todas as combinações de qualidade/importância da Wikipedia a partir da [matriz provida pelo serviço](https://ptwikis.toolforge.org/Matriz:Brasil) os registrando em uma tabela no formato CSV.

## Uso
Uma vez clonado ou baixo o repositório, simplesmente execute o arquivo `wikiscrape.py` no formato

``` sh
python3 wikiscrape.py [-h] [-l LISTA] [-s SAIDA] 
```

, sendo LISTA opcionalmente o nome da lista de artigos para serem extraídos (como no exemplo `listaArtigos.csv`) e SAIDA opcionalmente o nome do arquivo de saída (por padrão `verbetes.csv`).

## Customização
A execução pode ser modificada pelas variáveis de ambiente definidas em `.env`:

- `MAX_QUALIDADE`: qualidade máxima de artigo a ser extraído da tabela

- `MAX_IMPORTANCIA`: importância máxima de artigo a ser extraído da tabela

- `NUM_CLASSIFICACAO`: número de artigos a serem extraídos por classificação

- `MIN_REVISOES`: número mínimo de revisões que o artigo deve ter para ser registrado na tabela

- `ENVIRONMENT`: tipo de ambiente de execução, caso `dev` (padrão), todas as mesagens de debugging serão exibidas
