#!/usr/bin/python3

from jinja2 import *
from jinja2.exceptions import TemplateNotFound

warning = "THIS FILE IS GENERATED FROM TEMPLATE. DON'T MODIFY IT"

class EDescriptionError(Exception):
	pass

def load_yaml_values(filename):
	import yaml

	with open(filename, 'r') as stream:
		data = yaml.load(stream)
	return data

class Exporter:

	def __init__(self, outputdir):
		self.outputdir = outputdir
		if outputdir and outputdir[-1]!='/':
			self.outputdir += '/'
		self.dtslist = []
		self.products = {}
		self.boards = {}

	def get_name(self, id, prefix="", slot=None):
		if slot==None:
			return "%s%04x" % (prefix, id)
		return "%s%04x-slot%d" % (prefix, id, slot)
		
	def write(self, name, content):
		with open(self.outputdir+name, 'w') as f:
			f.write(content)

	def writedts(self, name, content):
		self.write(name+".dts", content)
		self.dtslist.append(name+".dts")

	def add_product(self, id, name):
		try:
			self.products[str(id)] += " " + name
		except KeyError:
			self.products[str(id)] = name

	def add_board(self, id, slot, name):
		key = "%s.%d" % (id,slot)
		try:
			subdict = self.boards[str(id)]
		except KeyError:
			subdict = {}
			self.boards[str(id)] = subdict
		try:
			subdict[str(slot)] += " " + name
		except KeyError:
			subdict[str(slot)] = name


def gener_by_desc(description, uniee_data, jinjaenv, exporter):

	data_platform = uniee_data["platform"]["id"]
	for product, p_desc in description["product"].items():
		try:
			p_id = data_platform[product]
		except KeyError as E:
			raise EDescriptionError('Invalid value for product name "%s"'% product) from None

		if not isinstance(p_desc, dict): continue
		t = jinjaenv.get_template(name=p_desc["template"])
		result = t.render(id=p_id)
		ename = exporter.get_name(p_id, prefix="bb")
		exporter.writedts(ename, result)
		exporter.add_product(p_id, ename)

	data_board = uniee_data["board"]["model"]
	for board, b_desc in description["board"].items():
		try:
			b_id = data_board[board]
		except KeyError as E:
			raise EDescriptionError('Invalid value for board name "%s"'% board) from None
		prefix = board[:2].lower()

		if not isinstance(b_desc, dict): continue
		t = jinjaenv.get_template(name=b_desc["template"])
		for slot in b_desc["slot"]:
			params = description["slot"][str(slot)]
			result = t.render(id=b_id, slot=slot, **params)
			ename = exporter.get_name(b_id, prefix=prefix, slot=slot)
			exporter.writedts(ename, result)
			exporter.add_board(b_id, slot, ename)


def gener_library(jinjaenv, uniee_data, exporter):
	t = jinjaenv.get_template(name="unipi-values.template.c")
	result = t.render(product_dt=exporter.products, board_dt=exporter.boards, **uniee_data)
	with open("unipi-values.c", 'w') as f:
		f.write(result)

def gener_makefile(jinjaenv, exporter):
	t = jinjaenv.get_template(name="Makefile.template")
	result = t.render(dtslist=exporter.dtslist)
	exporter.write("Makefile", result)


if __name__ == "__main__":
	import argparse, sys
	a = argparse.ArgumentParser(prog='render-slot.py')
	a.add_argument('description', metavar="file", help='input yaml description', type=str, nargs=1)
	a.add_argument('-d','--data', metavar="file", help='uniee_values data yaml')
	a.add_argument('-t','--templates', metavar="directory", help='Template directory')
	a.add_argument('-o','--output', metavar="directory", help='Output directory')
	args = a.parse_args()
	datafile = args.data if args.data else "unipi-hardware-id/values/uniee_values.yaml"
	templates = args.templates if args.templates else "template"

	loader=FileSystemLoader(searchpath=templates)
	jinjaenv = Environment(loader=loader)

	outdir = args.output if args.output else "overlays"
	exporter = Exporter(outdir)

	uniee_data = load_yaml_values(datafile)

	description = load_yaml_values(args.description[0])
	try:
		gener_by_desc(description, uniee_data, jinjaenv, exporter)
		gener_makefile(jinjaenv, exporter)
		gener_library(jinjaenv, uniee_data, exporter)
		sys.exit(0)

	except EDescriptionError as E:
		print(str(E))
	except TemplateNotFound as E:
		print('TemplateError: %s not found' % str(E))
	sys.exit(1)