"""
csv file:
nome,uf,lat,lon

json file:
{
	"tipo": "copaenergia pross", "copaenergia arm", "domestico", "industrial", "comercial",  etc
	"unidade": "ton/mês", etc
}
"""
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import json

class StaticUnits:
	def __init__(self, fig, ax, df, specs_dict):
		"""
		fig: matplotlib.figure.Figure
		ax: matplotlib.axes.Axes
		unit_type: str
		file_prefix: str
		color: str
			must be accepted by matplotlib
		marker: str
			must be accepted by matplotlib
		

		csv file:
		nome,uf,lat,lon

		json file:
		{
			"tipo_unidade": "Unidade de processamento", "Unidade de armazenamento", etc
			"marker": "o", "*", https://matplotlib.org/stable/api/markers_api.html
			"color": HEX color
		}
		"""
		self.uf_list = ['RO', 'AC', 'AM', 'RR', 'PA', 'AP', 'TO', 'MA', 'PI', 'CE', 'RN', 'PB', 'PE', 'AL', 'SE', 'BA', 'MG', 'ES', 'RJ', 'SP', 'PR', 'SC', 'RS', 'MS', 'MT', 'GO', 'DF']
		self.path = "./static_units_files"
		self.fig = fig
		self.ax = ax
		
		self.unit_type = specs_dict["tipo_unidade"]
		self.marker = specs_dict["marker"]
		self.color = specs_dict["color"]

		self.unit_type = specs_dict["tipo_unidade"]
		self.marker = specs_dict["marker"]
		self.color = specs_dict["color"]

		self.df = df
		self.df["lat"] = pd.to_numeric(self.df["lat"])
		self.df["lon"] = pd.to_numeric(self.df["lon"])

		self.create_point_dict()



	def create_point_dict(self):
		self.point_dict = dict()
		for uf in self.df.uf.unique():
			self.point_dict[uf] = list()

		for index, row in self.df.iterrows():
			self.point_dict[row.uf].append(
				self.ax.scatter(row.lon, row.lat, color=self.color, marker=self.marker, zorder=2)
			)


	def change_visibility(self, visible, uf="Brasil"):
		for uf_name, point_list in self.point_dict.items():
			if uf_name == uf or uf == "Brasil":
				for point in point_list:
					# point is a matplotlib collection
					point.set(visible=visible)
			else:
				for point in point_list:
					# point is a matplotlib collection
					point.set(visible = False)