import streamlit as st
from streamlit import session_state as sst

from biomass import BiomassMap
from static_units import StaticUnits 
from dynamic_units import DynamicUnits
from support_sst import *

import matplotlib.pyplot as plt
import pandas as pd
import io

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
		sst["selected_biomass_name"] = "Algodão herbáceo."

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

		fig, ax = plt.subplots()
		sst[f"dynamic_unit_obj#{k}"] = DynamicUnits(
			fig=sst["biomass_obj"].fig,
			ax=sst["biomass_obj"].ax,
			legend_fig=fig,
			legend_ax=ax,
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
	units_list = [k for k in sst.keys() if k.startswith("static_unit_obj#") or k.startswith("dynamic_unit_obj#")]
	fig, ax = plt.subplots()
	ax.axis("off")

	for unit in units_list:
		marker = sst[unit].marker
		unit_type = sst[unit].unit_type
		try:
			color = sst[unit].color
		except:
			color = "black"

		ax.scatter(0,0, marker=marker, label=unit_type, color=color)

	ax.legend(framealpha=1, loc="center")

	legend_array = sst["biomass_obj"].fig_to_array(fig)
	legend_array = sst["biomass_obj"].remove_white_spaces(legend_array)

	st.image(legend_array)

def create_columns():
	units_list = [k for k in sst.keys() if k.startswith("dynamic_unit_obj#") or k == "biomass_obj"]
	col_list = [1,2] + [1/len(units_list) for _ in range(len(units_list))]
	col_list = st.columns(col_list)

	# widgets column
	with col_list[0]:
		create_uf_selector()
		update_biomass_obj_uf()

		st.write("Selecione as unidades desejadas:")
		create_static_unit_checkboxes()
		create_dynamic_units_checkboxes()

		create_legend()

	# map (fig) column
	with col_list[1]:
		create_fig()

	# All cbar legends
	for unit_idx, unit in enumerate(units_list):
		col_idx = unit_idx + 2  # 2 columns already created
		with col_list[col_idx]:
			st.image(sst[unit].cbar_array)

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

	logos, title_c = st.columns((1, 2))
	with logos:
		st.image("logos.png")
	with title_c:
		st.title("Distribuição de biomassa no Brasil")

	st.markdown("---")



	create_static_unit_objs()
	update_static_unit_objs()
	create_dynamic_units_objs()
	update_dynamic_unit_objs()


	create_columns()


	st.write("Fonte:", sst["biomass_obj"].source)
	st.write("Observações:", sst["biomass_obj"].obs)
	st.write("App criado por Roger Sampaio Bif")
if __name__ == "__main__":
	main()
