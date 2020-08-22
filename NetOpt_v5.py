# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 19:30:00 2020

@author: DELL
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

def popupmsg(msg):
    popup = Tk()
    NORM_FONT = ("Helvetica", 10)
    popup.wm_title("Error")
    label = Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)
    B1 = Button(popup, text="Okay", command = popup.destroy)
    B1.pack()
    popup.mainloop()

def getDBCreds(path):
    SQLCreds = open(path,'r')
    creds = {}
    lcreds = list(SQLCreds.readlines())
    SQLCreds.close()
    for c in lcreds:
        l = c.split(':')
        creds[l[0]] =l[1].replace('\n','')
    return creds

def saveDBCreds(path,h,u,p,d):
    credFile = open(path,'w')
    writeText='host:' + h + '\n' + 'user:' + u + '\n' + 'password:' + p + '\n' + 'database:' + d + '\n'
    credFile.write(writeText)
    credFile.close()

def validateDBCreds(entries):
    ihost = entries['Host'].get()
    iuser = entries['User'].get()
    ipasswordCode = entries['Password'].get()
    idb = entries['DB'].get()
    ipassword=''
    if ihost.strip()=="" or iuser.strip()=="" or ipasswordCode.strip()=="" or idb.strip()=="":
        popupmsg('Invalid Entry!!')
    else:
        if ipasswordCode.replace("*","").strip()=="":
            SQLFile = getDBCreds('C:/Users/DELL/Desktop/NetOp/SQLCreds.txt')
            ipassword = SQLFile['password']
        else:
            ipassword = passwordCode
        try:
            nodb = mysql.connector.connect(host=ihost,user=iuser,password=ipassword,database =idb)
            saveDBCreds('C:/Users/DELL/Desktop/NetOp/SQLCreds.txt',ihost,iuser,ipassword,idb)
            return nodb
        except:
            popupmsg('Login Failed!!!')    
   
def getTotalValues(db):
    sqlstmt = '''select sum(demandUnits) total_demand , total.total_served, total.total_cost 
             from no.demand 
             cross join (select sum(flow) total_served, sum(rate*flow) total_cost
                       from no.customerlanes) total '''
    total_result = result = pd.read_sql(sqlstmt,db)
    return total_result

def RunpyomoModel(entries, entries1):
    DBObject = validateDBCreds(entries)
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
                dict1.update({(i,j,k): float(CustomerRate['Rate'][(CustomerRate['Location'] == i) & (CustomerRate['Customer'] == j) & (CustomerRate['Product'] == k)].to_string(index=False))})
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
    model.x1.display()
    
    result_dict = dict(model.x1)
    stats = model.compute_statistics
    print(stats)
    cursor = DBObject.cursor()
 
    for k1,v1 in result_dict.items():
        sql = 'UPDATE no.customerlanes set flow = ' + str(v1.value) + ' where location = \'' + str(k1[0]) + '\' and customer = \'' + str(k1[1]) + '\' and product = \'' + str(k1[2]) + '\';'
        cursor.execute(sql)
        DBObject.commit()
    print('Table Updated')
    
    modelResults = getTotalValues(DBObject)
    if modelResults.empty:
        entries1['Total Demand Amount'].delete(0,END)
        entries1['Total Demand Amount'].insert(0, 'No record found')
        entries1['Total Amount served'].delete(0,END)
        entries1['Total Amount served'].insert(0, 'No record found')
        entries1['Total cost to serve'].delete(0,END)
        entries1['Total cost to serve'].insert(0, 'No record found')
    else:
        entries1['Total Demand Amount'].delete(0,END)
        entries1['Total Demand Amount'].insert(0,modelResults['total_demand'].values[0])
        entries1['Total Amount served'].delete(0,END)
        entries1['Total Amount served'].insert(0,modelResults['total_served'].values[0])
        tCost = modelResults['total_cost'].values[0]
        formattedtCost = '$' + "{:.2f}".format(tCost)
        entries1['Total cost to serve'].delete(0,END)
        entries1['Total cost to serve'].insert(0,formattedtCost)


def makeform(root, fields,fieldvalues,x):
   entries = {}
   #root.title("Network Optimiser")
   for i in range(len(fields)):
      row = Frame(root)
      lab = Label(row, width=25, text=fields[i]+": ", anchor='w')
      ent = Entry(row)
      ent.insert(0,fieldvalues[i])
      row.pack(side = TOP, fill = X, padx = x , pady = 15)
      lab.pack(side = LEFT)
      ent.pack(side = RIGHT, expand = YES, fill = X)
      entries[fields[i]] = ent
   return entries

if __name__ == '__main__':
    fields = ('Host', 'User', 'Password','DB')
    fieldvalues = ('localhost','root','*********','no')
    root = Tk()
    root.title('Network Optimiser')
    root.geometry('500x510')
    topFrame = Frame(root, width=500, height=200,highlightbackground="black", highlightcolor="black", highlightthickness=1)
    topFrame.pack(side=TOP)
    topLabel = Label(topFrame,text='Login Details:                                                                                                   ', justify=LEFT, font=10)
    topLabel.pack(side=TOP)
    ents = makeform(topFrame,fields,fieldvalues,25)
    middleFrame = Frame(root, width=500, height=50,highlightbackground="black", highlightcolor="black", highlightthickness=1)
    middleFrame.pack(side=TOP)
    middleFrameLeft = Frame(middleFrame, width = 160,height=50,highlightbackground="black", highlightcolor="black", highlightthickness=1)
    middleFrameLeft.pack(side=LEFT)
    b1 = Button(middleFrameLeft, text = 'Connect & save', width=15, height=3,command=(lambda e = ents: validateDBCreds(e)))
    b1.pack(side = LEFT, padx = 5, pady = 5)
    middleFrameCenter = Frame(middleFrame, width = 160,height=50)
    middleFrameCenter.pack(side=LEFT)
    rb1 = Radiobutton(middleFrameCenter, text='Minimize Costs', width=15, height=1,value=1, state=ACTIVE)
    rb1.select()
    rb1.pack(side = TOP)
    rb2 = Radiobutton(middleFrameCenter, text='Maximize Profits', width=15, height=1,value=2, state=DISABLED)
    rb2.pack(side = TOP)
    middleFrameRight = Frame(middleFrame, width = 160,height=50)
    middleFrameRight.pack(side=LEFT)
    labelFrame =Frame(root,width=500, height=25,highlightbackground="black", highlightcolor="black", highlightthickness=1)
    labelFrame.pack(side=TOP)
    bottomLabel = Label(labelFrame,text='ModelResults:                                                     Model Stats:                        ', justify=LEFT, font=10)
    bottomLabel.pack(side=LEFT)
    bottomFrame =Frame(root,width=500, height=225,highlightbackground="black", highlightcolor="black", highlightthickness=1)
    bottomFrame.pack(side=TOP)
    modelresult = Frame(bottomFrame,width=500, height=250)
    modelresult.pack(side=LEFT)
    results = ('Total Demand Amount','Total Amount served','Total cost to serve')
    resultvalues =('--','--','--')
    ents1 = makeform(modelresult,results,resultvalues,5)
    modelstats = Frame(bottomFrame,width=500, height=250)
    modelstats.pack(side=LEFT)
    txt = Text(modelstats)
    txt.pack(fill=BOTH, pady=5, padx=5, expand=True)
    b3 = Button(middleFrameRight, text = 'Run Model', width=15, height=3, command=(lambda e = ents, e1= ents1: RunpyomoModel(e,e1)))
    b3.pack(side = LEFT, padx = 5, pady = 5)
    root.mainloop()