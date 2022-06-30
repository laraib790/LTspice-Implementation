"""
        EE2703 Applied Programming Lab - 2022
            Assignment 2: Solution of SPICE PART2
            By LARAIB HASSAN ( EE20B070)

"""
from sys import argv, exit
import numpy as np
from numpy import cos,sin
#importing necessry libraries

CIRCUIT = '.circuit'
END = '.end'
AC = '.ac' 
#Using variables so as to avoid hardcoding

if len(argv) != 2:
    # Checking for number of command line arguments. If two arguments are not given
    print("Invalid number of arguments")
    exit()

class Sources():
    # Class for all elements/componenets contained in the circuit and finding out ac/dc types by checking w(omega), values etc.

    def __init__(self,line):
        self.line = line
        self.tokens = self.line.split() #getting tokens 
        self.name = element(self.tokens[0]) # element function returning the name of element
        #Or we could have just used the symbol of the elemenet instead of using element fuction if we didnt want the full name.

        # Getting nodes
        self.from_node = self.tokens[1] # 2nd letter = from node
        self.to_node = self.tokens[2] # 3rd letter = to node

        if len(self.tokens) == 5: # corresponds to dc
            self.type = 'dc' 
            self.value = float(self.tokens[4])

        elif len(self.tokens) == 6: # corresponds to ac 
            self.type = 'ac' 
            mag = float(self.tokens[4])/2
            phase = float(self.tokens[5])
            real = mag*cos(phase)
            imag = mag*sin(phase)
            self.value = complex(real,imag)  #writing value in complex form
        else:
            self.type = 'RLC' # R L C and Independent sources
            self.value = float(self.tokens[3])


def extract_circuit(Lines):
 # function to extract circuit definition start and end lines ignoring comments

    Start = -1; End = -2;c = 0
    for line in Lines:             
        if CIRCUIT == line[:len(CIRCUIT)]:
            Start = Lines.index(line)# first time when .circuit appeared
            c+=1# keeping a count to reject unaccepatable circuits
        elif END == line[:len(END)]:
            End = Lines.index(line)# first time when .end appeared
            break

    if (Start >= End) or (c!=1):  
            # validating circuit block
            print('Invalid circuit definition')
            exit(0)

    Actual_lines = Lines[Start+1:End]
    withoutComment = []
    for line in Actual_lines:
        withoutComment.append(line.split('#')[0])
    return withoutComment
   #Overall this function checks for correct circuit block and returns lines(tokens) to be processed further
     

def element(word):
   #Function to check the first letter of each line (token) and finding the type of element 
   #R L C Independent voltage and current sources

    if word[0] == 'R':
        return 'Resistor'
    elif word[0] == 'L':
        return 'Inductor'
    elif word[0] == 'C':
        return 'Capacitor'
    elif word[0] == 'V':
        return 'Independent Voltage Source'
    elif word[0] == 'I':
        return 'Independent Current Source'

def freq(lines):
# Function to get frequency of the source
    w = 0 # setting it to zero for dc cases
    for line in lines:
        if line[:len(AC)] == '.ac' : #slicing the line and extracting frequency value
            w = float(line.split()[2]) # After getting w , we can calculate omega whenever necessary
    return w


def Nodes_dict(circuit):
# Function to create dictionary of nodes present in the circuit

    nodes_dict = {} # empty dictionary to store nodes
    nodes = [Sources(line).from_node for line in circuit]  #adding from nodes to the list
   
    nodes.extend([Sources(line).to_node for line in circuit])  # adding to nodes to the end of the list.

    node_number = 1
    nodes = list(set(nodes)) # getting table of distinct nodes by using set command
    for node in nodes:
        if node == 'GND' :
            nodes_dict[node] = 0 # Given GRD = 0
        else :
            nodes_dict[node] = node_number
            node_number = node_number + 1
    return nodes_dict


def create_dict(circuit,element):
    #Makes a dictionary for each component of the particular type of element 
    e = element
    dict = {}
    names = [Sources(line).tokens[0] for line in circuit if Sources(line).tokens[0][0]== e]
    for index,name in enumerate(names):
        dict[name] = index
    return dict

def key(nodes_dict,value):
    for key in nodes_dict.keys(): #itterarting through all keys in dictionary
        if nodes_dict[key] == value : #matching key with value
            return key # returning the key to use while printing result

def get_node(circuit,node_key,nodes_dict):
    # This function is used to find the index of nodes(position of to and from node)
    indexs = [(i,j) for i in range(len(circuit)) for j in range(len(circuit[i].split())) if circuit[i].split()[j] in nodes_dict.keys() if nodes_dict[circuit[i].split()[j]] == node_key]
    return indexs


def matrix(circuit,w,node_key,nodes_dict,voltage_dict,inductor_dict,M,b):
    # Filling / Updating M and b matrix

    indices = get_node(circuit,node_key,nodes_dict)

    volt_ind = [i for i in range(len(circuit)) if circuit[i].split()[0][0] == 'V']
    k = len(volt_ind) # number of voltage sources
    n = len(Nodes_dict(circuit)) # number of nodes
    # n+k to get dimensions of the M and b matrices

    for idc in indices:
        # Collecting attributes of elements
        element = Sources(circuit[idc[0]])
        element_name = circuit[idc[0]].split()[0]

        if element_name[0] == 'R': # filling values if the element is resistor
            if idc[1] == 1:  #node is the from_node
                n2_key = nodes_dict[element.to_node]  # getting the stamp/position of to node
                M[node_key,node_key] += 1/(element.value) #1/r that is conductance
                M[node_key,n2_key] -= 1/(element.value)
                    
            if idc[1] == 2 :  #node is to_node
                n1_key = nodes_dict[element.from_node] # getting the stamp/position of from node
                M[node_key,node_key] += 1/(element.value) #1/r that is conductance
                M[node_key,n1_key] -= 1/(element.value)
                
        if element_name[0] == 'C' : # filling values if the element is capacitor
            if idc[1]== 1:
                # node is the from_node
                n2_key = nodes_dict[element.to_node]  # getting the stamp/position of to node
                M[node_key,node_key] += complex(0, 2*np.pi*w*(element.value))#omega * c
                M[node_key,n2_key] -= complex(0, 2*np.pi*w*(element.value))

            if idc[1] == 2 :
                # node is the to_node
                n1_key = nodes_dict[element.from_node] # getting the stamp/position of from node
                M[node_key,node_key] += complex(0, 2*np.pi*w*(element.value)) #omega * c
                M[node_key,n1_key] -= complex(0, 2*np.pi*w*(element.value))

        if element_name[0] == 'L' : # filling values if the element is inductor
                if idc[1]== 1:
                    n2_key = nodes_dict[element.to_node] # getting the stamp/position of to node
                    M[node_key,node_key] -= complex(0,1/(2*np.pi*w*element.value))#1/omega*L
                    M[node_key,n2_key] += complex(0,1/(2*np.pi*w*element.value))

                if idc[1] == 2 :
                    n1_key = nodes_dict[element.from_node] # getting the stamp/position of from node
                    M[node_key,node_key] -= complex(0,1/(2*np.pi*w*element.value)) #1/omega*L
                    M[node_key,n1_key] += complex(0,1/(2*np.pi*w*element.value))

        if element_name[0] == 'V' : # filling values if the element is voltage source

            i= voltage_dict[element_name] # getting index of voltage element
            if idc[1]== 1:
               
                M[node_key,n+i] += 1
                M[n+i,node_key] -= 1
                b[n+i] = element.value #updating b matrix
                
            if idc[1] == 2 :
               
                M[node_key,n+i] -= 1
                M[n+i,node_key] +=1
                b[n+i] = element.value #updating b matrix

        if element_name[0] == 'I' : # filling values if the element is current source

            if idc[1]== 1:
                b[node_key] -= element.value #updating b matrix
            if idc[1] == 2 :
                b[node_key] += element.value #updating b matrix


# Main Function
try:
    ckt_file = argv[1]
    #Checking if the file is of correct type or not
    if (not ckt_file.endswith(".netlist")):
        print("Wrong file type!")
    else:
        with open (ckt_file, "r") as f:
            lines = f.readlines()
            f.close()

            circuit = extract_circuit(lines) # getting lines useful in the circuit defination after removing commnets
            w = freq(lines) #frequency
            nodes_dict = Nodes_dict(circuit) # stores nodes in dictionary . Its length will give value of n
            
            voltage_dict = create_dict(circuit,'V') # stores voltage nodes in dictionary
            inductor_dict = create_dict(circuit,'L') # stores nodes in dictionary
        
            volt_ind = [i for i in range(len(circuit)) if circuit[i].split()[0][0] == 'V']
            k = len(volt_ind)
            n = len(Nodes_dict(circuit)) 
           

            M = np.zeros((n+k,n+k),dtype=complex)  #creating M matrix which will be updated later on
            b = np.zeros(n+k,dtype=complex) #creating b matrix

            for i in range(len(nodes_dict)):
                matrix(circuit,w,i,nodes_dict,voltage_dict,inductor_dict,M,b) #calling the function to get the required matrix
            M[0] = 0 
            M[0,0] = 1 #filling up the space for ground node
            print(' M = \n',M)
            print(' b = \n',b)
           
           
            try:
                x = np.linalg.solve(M,b)
            except Exception:
                print("The matrix Can't be solved")
                exit()

            print('x = \n',x)
            for i in range(n): #printing node voltages
                print("voltage at {}= {}".format(key(nodes_dict,i),x[i]))
        
            for j in range(k): #printing current through sources
                print("current through {} = {}".format(key(voltage_dict,j),x[n+j]))

# if the file could not be found
except IOError:
    print('Invalid file')
    exit()


