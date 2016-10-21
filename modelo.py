# -*- coding: cp1252 -*-
from pyomo.core import *
from pyomo.environ import *
from math import log,e
infinity = float('inf')

model = AbstractModel()

#Sets
model.tecnologias = Set(ordered=True)
model.tecnologias.construct()
model.fallas = Set()
model.fallas.construct()
model.hidrologias = Set()
model.tecnologias2 = model.tecnologias|model.fallas

#Parameters
model.dmax = Param()
model.T = Param()
model.alpha = Param()
model.constInt = Param() #constante de la integral
model.k = Param() #constante de la exponencial
model.enerTot = Param()
model.cvar = Param(model.tecnologias2, within=NonNegativeReals)
model.cf = Param(model.tecnologias2)
model.pond = Param(model.hidrologias)

#Variables
#Investment
model.inv = Var(model.tecnologias2, initialize=0, within=NonNegativeReals)
#Generation
model.gen = Var(model.tecnologias2, model.hidrologias, initialize=0, within=NonNegativeReals)
#Times
model.tiempo = Var(model.tecnologias, model.hidrologias, bounds=(0,model.T), initialize=0, within=NonNegativeReals)
#Energy
model.energia = Var(model.tecnologias2, model.hidrologias, initialize=0, within=NonNegativeReals)

#Supersets
#order1
def orden_rule(model, tec):
        lista = list(model.tecnologias)
        blo = []
        for i,tecnologia in enumerate(model.tecnologias):
                if (tecnologia==tec and tecnologia!=hidro):
                        blo.append(lista[0:i])
                elif (tecnologia==tec and tecnologia==hidro):
                        blo.append(lista[0])
        return blo
model.arr_orden = Set(ordered=True, initialize=orden_rule)
#order2
def orden2_rule(model, tec):
        lista = list(model.tecnologias)
        blo = []
        for i,tecnologia in enumerate(model.tecnologias):
                if (tecnologia==tec and tecnologia!=hidro):
                        blo.append(lista[i-1])
                elif (tecnologia==tec and tecnologia==hidro):
                        blo.append(lista[0])
        return blo
model.arr_orden2 = Set(ordered=True, initialize=orden2_rule)

#Objective function
def cost_rule(model):
        #costos de inversión
        value = sum(model.inv[i]*model.cf[i] for i in model.tecnologias2)
        #costos de operación/generación
        value += sum(model.energia[i,j]*model.cvar[i] \
                     for i in model.tecnologias2 \
                     for j in model.hidrologias)
        return value
model.totCost = Objective(rule=cost_rule, sense=minimize)

#Constraints
#restricción: balance de demanda
def balance_rule(model, hidrologia):
        value = sum(model.energia[i,hidrologia] for i in model.tecnologias2)
        return value==model.enerTot
model.balance = Constraint(model.hidrologias, rule=balance_rule)
#restricción: acoplamiento de tecnologías
def acopTec_rule(model, tec):
        return model.inv[tec]>=sum(model.inv[i] for i in model.arr_orden2[tec])
model.acopTec = Constraint(model.tecnologias2, rule=acopTec_rule)
#restricción: acoplamiento de tiempos
def acopTiempos_rule(model, tec, hidrologia):
        return model.tiempo[tec,hidrologia]>=sum(model.tiempo[i,hidrologia] for i in model.arr_orden2[tec])
model.acopTiempos = Constraint(model.tecnologias, model.hidrologias, rule=acopTiempos_rule)
#restricción: potencias máximas
def maxPot_rule(model, tec, hidrologia):
        return model.gen[tec,hidrologia]<=model.inv[tec]
model.maxPot = Constraint(model.tecnologias2, model.hidrologias, rule=maxPot_rule)
#restricción: asociación tiempos con potencias
def asocPotTiempo_rule(model, tec, hidrologia):
        value = (model.T/model.alpha)*log(model.dmax/sum(model.gen[i,hidrologia] for i in model.arr_orden[tec]))
        return model.tiempo[tec,hidrologia]==value
model.asocPotTiempo = Constraint(model.tecnologias, model.hidrologias, rule=asocPotTiempo_rule)
#restricción: definición energías
def asocEnergia_rule(model, tec, hidrologia):
        value = model.gen[tec,hidrologia]*model.tiempo[tec,hidrologia]
        value2 = 0
        value3 = 0
        if tec==hidro:
                value2 = e**(model.k*model.tiempo[tec,hidrologia]) - e**(model.k*model.T)
                value3 = 0
        elif tec==fa:
                value2 = 1-sum(e**(model.k*model.tiempo[i,hidrologia] for i in model.arr_orden2[tec]))
                value3 = sum(model.gen[i,hidrologia] for i in model.arr_orden[tec])* \
                         sum(model.tiempo[i,hidrologia] for i in model.arr_orden2[tec])
        else:
                value2 = sum(e**(model.k*model.tiempo[i,hidrologia]) for i in model.arr_orden2[tec])- \
                 e**(model.k*model.tiempo[tec,hidrologia])
                value3 = sum(model.gen[i,hidrologia] for i in model.arr_orden[tec])* \
                         (sum(model.tiempo[i,hidrologia] for i in model.arr_orden2[tec])- \
                          model.tiempo[tec,hidrologia])
        value += model.constInt*value2
        value -= value3
        return model.energia[tec,hidrologia]==value
model.asocEnergia = Constraint(model.tecnologias2, model.hidrologias, rule=asocEnergia_rule)
