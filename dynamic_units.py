import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import io
from itertools import groupby
from operator import itemgetter

class DynamicUnits:
	def __init__(self, fig, ax, legend_fig, legend_ax, df, specs_dict):
		"""
		fig and legend_fig: matplotlib.figure.Figure
		ax and legend_ax: matplotlib.axes.Axes
		unit_type: str
		
		df:
		nome,uf,lat,lon,coef

		specs_dict:
		{
			"tipo_unidade": "Centros de consumo", etc
			"unidade": "ton/mês", "ton/ano", etc
			"marker": "o", "*", https://matplotlib.org/stable/api/markers_api.html
			"cmap": "GnBu", etc
		}
		"""

		self.fig = fig
		self.ax = ax
		self.legend_fig = legend_fig
		self.legend_ax = legend_ax
		self.df = df
		self.fix_df()

		self.specs_dict = specs_dict
		self.marker = specs_dict["marker"]
		self.unit_type = specs_dict["tipo_unidade"]

		self.cmap = matplotlib.cm.get_cmap(self.specs_dict["cmap"])
		self.create_colorbar(n_divisions=5)
		self.create_units()

	def fix_df(self):
		self.df["lat"] = pd.to_numeric(self.df["lat"])
		self.df["lon"] = pd.to_numeric(self.df["lon"])
		self.df["coef"] = pd.to_numeric(self.df["coef"])

	def get_boundaries(self, uf="Brasil", n_divisions=5):
		if uf == "Brasil":
			df_max = self.df["coef"].max()
		else:
			df_max = self.df.loc[self.df.uf == uf]["coef"].max()
		
		if pd.isna(df_max):
			df_max = self.df["coef"].max()
	

		sci = np.format_float_scientific(df_max)
		
		sig, pot = sci.split("e")  # Example: sci = 1.4257e+05; sig = "1.4257"; pot = "+05"
		
		pot = 10**(float(pot))

		if len(sig) > 3 and int(sig[3]) < 3:
			sig = sig[:3]
			# if sig = 1.42 -> sig = 1.4
		
		elif len(sig) > 2:
			sig = sig[:2] + str(int(sig[2]) + 1)
			# if sig = 1.44 -> sig = 1.5

		sig = float(sig)

		boundary_max = sig * pot

		boundaries = np.linspace(start=0, stop=boundary_max, num=n_divisions)
		return boundaries


	def create_colorbar(self, uf="Brasil", n_divisions=5):
		self.norm = matplotlib.colors.BoundaryNorm(self.get_boundaries(uf=uf, n_divisions=n_divisions), self.cmap.N, extend='neither')
		self.mappable = matplotlib.cm.ScalarMappable(norm=self.norm, cmap=self.cmap)
		
		fig, ax = plt.subplots()
		ax.axis('off')
		fig.colorbar(
			self.mappable,
			orientation='vertical',
			use_gridspec=True,
		).set_label(f"{self.specs_dict['tipo_unidade']} ({self.specs_dict['unidade']})", labelpad=5)

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



	def update_colorbar(self, uf_selected):
		self.create_colorbar(uf=uf_selected)

	def create_units(self):
		self.units_dict = dict()
		for idx, row in self.df.iterrows():
			self.units_dict[row["nome"]] = self.ax.scatter(
				row.lon,
				row.lat,
				color=self.cmap(self.norm(row["coef"])),
				marker=self.specs_dict["marker"],
				zorder=3,
				s=20
			)

	def change_visibility(self, uf, visible):
		self.update_colorbar(uf)
		
		if uf == "Brasil":
			for idx, row in self.df.iterrows():
				self.units_dict[row["nome"]].set_color(self.cmap(self.norm(row["coef"])))
				self.units_dict[row["nome"]].set_visible(visible)
		else:
			for idx, row in self.df.iterrows():
				if row["uf"] == uf:
					self.units_dict[row["nome"]].set_visible(visible)
					self.units_dict[row["nome"]].set_color(self.cmap(self.norm(row["coef"])))

				else:
					self.units_dict[row["nome"]].set_visible(False)


