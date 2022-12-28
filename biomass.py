import json
import io
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from itertools import groupby
from operator import itemgetter

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

		self.biomass_df
		self.uf_df

		self.baseartist_dict
		self.baseoutline_dict
		self.artist_dict
		self.bbox_dict

		self.norm
		self.mappable
		self.cbar
	"""

	def __init__(self, fig, file_prefix):
		self.uf_list = ['RO', 'AC', 'AM', 'RR', 'PA', 'AP', 'TO', 'MA', 'PI', 'CE', 'RN', 'PB', 'PE', 'AL', 'SE', 'BA', 'MG', 'ES', 'RJ', 'SP', 'PR', 'SC', 'RS', 'MS', 'MT', 'GO', 'DF']

		fig.clear()
		ax = fig.add_subplot(111)
		self.fig = fig
		self.ax = ax


		self.ax.set_aspect("0.9")
		self.ax.axis("off")
		self.cmap = matplotlib.cm.get_cmap("Oranges")

		
		self.read_json_file(file_prefix)
		self.create_dfs(file_prefix)
		self.create_basemap()
		self.create_baseoutline()
		self.read_bbox()
		self.create_map()
		self.create_colorbar("Brasil")



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
		try:
			self.norm_type = json_dict["norm"]  # "linear" ou "log"
		except KeyError:
			self.norm_type = "linear"

		try:
			self.obs = json_dict["obs"]
		except KeyError:
			self.obs = ""



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

		biomass_df = pd.read_csv(f"{biomass_path}/{file_prefix}.csv")
		biomass_df = biomass_df.drop("uf", axis=1)

		map_df = pd.read_json(f"{map_path}/{self.region_type}.json")
		map_df = map_df.loc[map_df.cod_ibge.isin(biomass_df.cod_ibge)]
		map_df = map_df.reset_index(drop=True)

		self.biomass_df = pd.merge(biomass_df, map_df, on="cod_ibge")
		self.biomass_df = self.biomass_df.loc[self.biomass_df.qnt_produzida > 0]
		self.uf_df = pd.read_json(f"{map_path}/uf.json")

		# biomass_df.columns: ['cod_ibge', 'qnt_produzida', 'ano', 'nome', 'uf', 'macro', 'geometry']
		# uf_df.columns: ['cod_ibge', 'nome', 'uf', 'macro', 'geometry']



	def update_norm(self, uf):
		if uf == "Brasil":
			new_vmax = self.biomass_df.qnt_produzida.max()
			new_vmin = self.biomass_df.qnt_produzida.min()
		else:
			new_vmax = self.biomass_df.loc[self.biomass_df["uf"] == uf].qnt_produzida.max()
			new_vmin = self.biomass_df.loc[self.biomass_df["uf"] == uf].qnt_produzida.min()

		if pd.isna(new_vmax):
			new_vmin = 1
			new_vmax = 10

		if self.norm_type == "linear":
			self.norm = matplotlib.colors.Normalize(vmin=0, vmax=new_vmax)
		elif self.norm_type == "log":
			self.norm = matplotlib.colors.LogNorm(vmin=new_vmin, vmax=new_vmax)



	def create_basemap(self):
		self.baseartist_dict = dict()
		if self.norm_type == "linear":
			basemap_color = self.cmap(0)
		elif self.norm_type == "log":
			basemap_color = "white"

		for index, row in self.uf_df.iterrows():
			self.baseartist_dict[row.uf] = self.ax.fill(
				*row.geometry,
				color=basemap_color
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
		self.artist_dict is a dict with uf's as keys
		the value for each key is a list that contains artists
		*There might be some uf's out of the dict*
		"""
		self.ax.set_title(f"Produção de {self.biomass_name}")
		self.artist_dict = dict()  
		self.update_norm("Brasil")

		for index, row in self.biomass_df.iterrows():
			artist_color = self.cmap( self.norm(row.qnt_produzida) )
			artist = self.ax.fill(
				*row.geometry,
				url=row.cod_ibge,
				color=artist_color,
				edgecolor="grey",
				linewidth=0.1
			)[0]  # fill() method returns a list, so the [0] is needed to get the artist object
			
			try:
				self.artist_dict[row.uf].append(artist)
			except KeyError:
				self.artist_dict[row.uf] = [artist]
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
		self.baseartist_dict[uf].set_visible(visible)
		self.baseoutline_dict[uf].set_visible(visible)
		
		if uf in self.artist_dict.keys():
			for artist in self.artist_dict[uf]:
				artist.set_visible(visible)

	def update_color(self, uf):
		"""
		artist: str
		vmin = int or float
		vmax = int or float
		"""
		self.update_norm(uf)
		if uf == "Brasil":
			for artist_list in self.artist_dict.values():
				for artist in artist_list:
					cod_ibge = artist.get_url()
					# If there is more than one cod_ibge in the DataFrame, the line below will cause an error, check your DataFrame
					artist_value = float (self.biomass_df.loc[self.biomass_df.cod_ibge == cod_ibge].qnt_produzida)
					new_color = self.cmap(self.norm(artist_value))
					artist.set(color=new_color, edgecolor="grey", linewidth=0.1)

		elif uf in self.artist_dict.keys():
			artist_list = self.artist_dict[uf]
			for artist in artist_list:
				cod_ibge = artist.get_url()
				# If there is more than one cod_ibge in the DataFrame, the line below will cause an error, check your DataFrame
				artist_value = float (self.biomass_df.loc[self.biomass_df.cod_ibge == cod_ibge].qnt_produzida)
				new_color = self.cmap(self.norm(artist_value))
				artist.set(color=new_color, edgecolor="grey", linewidth=0.1)


	def change_uf(self, uf):
		self.resize_ax(uf)
		self.update_colorbar(uf)
		self.update_color(uf)
		
		if uf == "Brasil":
			# Show all
			for uf_key in self.uf_list:
				self.change_visibility(uf_key, visible=True)

		# Not "Brasil":
		else:
			# Hide all
			for uf_key in self.uf_list:
				self.change_visibility(uf_key, visible=False)
			# Show selected uf
			self.change_visibility(uf, visible=True)



	def create_colorbar(self, uf):
		self.update_norm(uf)
		self.mappable = matplotlib.cm.ScalarMappable(norm=self.norm, cmap=self.cmap)

		fig, ax = plt.subplots()
		fig.colorbar(
    		self.mappable,
    		orientation='vertical',
		).set_label(label=f" Produção de {self.biomass_name} ({self.unit})", labelpad=5)
		ax.remove()

		cbar_array = self.fig_to_array(fig)
		self.cbar_array = self.remove_white_spaces(cbar_array)

	def fig_to_array(self, fig):
		io_buf = io.BytesIO()
		fig.savefig(io_buf, format='raw')
		io_buf.seek(0)
		img_arr = np.reshape(np.frombuffer(io_buf.getvalue(), dtype=np.uint8),
                     newshape=(int(fig.bbox.bounds[3]), int(fig.bbox.bounds[2]), -1))
		io_buf.close()
		return np.array(img_arr)

	def fix_list(self,lst):
		lst = sorted(lst)
		for i in range(len(lst)):
			if lst[i] + 1 != lst[i+1]:
				fim_comeco = i
				break
		lst = lst[::-1]
		for i in range(len(lst)):
			if lst[i] - 1 != lst[i+1]:
				comeco_fim = len(lst) - i
				break
		lst = lst[::-1]
		return lst[:fim_comeco+1] + lst[comeco_fim:]

	def remove_white_spaces(self, img_arr):
		# Remove horizontal white lines
		hor_indexes = list()
		for idx, line in enumerate(img_arr):
			if self.white_line(line):
				hor_indexes.append(idx)
		hor_indexes = self.fix_list(hor_indexes)
		img_arr = np.delete(img_arr, hor_indexes, 0)

		# Remove vertical white lines
		img_arr = np.transpose( img_arr, (1,0,2) )
		ver_indexes = list()
		for idx, line in enumerate(img_arr):
			if self.white_line(line):
				ver_indexes.append(idx)

		ver_indexes = self.fix_list(ver_indexes)
		img_arr = np.delete(img_arr, ver_indexes, 0)

		img_arr = np.transpose( img_arr, (1,0,2) )
		return img_arr
 


	def white_line(self, line):
		line = np.array(line)
		len_line = len(line)
		if np.array_equal( line , np.array([[255, 255, 255, 255] for _ in range(len(line))]) ):
			return True

		elif np.array_equal(line[:, 3] , [0 for _ in range(len(line))]):
			return True

		else:
			return False

	def update_colorbar(self, uf):
		self.create_colorbar(uf)		

	def resize_ax(self, uf):
		bbox = self.bbox_dict[uf]
		self.ax.set_xlim( [bbox[0][0], bbox[1][0]] )  # [x_min, x_max]
		self.ax.set_ylim( [bbox[0][1], bbox[1][1]] )  # [y_min, y_max]