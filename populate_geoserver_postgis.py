#!/usr/bin/env python3
# script para criar um workspace, dataStore e camadas no GeoServer
# as senhas padrão das imagens docker não foram alteradas
# quando for colocar isso em produção, é preciso alterar as senhas, que estão nos arquivos docker-env/[geoserver.env, db.env]
#

import requests, json, subprocess
from urllib.parse import urljoin

geoserver_url = 'http://localhost:8600/geoserver/rest/'
headers = {'Content-type': 'application/json'}
user = 'admin'
passwd = 'myawesomegeoserver'

#### create workspace ####
endpoint = 'workspaces'
ws = 'zarc'
payload = {'workspace' : {'name' : ws, 'default' : 'TRUE'}}

r = requests.post(urljoin(geoserver_url, endpoint), auth = (user, passwd), headers = headers, data = json.dumps(payload))

#### inserindo limites estaduais e municipais no banco de dados ####
# dados do IBGE podem ser baixados no endereço
# https://www.ibge.gov.br/geociencias/downloads-geociencias.html
# BC250 está em cartas_e_mapas / bases_cartograficas_continuas / bc250 / versao_2019 / geopackage
# como inserção é feita via host do docker, a conexão é para o localhost, na porta exposta pelo docker
PG = 'PG:dbname=gis host=localhost port=25432 user=docker password=docker'
bc250 = '/home/daniel/geodb/IBGE/bc250_2017-11-08.gpkg'

subprocess.call(['ogr2ogr', '-t_srs', 'EPSG:4326', '-f', 'PostgreSQL', PG, bc250, 'lim_unidade_federacao_a'])
subprocess.call(['ogr2ogr', '-t_srs', 'EPSG:4326', '-f', 'PostgreSQL', PG, bc250, 'lim_municipio_a'])

#### cria PostGIS stores no GeoServer ####
# dica - se criarmos alguma coisa na mão do GeoServer e depois entrar no serviço rest
# podemos ver o payload JSON que gerou o dado
# ex. http://localhost:8600/geoserver/rest/workspaces/zarc/datastores/teste.json

# por estarmos fazendo conexão de um docker (geoserver) para outro (postgis)
# usamos no nome do host interno (db) e porta 5432
endpoint = 'workspaces/{}/datastores/'.format(ws)
data_store = 'gis'
docker_pghost = 'db'
pg_dbname = 'gis'
pg_user = 'docker'
pg_pass = 'xx' ## criei na mão e olhei o json do geoserver. Me retornou a senha critografada que estou usando

# provavelmente não precisa de todos os parâmetros
# mas como copiei de um datastore já criado, mantive tudo
payload = {
  "dataStore": {
    "name": data_store,
    "type": "PostGIS",
    "enabled": 'true',
    "workspace": {
      "name": "zarc",
      "href": "http://localhost:8600/geoserver/rest/workspaces/zarc.json"
    },
    "connectionParameters": {
      "entry": [
        {"@key": "host","$": docker_pghost},
        {"@key": "schema","$": "public"},
        {"@key": "database", "$": pg_dbname},
        {"@key": "user", "$": pg_user},
        {"@key": "passwd", "$": "crypt1:b0y8RUuP0yPa0uqq3GHiCA=="},
        {"@key": "Evictor run periodicity", "$": "300"},
        {"@key": "Max open prepared statements", "$": "50"},
        {"@key": "encode functions", "$": "true"},
        {"@key": "Batch insert size", "$": "1"},
        {"@key": "preparedStatements", "$": "false"},
        {"@key": "Loose bbox","$": "true"},
        {"@key": "SSL mode", "$": "DISABLE"},
        {"@key": "Estimated extends", "$": "true"},
        {"@key": "fetch size", "$": "1000"},
        {"@key": "Expose primary keys", "$": "false"},
        {"@key": "validate connections", "$": "true"},
        {"@key": "Support on the fly geometry simplification", "$": "true"},
        {"@key": "Connection timeout", "$": "20"},
        {"@key": "create database", "$": "false"},
        {"@key": "port", "$": "5432"},
        {"@key": "min connections", "$": "1"},
        {"@key": "dbtype", "$": "postgis"},
        {"@key": "namespace", "$": "http://zarc"},
        {"@key": "max connections", "$": "10"},
        {"@key": "Evictor tests per run", "$": "3"},
        {"@key": "Test while idle", "$": "true"},
        {"@key": "Max connection idle time", "$": "300"}
      ]
    },
    "_default": 'true',
    "featureTypes": "http://localhost:8600/geoserver/rest/workspaces/zarc/datastores/teste/featuretypes.json"
  }
}

r = requests.post(urljoin(geoserver_url, endpoint), auth = (user, passwd), headers = headers, data = json.dumps(payload))

#### Publicando camadas ####
endpoint = 'workspaces/{}/datastores/{}/featuretypes'.format(ws, data_store)

payload = {
  "featureType": {
    "name": "bc250_uf",
    "nativeName": "lim_unidade_federacao_a",
    "namespace": {
      "name": "zarc",
      "href": "http://localhost:8600/geoserver/rest/namespaces/zarc.json"
    },
    "title": "Unidades da Federação",
    "abstract": "Unidades da Federação. (BG250 - IBGE)",
    "keywords": {
      "string": [
        "features",
        "lim_unidade_federacao_a"
      ]
    }
  }
}

r = requests.post(urljoin(geoserver_url, endpoint), auth = (user, passwd), headers = headers, data = json.dumps(payload))

payload = {
  "featureType": {
    "name": "bc250_munic",
    "nativeName": "lim_municipio_a",
    "namespace": {
      "name": "zarc",
      "href": "http://localhost:8600/geoserver/rest/namespaces/zarc.json"
    },
    "title": "Municipios",
    "abstract": "Municípios brasileiros. (BG250 - IBGE)",
    "keywords": {
      "string": [
        "features",
        "lim_municipio_a"
      ]
    }
  }
}

r = requests.post(urljoin(geoserver_url, endpoint), auth = (user, passwd), headers = headers, data = json.dumps(payload))
