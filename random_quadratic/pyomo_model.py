from pyomo.environ import (
    ConcreteModel, RangeSet, Param, Var,
    Objective, Constraint, Binary, Reals, minimize
)
import time
import pyomo.environ as pyo

model = ConcreteModel()

# ── Index sets ────────────────────────────────────────────────────────────────
model.D = RangeSet(2)   # indices for x (1..2)
model.I = RangeSet(2)   # disjunction index (1..2)
model.K = RangeSet(2)   # constraint index within each disjunct (1..2)

# ── Variables ─────────────────────────────────────────────────────────────────
model.x = Var(model.D, bounds=(-1,1), domain=Reals)
# One binary per disjunction: y[i]=1 ⇒ choose disjunct 1; y[i]=0 ⇒ choose disjunct 2
model.y = Var(model.I, domain=Binary)

# ── Objective parameters (from pprint) :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1} ─────────────────────
Q_dict = {
    (1,1):-0.18901742778001407, (1,2):  0.21944437071223033,
    (2,1): 0.21944437071223033, (2,2): -0.8945263378065618
}
c_dict = {1: 0.6723220643232408, 2: 0.03147874693807795}
d_val  = -0.5824991358001623

model.Q = Param(model.D, model.D, initialize=Q_dict)
model.c = Param(model.D, initialize=c_dict)
model.d = Param(initialize=d_val)

# ── Big‑M reformulation data :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3} ───────────────────────────────
Qc = {}
cc = {}
dc = {}
M  = {}

# Disjunction 1, disjunct 1, constraint 1
Qc.update({
    (1,1,1,1,1): -0.16409469668646204, (1,1,1,1,2):  0.33143684913094695,
    (1,1,1,2,1):  0.33143684913094695, (1,1,1,2,2): -0.48237749791978723,
})
cc.update({
    (1,1,1,1): -0.5322450478169161, (1,1,1,2):  0.7724443280821616,
})
dc[(1,1,1)] = -0.29450763397622176
M[(1,1,1)]  =  2.319527634790999

# Disjunction 1, disjunct 1, constraint 2
Qc.update({
    (1,1,2,1,1):  0.9251834955434677, (1,1,2,1,2):  0.7786576466932008,
    (1,1,2,2,1):  0.7786576466932008, (1,1,2,2,2):  0.5425063378458779,
})
cc.update({
    (1,1,2,1): -0.32156657064502103, (1,1,2,2):  0.26626665545945527,
})
dc[(1,1,2)] = -0.4559118471292294
M[(1,1,2)]  =  3.156926505750994

# Disjunction 1, disjunct 2, constraint 1
Qc.update({
    (1,2,1,1,1):  0.8795930681266637, (1,2,1,1,2):  0.1318672863216298,
    (1,2,1,2,1):  0.1318672863216298, (1,2,1,2,2): -0.3836330188277024,
})
cc.update({
    (1,2,1,1):  0.7797811115464033, (1,2,1,2): -0.2229733929141633,
})
dc[(1,2,1)] = -0.7097916077951609
M[(1,2,1)]  =  1.8199235562630314

# Disjunction 1, disjunct 2, constraint 2
Qc.update({
    (1,2,2,1,1): -0.7262492447984177, (1,2,2,1,2): -0.428395730527813,
    (1,2,2,2,1): -0.428395730527813, (1,2,2,2,2): -0.5070329909529503,
})
cc.update({
    (1,2,2,1): -0.28156245428511806, (1,2,2,2):  0.04459650007231608,
})
dc[(1,2,2)] =  0.2815255838820823
M[(1,2,2)]  =  2.6977582350465106

# Disjunction 2, disjunct 1, constraint 1
Qc.update({
    (2,1,1,1,1):  0.09160777014167998, (2,1,1,1,2): -0.6171581776834053,
    (2,1,1,2,1): -0.6171581776834053, (2,1,1,2,2):  0.7023859088989726,
})
cc.update({
    (2,1,1,1): -0.8951200947646678, (2,1,1,2):  0.9086389310138185,
})
dc[(2,1,1)] = -0.3294759940816933
M[(2,1,1)]  =  3.502593066104256

# Disjunction 2, disjunct 1, constraint 2
Qc.update({
    (2,1,2,1,1): -0.6475750698582767, (2,1,2,1,2):  0.6296725701830355,
    (2,1,2,2,1):  0.6296725701830355, (2,1,2,2,2): -0.5804469544587116,
})
cc.update({
    (2,1,2,1):  0.28965741246295695, (2,1,2,2): -0.5988525843541679,
})
dc[(2,1,2)] =  0.1798534219920506
M[(2,1,2)]  =  3.5557305834922346

# Disjunction 2, disjunct 2, constraint 1
Qc.update({
    (2,2,1,1,1): -0.9515352931535772, (2,2,1,1,2): -0.11232898357566368,
    (2,2,1,2,1): -0.11232898357566368, (2,2,1,2,2):  0.905184464638709,
})
cc.update({
    (2,2,1,1):  0.6242325373915671, (2,2,1,2): -0.2866525283991188,
})
dc[(2,2,1)] = -0.2736701516079182
M[(2,2,1)]  =  2.7185926391263813

# Disjunction 2, disjunct 2, constraint 2
Qc.update({
    (2,2,2,1,1):  0.7589627926408236, (2,2,2,1,2):  0.09380912422189358,
    (2,2,2,2,1):  0.09380912422189358, (2,2,2,2,2): -0.5076970559712244,
})
cc.update({
    (2,2,2,1):  0.2936326356947716, (2,2,2,2):  0.43869070726639614,
})
dc[(2,2,2)] = -0.23515757593339248
M[(2,2,2)]  =  1.9514438640836103

# Wrap into Pyomo Params
model.Qc   = Param(model.I, RangeSet(2), model.K, model.D, model.D, initialize=Qc)
model.cc   = Param(model.I, RangeSet(2), model.K, model.D,       initialize=cc)
model.dc   = Param(model.I, RangeSet(2), model.K,               initialize=dc)
model.bigM = Param(model.I, RangeSet(2), model.K,               initialize=M)

# ── Objective ────────────────────────────────────────────────────────────────
model.obj = Objective(
    expr = sum(model.Q[i,j]*model.x[i]*model.x[j]
               for i in model.D for j in model.D)
         + sum(model.c[i]*model.x[i] for i in model.D)
         + model.d,
    sense = minimize
)

# ── Big‑M constraints using y[i] for disjunct 1 and (1−y[i]) for disjunct 2 ──
def bigM_rule(m, i, j, k):
    quad = sum(m.Qc[i,j,k,p,q]*m.x[p]*m.x[q] for p in m.D for q in m.D)
    lin  = sum(m.cc[i,j,k,p]*m.x[p]             for p in m.D)
    const = m.dc[i,j,k]
    if j == 1:
        # Constraint active if y[i]=1; relaxed by M*(1−y[i]) when y[i]=0
        return quad + lin + const - m.bigM[i,1,k]*(1 - m.y[i]) <= 0
    else:
        # Constraint active if y[i]=0; relaxed by M*y[i] when y[i]=1
        return quad + lin + const - m.bigM[i,2,k]*m.y[i] <= 0

model.bigM_con = Constraint(model.I, RangeSet(2), model.K, rule=bigM_rule)


time_limit = 3600
#solver = "gurobi"
solver = "gams"

#Solve model
if solver == "gams":
    opt = pyo.SolverFactory("gams")

    options_gams = ("$onecho > gurobi.opt","NonConvex 2", "$offecho", ("GAMS_MODEL.optfile=1"))
    #options_gams = ("$onecho > gurobi.opt", "$offecho", ("GAMS_MODEL.optfile=1"))


    start = time.time()
    result = opt.solve(
        model,
        solver="gurobi",
        #tee=False,
        tee=True,
        symbolic_solver_labels=True,
        add_options=[
            f"option reslim={time_limit};",
            "option threads=1;",
            "option optcr=1e-6;",
            "option optca=0;",
            *options_gams,
        ],
    )
    #result = opt.solve(model, solver="gurobi", tee=True)

elif solver == "gurobi":

    # Create Gurobi solver directly
    opt = pyo.SolverFactory("gurobi")

    # Set Gurobi parameters
    # NonConvex=2 to handle non-convex quadratic problems
    opt.options["NonConvex"] = 2
    # Time limit
    opt.options["TimeLimit"] = time_limit
    # Use single thread
    opt.options["Threads"] = 1
    # Set relative optimality criterion (equivalent to optcr)
    opt.options["MIPGap"] = 1e-6
    # Set absolute optimality criterion (equivalent to optca)
    opt.options["MIPGapAbs"] = 0

    start = time.time()
    result = opt.solve(
        model,
        tee=True,
        symbolic_solver_labels=True,
    )




end = time.time()
duration = end - start

print(f"Time taken: {duration} seconds")
#objective value
print(f"Objective value: {model.obj()}")
