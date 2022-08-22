import json
import numpy as np
import pandas as pd
import matplotlib
from matplotlib.colors import LogNorm

class BiomassMap:
	"""
	All attributes:
		self.fig
		self.ax
		self.cmap
		
		self.uf_list
		self.biomass_name
		self.biomass_type
		self.unit
		self.region_type
		self.derived_product
		self.derived_coef
		self.gas_coef
		self.source

		self.artist_df
		self.uf_df

		self.basemap_dict
		self.baseoutline_dict
		self.map_dict
		self.bbox_dict

		self.norm
		self.mappable
		self.cbar
	"""

	def __init__(self, fig, legend_fig, file_prefix=None):
		self.uf_list = ['RO', 'AC', 'AM', 'RR', 'PA', 'AP', 'TO', 'MA', 'PI', 'CE', 'RN', 'PB', 'PE', 'AL', 'SE', 'BA', 'MG', 'ES', 'RJ', 'SP', 'PR', 'SC', 'RS', 'MS', 'MT', 'GO', 'DF']

		fig.clear()
		ax = fig.add_subplot(111)
		self.fig = fig
		self.ax = ax

		legend_fig.clear()
		legend_ax = legend_fig.add_subplot(111)
		legend_ax.axis("off")
		self.legend_fig = legend_fig
		self.legend_ax = legend_ax

		self.ax.set_aspect("0.8")
		self.ax.axis("off")
		self.cmap = matplotlib.cm.get_cmap("GnBu")

		if file_prefix is None:  # if the biomass is not specified creates an empty map
			self.uf_df = pd.read_json("./map_files/geometry/uf.json")  # This path is hardcoded on purpose
			self.create_basemap()
			self.create_baseoutline()

		else:
			self.read_json_file(file_prefix)
			self.create_dfs(file_prefix)
			self.create_basemap()
			self.create_baseoutline()
			self.read_bbox()
			self.create_map()
			self.create_colorbar()
			self.update_colorbar(vmax=self.artist_df.qnt_produzida.max())

	def read_json_file(self, file_prefix):
		"""
		file_prefix: str
			There should be file_prefix.csv and file_prefix.json inside the biomass folder
		"""
		biomass_path = "./biomass"
		with open(f"{biomass_path}/{file_prefix}.json", "r", encoding="utf-8") as file:
			json_dict = json.load(file)

		self.biomass_name = json_dict["nome_biomassa"]
		self.biomass_type = json_dict["tipo_biomassa"]
		self.unit = json_dict["unidade"]
		self.region_type = json_dict["tipo_regiao"]
		self.derived_product = json_dict["produto_derivado"]
		self.derived_coef = json_dict["conversao_derivado"]
		self.gas_coef = json_dict["conversao_gas"]
		self.source = json_dict["fonte"]

	def create_dfs(self, file_prefix):
		"""
		The self.read_json_file(file_prefix) method must be executed before this one
		The csv file must have the following columns:
			- cod_ibge
			- uf
			- qnt_produzida
		"""
		biomass_path = "./biomass"
		map_path = "./map_files/geometry"

		artist_df = pd.read_csv(f"{biomass_path}/{file_prefix}.csv")
		artist_df = artist_df.drop("uf", axis=1)

		map_df = pd.read_json(f"{map_path}/{self.region_type}.json")
		map_df = map_df.loc[map_df.cod_ibge.isin(artist_df.cod_ibge)]
		map_df = map_df.reset_index(drop=True)

		self.artist_df = pd.merge(artist_df, map_df, on="cod_ibge")
		self.artist_df = self.artist_df.loc[self.artist_df.qnt_produzida > 0]
		self.uf_df = pd.read_json(f"{map_path}/uf.json")

	def create_basemap(self):
		self.basemap_dict = dict()
		for index, row in self.uf_df.iterrows():
			self.basemap_dict[row.uf] = self.ax.fill(
				*row.geometry,
				color="white"
			)[0]  # fill() method returns a list, so the [0] is needed to get the artist object
	
	def create_baseoutline(self):
		self.baseoutline_dict = dict()
		for index, row in self.uf_df.iterrows():
			self.baseoutline_dict[row.uf] = self.ax.plot(
				*row.geometry,
				color="black",
				linewidth=0.5
			)[0]  # plot() method returns a list, so the [0] is needed to get the artist object

	def create_map(self):
		"""
		self.map_dict is a dict with uf's as keys
		the value for each key is a list that contains artists
		*There might be some uf's out of the dict*
		"""
		self.ax.set_title(f"Produção de {self.biomass_name}")
		self.map_dict = dict()  # Could also be called artist_dict
		vmin = self.artist_df.qnt_produzida.min()
		vmax = self.artist_df.qnt_produzida.max()
		log_norm = LogNorm(vmin=vmin, vmax=vmax)
		for index, row in self.artist_df.iterrows():
			artist = self.ax.fill(
				*row.geometry,
				url=row.cod_ibge,
				color=self.cmap(log_norm(row.qnt_produzida)),
				edgecolor="grey",
				linewidth=0.1
			)[0]  # fill() method returns a list, so the [0] is needed to get the artist object
			
			try:
				self.map_dict[row.uf].append(artist)
			except KeyError:
				self.map_dict[row.uf] = [artist]
		self.resize_ax("Brasil")

	def read_bbox(self):
		# Each value of the dict follows: [[x_min, y_min], [x_max, y_max]]
		with open(f"map_files/bbox.json", "r", encoding="utf-8") as file:
			self.bbox_dict = dict( json.load(file) )

	def change_visibility(self, uf, visible):
		"""
		uf: str
		visible: bool
		"""
		self.basemap_dict[uf].set_visible(visible)
		self.baseoutline_dict[uf].set_visible(visible)
		
		if uf in self.map_dict.keys():
			for artist in self.map_dict[uf]:
				artist.set_visible(visible)

	def update_color(self, uf, vmin=10**0, vmax=10**1):
		"""
		artist: str
		vmin = int or float
		vmax = int or float
		"""
		if uf in self.map_dict.keys():
			for artist in self.map_dict[uf]:
				cod_ibge = artist.get_url()
				# If there is more than one cod_ibge in the DataFrame, the line below will cause an error, check your DataFrame
				artist_value = float (self.artist_df.loc[self.artist_df.cod_ibge == cod_ibge].qnt_produzida)
				if artist_value > vmax: print("vmax should be greater or equal to the artist_value")  # Error message
				log_norm = LogNorm(vmin=vmin, vmax=vmax)
				new_color = self.cmap( log_norm(artist_value) )
				artist.set(color=new_color, edgecolor="grey", linewidth=0.1)

	def change_uf(self, uf):
		self.resize_ax(uf)
		
		if uf == "Brasil":
			# Show all
			new_vmax = self.artist_df.qnt_produzida.max()
			new_vmin = self.artist_df.qnt_produzida.min()
			self.update_colorbar(vmin=new_vmin, vmax=new_vmax)

			for uf_key in self.uf_list:
				self.change_visibility(uf_key, visible=True)
				self.update_color(uf_key, vmin=new_vmin, vmax=new_vmax)

		# Not "Brasil":
		else:
			new_vmax = self.artist_df.loc[self.artist_df.uf == uf].qnt_produzida.max()
			new_vmin = self.artist_df.loc[self.artist_df.uf == uf].qnt_produzida.min()
			self.update_colorbar(vmin=new_vmin, vmax=new_vmax)

			# Hide all
			for uf_key in self.uf_list:
				self.change_visibility(uf_key, visible=False)

			# Show and update the colors of the selected uf
			self.change_visibility(uf, visible=True)
			self.update_color(uf, vmin=new_vmin, vmax=new_vmax)


	
	def create_colorbar(self, vmin=10**0, vmax=10**1):
		self.norm = LogNorm(vmin=vmin, vmax=vmax)
		self.mappable = matplotlib.cm.ScalarMappable(norm=self.norm, cmap=self.cmap)

		self.cbar = self.legend_fig.colorbar(
    		self.mappable,
    		orientation='vertical',
    		label=f"Produção ({self.unit})"
		)

	def update_colorbar(self, vmin=10**0, vmax=10**1):
		if pd.isna(vmin):
			vmin = 10**0
		if pd.isna(vmax):
			vmax = 10**1
		if vmin == vmax:
			vmax += 1
		self.mappable.set_clim(vmin=vmin, vmax=vmax)
		

	def resize_ax(self, uf):
		bbox = self.bbox_dict[uf]
		self.ax.set_xlim( [bbox[0][0], bbox[1][0]] )  # [x_min, x_max]
		self.ax.set_ylim( [bbox[0][1], bbox[1][1]] )  # [y_min, y_max]