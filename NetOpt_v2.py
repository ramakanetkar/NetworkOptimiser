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
from pyomo.environ import *
from tkinter import *
from pyomo.opt import SolverFactory
import pyomo.environ

def getDBCreds(path):
    SQLCreds = open(path,'r')
    creds = {}
    lcreds = list(SQLCreds.readlines())

    for c in lcreds:
        l = c.split(':')
        creds[l[0]] =l[1].replace('\n','')
    return creds

def RunpyomoModel(entries,DBObject):
    CustomerRate = pd.read_sql("SELECT * FROM CustomerLanes", DBObject)
    #print (CustomerRate)
    Demand = pd.read_sql("SELECT * FROM Demand", DBObject)
    #print (Demand)
    Location = pd.read_sql("SELECT * FROM Location", DBObject)
    #print (Location)
    Product = pd.read_sql("SELECT * FROM Product", DBObject)
    #print (Product)
    Customer = pd.read_sql("SELECT * FROM Customer", DBObject)
    #print (Customer)
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
    
    opt = SolverFactory("glpk")
    results = opt.solve(model)
    results.write()
    print("\nDisplaying Solution\n" + '-'*60)
   # model.x1.display()
    
    result_dict = dict(model.x1)
    cursor = DBObject.cursor()
 
    for k1,v1 in result_dict.items():
        sql = 'UPDATE no.customerlanes set flow = ' + str(v1.value) + ' where location = \'' + str(k1[0]) + '\' and customer = \'' + str(k1[1]) + '\' and product = \'' + str(k1[2]) + '\';'
        cursor.execute(sql)
        DBObject.commit()
    print('Table Updated')
    entries['Comments'].delete(0,END)
    entries['Comments'].insert(0, 'Run Successful')


def makeform(root, fields):
   entries = {}
   root.title("Pyomo Model")
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

def GetValues(entries, DBObject):
    cust = entries['Customer'].get()
    loc = entries['Location'].get()
    prod = entries['Product'].get()
    sqlstmt = 'SELECT * FROM no.CustomerLanes where location = \'' + str(loc) + '\' and customer = \'' + str(cust)+ '\' and product = \'' + str(prod)+ '\';'
    result = pd.read_sql(sqlstmt,DBObject)
    if result.empty:
        entries['Comments'].delete(0,END)
        entries['Comments'].insert(0, 'No record found')
    else:
        entries['Rate'].delete(0,END)
        entries['Rate'].insert(0, result['Rate'].values[0])
        entries['Flow'].delete(0,END)
        if result['flow'].values[0] == None:
            entries['Flow'].insert(0, 'Null')
            entries['Comments'].delete(0,END)
            entries['Comments'].insert(0, 'Run model to get Flow')
        else:
            entries['Flow'].insert(0, result['flow'].values[0])
            entries['Comments'].delete(0,END)
            entries['Comments'].insert(0, 'Data Extracted')
    
def ModifyTable(entries,DBObject):
    def properRate(number):
        try:
            float(number)
            return True
        except ValueError:
            return False
    cust = entries['Customer'].get()
    loc = entries['Location'].get()
    prod = entries['Product'].get()
    r = entries['Rate'].get()
    if r.strip() =="" or cust.strip()=="" or loc.strip() =="" or prod.strip()=="" :
        entries['Comments'].delete(0,END)
        entries['Comments'].insert(0, 'Values missing')
    else:
        if properRate(r):
            cursor = DBObject.cursor()
            sqlstmt = 'SELECT * FROM no.CustomerLanes where location = \'' + str(loc) + '\' and customer = \'' + str(cust)+ '\' and product = \'' + str(prod)+ '\';'
            result = pd.read_sql(sqlstmt,DBObject)
            if result.empty:
                entries['Comments'].delete(0,END)
                entries['Comments'].insert(0, 'Inserts not handled yet')
            else:
                sql = 'UPDATE no.customerlanes set flow = null, Rate = ' + str(r) + ' where location = \'' + str(loc) + '\' and customer = \'' + str(cust) + '\' and product = \'' + str(prod) + '\';'
                cursor.execute(sql)
                DBObject.commit()
                entries['Comments'].delete(0,END)
                entries['Comments'].insert(0, 'Records updated')
        else:
            entries['Comments'].delete(0,END)
            entries['Comments'].insert(0, 'Invalid rate')
    
            
        
    
if __name__ == '__main__':
    DBCreds = getDBCreds('C:/Users/DELL/Desktop/NetOp/SQLCreds.txt')
    nodb = mysql.connector.connect(
            host=DBCreds['host'],
            user=DBCreds['user'],
            password=DBCreds['password'],
            database =DBCreds['database']
            )
        
    fields = ('Customer', 'Location', 'Product','Rate', 'Flow', 'Comments') 
    root = Tk()
    ents = makeform(root, fields)
    root.bind('<Return>', (lambda event, e = ents: fetch(e)))
    b1 = Button(root, text = 'Get value',command=(lambda e = ents, d = nodb: GetValues(e,d)))
    b1.pack(side = LEFT, padx = 5, pady = 25)
    b2 = Button(root, text='Insert / Update',command=(lambda e = ents, d = nodb: ModifyTable(e,d)))
    b2.pack(side = LEFT, padx = 5, pady = 25)
    b3 = Button(root, text = 'Run Model', command=(lambda e = ents, d = nodb: RunpyomoModel(e,d)))
    b3.pack(side = LEFT, padx = 5, pady = 25)
    root.mainloop()