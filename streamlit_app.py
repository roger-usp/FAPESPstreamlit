import streamlit as st
from streamlit import session_state as sst

from biomass import BiomassMap
from static_units import StaticUnits 
from dynamic_units import DynamicUnits
from support_sst import *

import matplotlib.pyplot as plt
import pandas as pd

def init_sst():
	# Support variables
	if "biomass_prefixes_list" not in sst:
		sst["biomass_prefixes_list"] = create_biomass_prefixes_list()  # from support_sst

	if "biomass_types_dict" not in sst:
		sst["biomass_types_dict"] = create_biomass_types_dict()  # from support_sst



	# Real session state variables
	if "selected_biomass_type" not in sst:
		sst["selected_biomass_type"] = "Oleaginosas"

	if "selected_biomass_name" not in sst:
		sst["selected_biomass_name"] = "Algodão"

	if "selected_biomass_name" in sst and sst["selected_biomass_name"] is None:
		sst["selected_biomass_name"] = sorted(sst["biomass_types_dict"][sst["selected_biomass_type"]])[0]



	if "selected_uf" not in sst:
		sst["selected_uf"] = "Brasil"


	for k in st.secrets["static_units"].keys():
		if f"su#{k}" not in sst:
			# su#{k} will be su#capitais
			sst[f"su#{k}"] = True

	for k in st.secrets["dynamic_units"].keys():
		if f"du#{k}" not in sst:
			# du#{k} will be du#centros_consumo
			sst[f"du#{k}"] = True


def make_biomass_selectors():
	st.sidebar.selectbox(
		label="Selecione o tipo de biomassa:",
		options=sorted( sst["biomass_types_dict"].keys() ),
		key="selected_biomass_type"
	)

	st.sidebar.selectbox(
		label="Selecione a biomassa:",
		options=sorted( sst["biomass_types_dict"][sst["selected_biomass_type"]] ),
		key="selected_biomass_name"
	)



def get_biomass_prefix():
	for tup in sst["biomass_prefixes_list"]:
		if tup[1:] == ( sst["selected_biomass_type"], sst["selected_biomass_name"] ):
			sst["selected_biomass_prefix"] = tup[0]
			
def create_biomass_obj():
	sst["biomass_obj"] = BiomassMap(
		fig=plt.figure(),
		legend_fig=plt.figure(),
		file_prefix=sst["selected_biomass_prefix"]
	)

def create_uf_selector():
	st.selectbox(
		label="Selecione o estado:",
		options=uf_dict.keys(),  # support_sst
		key="selected_uf"
	)

def update_biomass_obj_uf():
	selected_uf_abbr = uf_dict[sst["selected_uf"]]  # support_sst
	sst["biomass_obj"].change_uf(selected_uf_abbr)

def create_static_unit_checkboxes():
	for k in st.secrets["static_units"].keys():
		checkbox_label = st.secrets["static_units"][k]["specs_dict"]["tipo_unidade"]
		st.checkbox(
			label=checkbox_label,
			key=f"su#{k}"
		)



def create_static_unit_objs():
	for k in st.secrets["static_units"].keys():
		fixed_df = st.secrets["static_units"][k]["df"]
		fixed_df = pd.DataFrame(fixed_df)
		fixed_df.columns = fixed_df.iloc[0]
		fixed_df = fixed_df.iloc[1:].reset_index(drop=True)


		sst[f"static_unit_obj#{k}"] = StaticUnits(
			fig=sst["biomass_obj"].fig,
			ax=sst["biomass_obj"].ax,
			legend_fig=sst["biomass_obj"].legend_fig,
			legend_ax=sst["biomass_obj"].legend_ax,
			df=fixed_df,
			specs_dict=st.secrets["static_units"][k]["specs_dict"]
		)

def update_static_unit_objs():
	for k in st.secrets["static_units"].keys():
		sst[f"static_unit_obj#{k}"].change_visibility(
			visible=sst[f"su#{k}"],
			uf=uf_dict[sst["selected_uf"]]  # support_sst
		)


def create_dynamic_units_checkboxes():
	for k in st.secrets["dynamic_units"].keys():
		checkbox_label = st.secrets["dynamic_units"][k]["specs_dict"]["tipo_unidade"]
		st.checkbox(
			label=checkbox_label,
			key=f"du#{k}"
		)

def create_dynamic_units_objs():
	for k in st.secrets["dynamic_units"].keys():
		fixed_df = st.secrets["dynamic_units"][k]["df"]
		fixed_df = pd.DataFrame(fixed_df)
		fixed_df.columns = fixed_df.iloc[0]
		fixed_df = fixed_df.iloc[1:].reset_index(drop=True)


		sst[f"dynamic_unit_obj#{k}"] = DynamicUnits(
			fig=sst["biomass_obj"].fig,
			ax=sst["biomass_obj"].ax,
			legend_fig=sst["biomass_obj"].legend_fig,
			legend_ax=sst["biomass_obj"].legend_ax,
			df=fixed_df,
			specs_dict=st.secrets["dynamic_units"][k]["specs_dict"]
		)

def update_dynamic_unit_objs():
	for k in st.secrets["dynamic_units"].keys():
		sst[f"dynamic_unit_obj#{k}"].change_visibility(
			visible=sst[f"du#{k}"],
			uf=uf_dict[sst["selected_uf"]]  # support_sst
		)


def create_fig():
	st.pyplot(sst["biomass_obj"].fig)
def create_legend():
	st.pyplot(sst["biomass_obj"].legend_fig)


def main():
	st.set_page_config(
		page_title="Distribuição de biomassa no Brasil",
		layout="wide",
		page_icon="copaenergialogo.ico"
	)

	init_sst()

	make_biomass_selectors()
	get_biomass_prefix()
	create_biomass_obj()




	widgets_c, fig_c, legend_c = st.columns((1,2,2))
	with widgets_c:
		create_uf_selector()
		update_biomass_obj_uf()

		st.write("Selecione as unidades desejadas:")
		create_static_unit_checkboxes()
		create_dynamic_units_checkboxes()

	create_static_unit_objs()
	update_static_unit_objs()

	create_dynamic_units_objs()
	update_dynamic_unit_objs()

	with fig_c:
		create_fig() 

	with legend_c:
		create_legend()

if __name__ == "__main__":
	main()