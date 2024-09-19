import statistics
from sympy import And, Or, Not
import numpy as np
from sympy.logic.boolalg import is_cnf
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute
from qiskit.circuit.library import XGate, ZGate
from qiskit.circuit import Gate
from typing import List, Callable

"""
Sorts a list of atoms of a sympy logical formula in alphabetical order

Args: 
    atoms_listed (list): List of sympy's logical formula atoms
Returns: 
    list: List of alphabetically sorted sympy's logical formula atoms
    
"""

def sort_atoms(atoms:list)-> list:
    return (sorted(atoms,key=str))


"""
Identifies which qubits are implyed in a serie of disjunctions and their their state of control in the MCX Gate. 
A serie of disjunctions are analysed and the variables impliated in this clause are associated with their corresponding qubit index

Args: 
    atoms (list): All of the variables of the general proposition orded following their qubit index
    disjonction_formula (Or): Sympy logical formula composed of literals and disjunctions

Returns:
    controls (list): The indexes of the qubits implied in the disjounction formula.
    control_states (string): The state of which the control qubits need to be verified. It follow the litte-indian
                            convention (the qubit at index 0 of the controls list is associated with the number on the 
                            far right of the control_states string) .
"""

def MCX_Gate_controls(atoms:list,disjonction_formula:Or)->(list,str):
    controls=[]
    control_states=""

    for litteral in disjonction_formula.args:
        if isinstance(litteral,Not):
            control_states="1"+control_states
        else:
            control_states="0"+control_states
        controls.append(atoms.index(list(litteral.atoms())[0]))

    return controls, control_states



"""
Builds the gate representing the cnf formula entered.

Args:
    sorted_atoms (list): The atoms of the logical formula alphabetically ordered
    num_of_vars (int): Number of variables in the logical formula
    num_of_anc (int): Number of ancillary qubit needed to build the gate (number of clauses)
    cnf_formula (And): Cnf logical formula 
    reverse (bool): If true, the circuit that composes the gate will be reversed

Returns: Gate: the quantum gate that represents the cnf logical formula
"""

def build_formula_gate(sorted_atoms:list,num_of_vars:int,num_of_anc:int,cnf_formula:And,reverse:bool)->Gate:
    varreg= QuantumRegister(num_of_vars, "v")
    ancreg=QuantumRegister(num_of_anc, "a")
    formula_circuit=QuantumCircuit(varreg,ancreg)

    clause_index=0
    
    #Conversion of the logical formula to a circuit
    for disjunction_formula in cnf_formula.args:
        controls, control_states=MCX_Gate_controls(sorted_atoms,disjunction_formula)
        
        MCX_Gate=XGate().control(len(controls),ctrl_state=control_states)
        formula_circuit.append(MCX_Gate,varreg[controls]+ancreg[clause_index:clause_index+1])

        clause_index=clause_index+1
    
    #To respect De Morgan's law
    formula_circuit.x(ancreg)

    if reverse==True:
        formula_circuit.inverse()

    formula_gate=formula_circuit.to_gate(label="logical formula")
    return formula_gate



"""
Builds the oracle door for a Grover algorithm

Args:
    cnf_formula: Cnf logical formula

Returns:
    Gate: Grover's algorithm oracle of the cnf logical formula
"""

def cnf_to_oracle(cnf_formula: And) -> Gate: 
    #Sorted list of the variables
    unsorted_vars=list(cnf_formula.atoms())
    vars=sort_atoms(unsorted_vars)

    #Determination of the number of ancillary qubits
    num_of_vars=len(vars)
    num_of_anc=len(cnf_formula.args)

    varreg= QuantumRegister(num_of_vars, "v")
    ancreg=QuantumRegister(num_of_anc, "a")
    oracle_circuit=QuantumCircuit(varreg,ancreg)
  
    oracle_circuit.append(build_formula_gate(vars,num_of_vars,num_of_anc,cnf_formula,False),varreg[:]+ancreg[:])

    #Flipping the phase of the valid elements
    oracle_circuit.append(ZGate().control(num_of_anc-1),ancreg)
    
    #Inversely reconverting the circuit
    oracle_circuit.append(build_formula_gate(vars,num_of_vars,num_of_anc,cnf_formula,True),varreg[:]+ancreg[:])

    oracle_quantum_gate=oracle_circuit.to_gate(label="Oracle")
    return oracle_quantum_gate


"""
Builds the Grover's algorithm diffuser

Args: 
    num_of_vars (int): Number of variable in the cnf logical formula
Sortie: 
    Gate: The quantum gate of the correct amount of qubits of the Grover's algorithm diffuser
"""

def build_diffuser(num_of_vars: int) -> Gate:
    qreg= QuantumRegister(num_of_vars, "q")
    diffuser_circuit = QuantumCircuit(qreg)

    diffuser_circuit.h(qreg)
    diffuser_circuit.x(qreg)
    diffuser_circuit.append(ZGate().control(num_of_vars-1),qreg)
    diffuser_circuit.x(qreg)
    diffuser_circuit.h(qreg)

    diffuser_quantum_gate=diffuser_circuit.to_gate(label="Diffuser")
    
    return diffuser_quantum_gate



"""
Builds Grover's algorithm circuit of a specific oracle

Args: 
    oracle (Gate): Cnf logical formula's associated Grover's algorithm Oracle gate
    num_of_vars (int): Number of variables in the cnf logical formula
    num_iters (int): Number of iterations of Grover's algorithm
Returns: 
    QuantumCircuit: Grover's algorithm circuit associated with a specific oracle

"""

def build_grover_circuit(oracle: Gate, num_of_vars: int, num_iters: int) -> QuantumCircuit: 
    nb_of_anc=oracle.num_qubits-num_of_vars
    varreg= QuantumRegister(num_of_vars, "v")
    ancreg=QuantumRegister(nb_of_anc, "a")
    creg=ClassicalRegister(num_of_vars, "c")
    grover_circuit = QuantumCircuit(varreg,ancreg,creg)

    grover_circuit.h(varreg)
    
    diffuser=build_diffuser(num_of_vars)
    for iteration in range(num_iters):
        grover_circuit.append(oracle,varreg[:]+ancreg[:])
        grover_circuit.append(diffuser,varreg)

    for variable_index in range(num_of_vars):
        grover_circuit.measure(varreg[variable_index],creg[variable_index])

    return grover_circuit


"""
Creates a list of the meaningful results out of the mutilples shots of Grover's algorithm.
    A meaningful output has a frequency greater than the sum of the mean and standard deviation of all of the frequencies observed.
Args:
    execution_results (dict): The dictionnary  of all of the output values of the differents shots of execution and their associated frequency

Returns
    list: All of the meaningful outputs of the execution of the circuit

"""

def get_meaningful_outputs(execution_results:dict)-> list:
    
    mean=sum(execution_results.values())/len(execution_results)
    sd=statistics.stdev(execution_results.values())
    results=[]
    for output, number_of_measurments in execution_results.items():
        if(number_of_measurments > (mean + sd)):
            results.append(output)
    return results



"""
Creates the list of the solutions of Grover's algorithm out of the good results.

Args:
    good_outputs(list): All of the meaningful outputs of the circuit that need to be included in the solution
    sorted_atoms (list): Sorted list of all of the variables in the logical formula analysed
Returns:
    list: Multiple dictionnaries of the thruth value of each variable of the meaningful outputs
"""

def build_dictionnary_state_of_vars(good_outputs:list, sorted_atoms: list)-> list:
    solution=[]
    for combination in good_outputs:
        states_of_vars={key:None for key in sorted_atoms}

        index=0
        for truth_value_var in reversed(combination):
            if truth_value_var=="0":
                states_of_vars[sorted_atoms[index]]=False
            else:
                states_of_vars[sorted_atoms[index]]=True
            index=index+1
        solution.append(states_of_vars)
    
    return solution


"""
Solves a cnf logical formula with Grover's algorithm
Args: 
    logical_formula (And): logical formula to analyse withe Grover's algorithm. Needs to be cnf to pass through the assert.
    logical_formula_to_oracle (Callable): Function building Grover's algorithm oracle door out of a logical formula
    backend: The place the quantum circuit needs to be run (simulator or on a QPU)
Returns: 
    solution List[dict]: The solution of Grover's algorithm (the truth value of every variable for each possible outputs) 
"""

def solve_sat_with_grover(logical_formula: And, logical_formula_to_oracle: Callable, backend) -> List[dict]:
    
    if(is_cnf(logical_formula)):
        sorted_atoms=sort_atoms(list(logical_formula.atoms()))
        optimal_number_of_iterations=int(np.floor(np.pi*0.25*np.sqrt(2**len(sorted_atoms))))   #Formula calculationg the ideal number of iterations needed
        
        oracle = logical_formula_to_oracle(logical_formula)
        job = execute(build_grover_circuit(oracle,len(list(logical_formula.atoms())),optimal_number_of_iterations), backend, shots =10000)
        execution = job.result().get_counts()
        
        good_results=get_meaningful_outputs(execution)

        solution=build_dictionnary_state_of_vars(good_results,sorted_atoms)

        return solution
    
    else:
        print("The formula is not a cnf and can not be solved with Grover's algorithm.")
        solution=["error"]
        return solution


"""
Checks if the meaningful results of the Grover algorithm are valid

Args:
    logical_formula (And): Logical formula to verify the validity of the outputs
    results (List[dict]): Results of the solve_sat_with_grover function
Returns:
    bool: If True, the results are valid
"""   

def solution_check(logical_formula:And, results: List[dict])-> bool:
    truth_value=True

    for solution in results:
         if logical_formula.subs(solution)==False:
            truth_value=False

    return truth_value