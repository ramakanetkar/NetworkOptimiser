# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 22:09:04 2020

@author: milind
"""

import os
import pandas as pd
import numpy as np
import mysql.connector
import json

def getDBCreds(path):
    SQLCreds = open(path,'r')
    creds = {}
    lcreds = list(SQLCreds.readlines())

    for c in lcreds:
        l = c.split(':')
        creds[l[0]] =l[1].replace('\n','')
    return creds

def makeform(root, fields):
   entries = {}
   for field in fields:
      row = Frame(root)
      lab = Label(row, width=25, text=field+": ", anchor='w')
      ent = Entry(row)
      ent.insert(0,"")
      row.pack(side = TOP, fill = X, padx = 25 , pady = 5)
      lab.pack(side = LEFT)
      ent.pack(side = RIGHT, expand = YES, fill = X)
      entries[field] = ent
   return entries

def ModifyTable(entries, Dbobject):
       # period rate:
   r = (float(entries['Customer'].get()) / 100) / 12
   print("r", r)
   # principal loan:
   loan = float(entries['Rate'].get())
   n = float(entries['Location'].get())
   remaining_loan = float(entries['Comments'].get())
   q = (1 + r)** n
   monthly = r * ( (q * loan - remaining_loan) / ( q - 1 ))
   monthly = ("%8.2f" % monthly).strip()
   entries['Flow'].delete(0,END)
   entries['Flow'].insert(0, monthly )
   print("Flow: %f" % float(monthly))

DBCreds = getDBCreds('C:/Users/DELL/Desktop/NetOp/SQLCreds.txt')

nodb = mysql.connector.connect(
  host=DBCreds['host'],
  user=DBCreds['user'],
  password=DBCreds['password'],
  database =DBCreds['database']
)

CustomerRate = pd.read_sql("SELECT * FROM CustomerLanes", nodb)
#print (CustomerRate)
Demand = pd.read_sql("SELECT * FROM Demand", nodb)
#print (Demand)
Location = pd.read_sql("SELECT * FROM Location", nodb)
#print (Location)
Product = pd.read_sql("SELECT * FROM Product", nodb)
#print (Product)
Customer = pd.read_sql("SELECT * FROM Customer", nodb)
#print (Customer)

from pyomo.environ import *
model = ConcreteModel()

#Set Declaration
#Location
model.location = Set(initialize = Location['Location'], doc = 'Location')
#Customer
model.customer = Set(initialize = Customer['Customer'], doc = 'Customer')
#Product
model.product = Set(initialize = Product['Product'], doc = 'Product')

dict1 = {}

for i in model.location:
    for j in model.customer:
        for k in model.product:
            dict1.update({(i,j,k) : float(CustomerRate['Rate'][(CustomerRate['Location'] == i) & (CustomerRate['Customer'] == j)].to_string(index=False))})
model.CustomerLaneCost = Param(model.location,model.customer,model.product, initialize = dict1, doc = 'Transportation cost from Location to Customer')

dict2 = {}
for i in model.customer:
    for j in model.product:
        dict2.update({(i,j): float(Demand['DemandUnits'][(Demand['Customer'] == i) & (Demand['Product'] == j)].to_string(index = False))})
model.demand = Param(model.customer,model.product, initialize = dict2, doc = 'Customer demand')

model.x1 = Var(model.location,model.customer,model.product, bounds = (0.0, None), doc = 'Outbound Lanes')

def demand_rule(model, customer,product):
    return sum(model.x1[i,customer,product] for i in model.location) >= model.demand[customer,product]
model.demandrule = Constraint(model.customer,model.product, rule = demand_rule, doc= 'Satisfy demand at customer for a given prouct')


def objective_rule(model):
    return  sum(model.CustomerLaneCost[location,customer,product]*model.x1[location,customer,product] for location in model.location for customer in model.customer for product in model.product)
model.objective = Objective(rule = objective_rule, sense = minimize, doc = 'Objective Function')


from pyomo.opt import SolverFactory
import pyomo.environ
opt = SolverFactory("glpk")
results = opt.solve(model)
results.write()
print("\nDisplaying Solution\n" + '-'*60)
model.x1.display()


result_dict = dict(model.x1)
cursor = nodb.cursor()
 
for k1,v1 in result_dict.items():
    sql = 'UPDATE no.customerlanes set flow = ' + str(v1.value) + ' where location = \'' + str(k1[0]) + '\' and customer = \'' + str(k1[1]) + '\' and product = \'' + str(k1[2]) + '\';'
    cursor.execute(sql)
    nodb.commit()
    print('Row Updated')
print('Table updated')



#cursor = nodb.cursor()
#sql ='Update customerlanes set flow = 0;'
#cursor.execute(sql)
#print ('Flows nulled')

