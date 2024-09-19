import Grover
from sympy import symbols
from sympy.logic.boolalg import to_cnf
from qiskit_aer import AerSimulator

backend=AerSimulator()

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"Pincus"

#Variables
x1,x2,x3,x4=symbols("x1,x2,x3,x4")
#Affirmations
A1=(x1|x4|x3)
A2=(~x1|x4|x2)
A3=(x3|~x4|x2)
A4=(~x2|x4|~x3)
A5=(~x1|x3|~x2)
A6=(x2|~x3|x1)
A7=(~x1|~x4|~x3)
pincus=A1 & A2 & A3 & A4 & A5 & A6 & A7
#Grover's algorithm
results=Grover.solve_sat_with_grover(pincus,Grover.cnf_to_oracle,backend)
print("Pincus solutions")
print("Are the results valid: ",Grover.solution_check(pincus,results))
print(results)

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"Cake"
#Variables
Xa,Xb,Xc,Xd,Xe= symbols("Xa,Xb,Xc,Xd,Xe")
#Affirmations
Pa=((~Xe & ~Xb)|(Xe & Xb))
Pb=((~Xc & Xe)|(Xc & ~Xe))
Pc=((Xe & Xa)|(~Xe & ~Xa))
Pd=((Xc & ~Xb)|(~Xc & Xb))
Pe=((Xd & Xa)|(~Xd & ~Xa))
cake = Pa & Pb & Pc & Pd & Pe
#Grover's algorithm
cnf_cake=to_cnf(cake, simplify=True)
results=Grover.solve_sat_with_grover(cnf_cake,Grover.cnf_to_oracle, backend)
print("")
print("Cake solutions")
print("Are the results valid: ",Grover.solution_check(cnf_cake,results))
print(results)


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"Original proposition"

#Variables
a,b,c,d= symbols("a,b,c,d")
#Affirmation
P1=(a|b)
P2=(~a|b|c)
P3=(~a|~b|~c)
P4=(b|d|a)
P5=(~a|b|~d)
P6=(a|~c|d)
invented_proposition=P1&P2&P3&P4&P5&P6
#Grover's algorithm
results=Grover.solve_sat_with_grover(invented_proposition,Grover.cnf_to_oracle,backend)
print("")
print("Original proposition solutions")
print("Are the results valid: ",Grover.solution_check(invented_proposition,results))
print(results)