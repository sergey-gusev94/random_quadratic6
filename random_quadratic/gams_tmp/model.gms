$offlisting
$offdigit

EQUATIONS
	capacity_hi
	obj;

BINARY VARIABLES
	x_1_
	x_2_
	x_3_;

VARIABLES
	GAMS_OBJECTIVE
	;


capacity_hi.. 5*x_1_ + 3*x_2_ + 4*x_3_ =l= 9 ;
obj.. GAMS_OBJECTIVE =e= 10*x_1_ + 6*x_2_ + 7*x_3_ ;


MODEL GAMS_MODEL /all/ ;
option mip=gurobi;
option solprint=off;
option limrow=0;
option limcol=0;
option solvelink=5;

* START USER ADDITIONAL OPTIONS

s
o
l
v
e
l
o
g
=
1
;

* END USER ADDITIONAL OPTIONS

SOLVE GAMS_MODEL USING mip minimizing GAMS_OBJECTIVE;

Scalars MODELSTAT 'model status', SOLVESTAT 'solve status';
MODELSTAT = GAMS_MODEL.modelstat;
SOLVESTAT = GAMS_MODEL.solvestat;

Scalar OBJEST 'best objective', OBJVAL 'objective value';
OBJEST = GAMS_MODEL.objest;
OBJVAL = GAMS_MODEL.objval;

Scalar NUMVAR 'number of variables';
NUMVAR = GAMS_MODEL.numvar

Scalar NUMEQU 'number of equations';
NUMEQU = GAMS_MODEL.numequ

Scalar NUMDVAR 'number of discrete variables';
NUMDVAR = GAMS_MODEL.numdvar

Scalar NUMNZ 'number of nonzeros';
NUMNZ = GAMS_MODEL.numnz

Scalar ETSOLVE 'time to execute solve statement';
ETSOLVE = GAMS_MODEL.etsolve


file results /'results.dat'/;
results.nd=15;
results.nw=21;
put results;
put 'SYMBOL  :  LEVEL  :  MARGINAL' /;
put x_1_ ' ' x_1_.l ' ' x_1_.m /;
put x_2_ ' ' x_2_.l ' ' x_2_.m /;
put x_3_ ' ' x_3_.l ' ' x_3_.m /;
put capacity_hi ' ' capacity_hi.l ' ' capacity_hi.m /;
put obj ' ' obj.l ' ' obj.m /;
put GAMS_OBJECTIVE ' ' GAMS_OBJECTIVE.l ' ' GAMS_OBJECTIVE.m;

file statresults /'resultsstat.dat'/;
statresults.nd=15;
statresults.nw=21;
put statresults;
put 'SYMBOL   :   VALUE' /;
put 'MODELSTAT' ' ' MODELSTAT /;

put 'SOLVESTAT' ' ' SOLVESTAT /;

put 'OBJEST' ' ' OBJEST /;

put 'OBJVAL' ' ' OBJVAL /;

put 'NUMVAR' ' ' NUMVAR /;

put 'NUMEQU' ' ' NUMEQU /;

put 'NUMDVAR' ' ' NUMDVAR /;

put 'NUMNZ' ' ' NUMNZ /;

put 'ETSOLVE' ' ' ETSOLVE /;
