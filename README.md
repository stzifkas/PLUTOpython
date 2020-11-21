# GSoC 2019 Work Product: PLUTO DSL in Python

Sample code for my GSoC 2019 proposal

## Itroduction 

Developing an open source parser for PLUTO that can read PLUTO scripts as input and generate valid Python 3 code from the script.
project is based on modeling Space System Models. In order to achieve this goal, we have to implement a library of classes according to the ECSS‐E‐ST‐70‐31C standard. This means separate classes for different types of Activities, Reporting Data, Events, Space Systems. Also we have to create classes for Types, both built-in and defined by user

## Static Analysis

From a static point of view, we have to keep track of the different systems (subsystems, parts etc.) and the relationships between them. A way to do this is by declaring a new data structure: systems_scope which is going to be populated during the initialization of new system models. On the example code I am using a python dictionary, but the most precise way of implementing scopes are simple tree structures. For a systems scope, for example, each node is going to be an instance of a system model object. The hierarchic relationships represent the hierarchic structure of space systems.

Each scope instance is going to integrate a resolve(name_of_system_model) method which will use the “child system of parent system” syntax in order to walk down the tree and resolve the corresponding object.   

Same way, scope structures have to be implemented for Activities, Reporting Data and Events.

## Extending Space System Model management

* Implementing an sqlite3 database proxy in order to store and access Space System Model’s properties
* Implementing a PLUTO procedure proxy in order to assign or return object values.

## BUILDING A PLUTO INTERPRETER IN PYTHON

### PARSING PLUTO SCRIPTS
#### Converting PLUTO structure into EBNF grammar notations
Lark Parser  besides the fact that is a truly powerful module, it can be really useful on the development of this project. The procedure that I have followed is as follows: 
```
procedurebody: "procedure" _NL  (proceduremainbody | proceduredeclarationbody | procedurepreconditionsbody)+ _NL "end procedure"
proceduremainbody: "main"_NL (procedurestatement _NL)+  "end main"
proceduredeclarationbody: "declare" _NL (eventdeclaration | "," eventdeclaration)+ _NL "end declare"
procedurestatement: paralleluntilall | paralleluntilone | setprocedurecontext | initiateandconfirmstep | initiateandconfirmactivity | initiateactivity
```
which, parses a PLUTO language script through LARK , generating hierarchic parse trees eg:

```
procedurebody
      proceduredeclarationbody
                eventdeclaration
                      eventname "chaos"
                    description "Total  disaster"                              
               eventdeclaration
                      eventname "chaos2"
       proceduremainbody
                procedurestatement
                      initiateactivity
                                activitycall
                              switchon "Reaction Wheel3"
```
Regarding those trees we have to keep the simple method of generating trees that have input-stream tokens as leaves and grammar rules as interior nodes.

#### Modeling PLUTO elements into classes

We have to analyze PLUTO language into symbols and create a symbol table, by implementing each symbol category with a different class.

e.g. Step and Procedures bodies can be implemented as follows

```python
class Body:
    def __init__(self,name,data,parent=None):
            self.name = name
            self.data = data
            self.parent = parent
    def run(self):
            pass
class DeclarationBody(Body):
    def __init__(self,name,data):
            global eventsScope
            super().__init__(name,data)
```
#### Transforming Parse Tree

The fact that PLUTO procedure integrates nested grammar, allows us to generate a single procedure instance by using Lark’s Transformer class. That way, each node is instanciated and passed to its parent. 

```python
class Parser(Transformer):
    def activitycall(self,args):
            obj = ActivityCallSymbol(None,args[0])
            return obj
        def initiateandconfirmactivity(self,args):
            obj = InitiateAndConfirmActivityStatement(None,args[0])
            return obj
    def stepstatement(self,args):
            return args
    def stepmainbody(self,args):
            obj = MainBody(None,args)
            return obj
    def stepdefinition(self,args):
            return args
    def stepname(self,args):
            stepname = " "
            stepname = stepname.join(args)
            return stepname
```

#### Scope of symbols

By transforming parse tree into different instances, with references to their parents, we can avoid creating a complicated symbol scope tree. 
Although we have to implement a Scope Class 

```python
Class Scope :
   def getScopeName(self):
   def getEnclosingScope(self): ← if nested
   def define(symbol): ← define a symbol in this scope
   def resolve(symbol): ← lookup a name in scope
```

## Runtime Analysis (PLUTO interpreter)

### Implementing registers and memory spaces

PLUTO is not a general purpose language, that’s why we have to specifically implement some of its characteristics in a different way. There is always global memory space which corresponds to global-procedure scope, but PLUTO allows us to implement steps in a nested manner. That’s why memory space can be implemented according to static scope structure, as property of procedure and step instances. To keep it simple for our example we can implement different memory spaces as dictionaries inside a step or procedure instance:

```python
class ProcedureSymbol(Symbol):
    execution_status = "executing"
    memory_space = { variable : variableSymbolInstance }
    def resolve_from_memory(variable):
class VariableSymbol(Symbol):
    name = ....
    parent = ProcedureSymbolInstance
    value = ....
    def update_in_memory(self):
        parent.memory_space[variableSymbolInstance.name] = variableSymbolInstance
```

### Implementing run() method

In order to run a PLUTO procedure, this composite-like pattern implementation allows us to implement different run methods for each symbol class. That way its composite object will be able to call the run() method of its components either structured or in parallel (according to PLUTO restrictions) and if needed sends requests or receives data through the space system model proxy. 

Evaluating an expression inside a run() method:

```python
class IfStatement:
    self.expression = ExpressionSymbolInstance
self.if_block = IfBlockInstance
self.else_block = ThenBlockInstance    
def run():
    result = self.expression.run()
    if result:
            self.if_block(run)
        else if self.else_block != None:
            self_block.run()

class ExpressionSymbol:
    def run():
        d = resolve_variables_from_memory()
            locals().update(d)
            result = eval(self.data)
            return result
```

### Implementing watchdogs through multiple observers and composite

According to PLUTO when an event is raised it may need to be handled by its scope’s (procedure or step) watchdog body. Same way, when watchdog finishes handling, has to return to a specific point of procedure’s or step’s execution.

First of all we have to implement a raise_event() method for each event instance this method has to notify its parent instance (step or procedure) then, procedure or step has to notify watchdog thread and pause execution. When watchdog finishes handling the event, has to notify procedure with the results, and the execution of the procedure proceeds according to this final notification.
