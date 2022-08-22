import biomass
import static_units
import os
import pandas as pd
import json

import tkinter as tk
from tkinter import ttk

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



class App(tk.Tk):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.iconbitmap("./copaenergialogo.ico")
		self.title("Distribuição de biomassa no Brasil")
		self.geometry(self.get_window_geometry())

		for page in [MainPage]:
			frame1 = page(self)
			frame1.config(background="white")
			frame1.pack()
			self.config(background="white")
			"""
			a = tk.Menu(self)
			b = tk.Menu(a, tearoff=0)
			b.add_command(label="b", command=print("b"))
			a.add_cascade(label="aa", menu=b)
			self.config(menu=a)
			"""
			self.config(menu=frame1.menu)
			# menu has to be an attribute in EVERY page created

	def get_window_geometry(self):
		with open(f"./dimensions/geometry.json", "r", encoding="utf-8") as file:
			json_dict = json.load(file)
			window_geometry = json_dict["window"]
			return window_geometry


class MainPage(tk.Frame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.STATE_TUPLE = ('Brasil','Acre', 'Alagoas', 'Amapá', 'Amazonas', 'Bahia', 'Ceará', 'Espírito Santo', 'Goiás', 'Maranhão', 'Mato Grosso', 'Mato Grosso do Sul', 'Minas Gerais', 'Pará', 'Paraíba', 'Paraná', 'Pernambuco', 'Piauí', 'Rio de Janeiro', 'Rio Grande do Norte', 'Rio Grande do Sul', 'Rondônia', 'Roraima', 'Santa Catarina', 'São Paulo', 'Sergipe', 'Tocantins')
		self.STATE_DICT = {'Brasil': 'Brasil','Acre':'AC', 'Alagoas':'AL', 'Amapá':'AP', 'Amazonas': 'AM', 'Bahia':'BA', 'Ceará':'CE', 'Espírito Santo': 'ES', 'Goiás': 'GO', 'Maranhão':'MA', 'Mato Grosso':'MT', 'Mato Grosso do Sul':'MS', 'Minas Gerais': 'MG', 'Pará':'PA', 'Paraíba':'PB', 'Paraná':'PR', 'Pernambuco':'PE', 'Piauí':'PI', 'Rio de Janeiro':'RJ', 'Rio Grande do Norte':'RN', 'Rio Grande do Sul':'RS', 'Rondônia':'RO', 'Roraima':'RR', 'Santa Catarina':'SC', 'São Paulo':'SP', 'Sergipe': 'SE', 'Tocantins':'TO'}
		self.biomass_path = "./biomass"
		self.static_units_path = "./static_units_files"
		self.menu = self.create_menu()

		self.get_figs_geometry()
		self.fig = Figure(figsize=self.map_geometry)
		self.legend_fig = Figure(figsize=self.legend_geometry)
		self.fig_canvas = FigureCanvasTkAgg(self.fig, self).get_tk_widget()
		self.legend_fig_canvas = FigureCanvasTkAgg(self.legend_fig, self).get_tk_widget()

		self.selected_state = tk.StringVar()

		self.create_state_selector_frame()
		self.biomass_object = biomass.BiomassMap(self.fig, self.legend_fig, file_prefix="palma")
		self.create_source_label()
		self.create_static_units()
		self.create_unit_checkboxes()
		self.setup_app()

	def get_figs_geometry(self):
		with open(f"./dimensions/geometry.json", "r", encoding="utf-8") as file:
			figs_json_dict = json.load(file)
			self.map_geometry = figs_json_dict["map"]
			self.legend_geometry = figs_json_dict["legend"]


	def setup_app(self):
		self.fig_canvas.grid(row=1, column=1)
		self.legend_fig_canvas.grid(row=1, column=2)
		self.state_selector_frame.grid(row=0, column=1)
		self.unit_checkboxes_frame.grid(row=0, column=0)
		self.source_label.grid(row=2, column=1)


	def create_source_label(self):
		self.source_label = tk.Label(self, text=f"Fonte: {self.biomass_object.source}", background="white")

	def change_source_label(self, new_source):
		self.source_label.config(text=f"Fonte: {new_source}")



	def create_state_selector_frame(self):
		self.state_selector_frame = tk.Frame(self)
		self.state_selector_frame.config(background="white")
		self.state_selector_label = tk.Label(self.state_selector_frame, text="Selecione um estado:", background="white")
		self.state_selector_label.grid(row=0, column=0)
		self.state_selector_bbox = self.create_state_bbox()
		self.state_selector_bbox.grid(row=1, column=0)

	def create_state_bbox(self):
		cbox = ttk.Combobox(self.state_selector_frame, textvariable=self.selected_state)
		cbox["values"] = self.STATE_TUPLE
		cbox["state"] = "readonly"
		cbox.set("Brasil")
		cbox.bind("<<ComboboxSelected>>", self.bbox_updated)
		return cbox

	def bbox_updated(self, event):
		selected_state_abbr = self.STATE_DICT[self.selected_state.get()]  # self.selected_state.get() = "São Paulo" , selected_state_abbr = "SP"
		self.biomass_object.change_uf(selected_state_abbr)
		self.update_static_units()
		self.update_fig_canvas()




	def update_fig_canvas(self):
		self.fig_canvas = FigureCanvasTkAgg(self.fig, self).get_tk_widget()
		self.legend_fig_canvas = FigureCanvasTkAgg(self.legend_fig, self).get_tk_widget()
		self.fig_canvas.grid(row=1, column=1)
		self.legend_fig_canvas.grid(row=1, column=2)



	def get_biomass_file_prefix_list(self):
		file_prefix_list = list()
		
		# get all the file prefixes to a list
		for filename in os.listdir(self.biomass_path):
			if filename.endswith(".csv"):
				file_prefix_list.append(filename.removesuffix(".csv"))
		return file_prefix_list

	def create_menu_df(self, file_prefix_list):
		# creates a dataframe with the file_prefix, biomass_type and biomass_name information
		menu_df = {"file_prefix": [], "biomass_type":[], "biomass_name":[]}
		for file_prefix in file_prefix_list:
			with open(f"{self.biomass_path}/{file_prefix}.json", "r", encoding="utf-8") as file:
				json_dict = json.load(file)

			menu_df["file_prefix"].append(file_prefix)
			menu_df["biomass_type"].append(json_dict["tipo_biomassa"])
			menu_df["biomass_name"].append(json_dict["nome_biomassa"])

		menu_df = pd.DataFrame(menu_df)
		menu_df = menu_df.loc[menu_df.file_prefix != "mapa_vazio"]
		self.menu_df = menu_df
		return menu_df

	def create_menu(self):
		menu = tk.Menu(self)
		file_prefix_list = self.get_biomass_file_prefix_list()
		menu_df = self.create_menu_df(file_prefix_list)
		biomass_type_menus = dict()

		# creates a menu for each biomass type
		for biomass_type in menu_df.biomass_type.unique():
			biomass_type_menus[biomass_type] = tk.Menu(menu, tearoff=0)

		# adds a command to each menu
		for index, row in menu_df.iterrows():
			biomass_type_menus[row.biomass_type].add_command(
				label=row.biomass_name,
				command=lambda x=row.file_prefix: self.change_biomass(x)
			)
		# put everything together
		for biomass_type_name, biomass_type_menu in biomass_type_menus.items():
			menu.add_cascade(label=biomass_type_name, menu=biomass_type_menu)
		
		return menu



	def get_static_units_file_prefix_list(self):
		# gets all the prefixes
		static_prefix_list = list()
		for filename in os.listdir(self.static_units_path):
			if filename.endswith(".csv"):
				static_prefix_list.append(filename.removesuffix(".csv"))
		return static_prefix_list

	def create_static_units_df(self, static_prefix_list):
		df = {"file_prefix":[],"unit_type": [], "marker": [], "color":[]}
		for file_prefix in static_prefix_list:
			with open(f"{self.static_units_path}/{file_prefix}.json", "r", encoding="utf-8") as file:
				json_dict = json.load(file)
			df["file_prefix"].append(file_prefix)
			df["unit_type"].append(json_dict["tipo_unidade"])
			df["marker"].append(json_dict["marker"])
			df["color"].append(json_dict["color"])
		df = pd.DataFrame(df)
		self.static_units_df = df
		return df

	def create_static_units(self):
		self.static_units_dict = dict()
		static_prefix_list = self.get_static_units_file_prefix_list()
		static_units_df = self.create_static_units_df(static_prefix_list)
		for index, row in static_units_df.iterrows():
			# creates the static units object
			self.static_units_dict[row.file_prefix] = static_units.StaticUnits(
				self.biomass_object.fig,
				self.biomass_object.ax,
				self.biomass_object.legend_fig,
				self.biomass_object.legend_ax,
				row.file_prefix,
				color=row.color,
				marker=row.color
			)




	def create_unit_checkboxes(self):
		self.unit_checkboxes_frame = tk.Frame(self, background="white")
		self.static_checkbox_var_dict = dict()
		self.static_checkbox_dict = dict()
		tk.Label(self.unit_checkboxes_frame, text="Unidades/Centros de consumo", background="white").grid(row=0,column=0)
		for index, row in self.static_units_df.iterrows():
			self.static_checkbox_var_dict[row.file_prefix] = tk.IntVar()
			self.static_checkbox_var_dict[row.file_prefix].set(1)
			self.static_checkbox_dict[row.file_prefix] = tk.Checkbutton(
				self.unit_checkboxes_frame,
				text=row.unit_type,
				variable=self.static_checkbox_var_dict[row.file_prefix],
				command=lambda x=row.file_prefix:
					self.change_static_unit_visibility(x),
				background="white"
			)
			self.static_checkbox_dict[row.file_prefix].grid(column=0, row=index+1)

	def change_static_unit_visibility(self, file_prefix):
		self.static_units_dict[file_prefix].change_visibility(
			visible=bool(self.static_checkbox_var_dict[file_prefix].get()), 
			uf=self.STATE_DICT[self.selected_state.get()]
		)
		self.update_fig_canvas()

	def update_static_units(self):
		for file_prefix in self.static_checkbox_var_dict.keys():
			self.change_static_unit_visibility(file_prefix)

		
	def change_biomass(self, file_prefix):
		self.biomass_object = biomass.BiomassMap(self.fig, self.legend_fig, file_prefix)
		self.create_static_units()
		self.update_static_units()
		self.change_source_label(self.biomass_object.source)
		self.state_selector_bbox.set("Brasil")
		self.update_fig_canvas()


app = App()
app.resizable(True, True)
app.mainloop()