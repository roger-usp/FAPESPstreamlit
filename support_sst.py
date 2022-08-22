from os import listdir
from os.path import isfile, join
import json
import streamlit as st

uf_dict =  {
	'Brasil': 'Brasil',
	'Acre': 'AC',
	'Alagoas': 'AL',
	'Amapá': 'AP',
	'Amazonas': 'AM',
	'Bahia': 'BA',
	'Ceará': 'CE',
	'Distrito Federal': 'DF',
	'Espírito Santo': 'ES',
	'Goiás': 'GO',
	'Maranhão': 'MA',
	'Mato Grosso': 'MT',
	'Mato Grosso do Sul': 'MS',
	'Minas Gerais': 'MG',
	'Pará': 'PA',
	'Paraíba': 'PB',
	'Paraná': 'PR',
	'Pernambuco': 'PE',
	'Piauí': 'PI',
	'Rio de Janeiro': 'RJ',
	'Rio Grande do Norte': 'RN',
	'Rio Grande do Sul': 'RS',
	'Rondônia': 'RO',
	'Roraima': 'RR',
	'Santa Catarina': 'SC',
	'São Paulo': 'SP',
	'Sergipe': 'SE',
	'Tocantins': 'TO'
}

def create_biomass_prefixes_list():
	# biomass_prefixes_list = [(prefix1, biomass_type1, biomass_name1), ... ]
	biomass_path = "./biomass"
	onlyfiles = [f for f in listdir(biomass_path) if isfile(join(biomass_path, f))]
	onlyfiles = [f for f in onlyfiles if f.endswith(".json")]

	biomass_prefixes_list = list()
	for file in onlyfiles:
		prefix = file.split(".")[0]

		with open(f"{biomass_path}/{file}", "r", encoding="utf-8") as f:
			json_dict = json.load(f)

		biomass_type = json_dict["tipo_biomassa"]
		biomass_name = json_dict["nome_biomassa"]

		biomass_prefixes_list.append( (prefix, biomass_type, biomass_name) )

	return biomass_prefixes_list



def create_biomass_types_dict():
	biomass_types_dict = dict()
	
	for tup in create_biomass_prefixes_list():
		prefix, biomass_type, biomass_name = tup
		
		try:
			biomass_types_dict[biomass_type].append(biomass_name)
		except KeyError:
			biomass_types_dict[biomass_type] = [biomass_name]

	return biomass_types_dict