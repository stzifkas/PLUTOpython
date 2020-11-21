from lark import Lark, Tree, Transformer, v_args
import threading
import queue
from SSM import *

eventsScope = {}
class Utilities(object):
    system = None

class Symbol:
    def __init__(self,name,type=None):
        self.name = name
        self.type = type

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
    def run(self):
        eventsScope[self.parent] = []
        self.parent.executionStatus = "executing"
        for statement in self.data:
            #print(statement)
            statement.run(self.parent)

class PrecoditionsBody(Body):
    def __init__(self,name,data):
        super().__init__(name,data)

class MainBody(Body):
    def __init__(self,name,statements):
        super().__init__(name,statements)
    def run(self):
        self.parent.executionStatus = "executing"
        ### FIXME: we dont need to flatten statement list like this:
        statements = [statement for sublist in self.data for statement in sublist]
        for statement in statements:
            statement.run()

class WatchdogBody(Body):
    def __init__(self,name,data):
        super().__init__(name,data)

class ConfirmationBody(Body):
    def __init__(self,name,ifOrWaitStatements):
        super().__init__(name)
        self.ifOrWaitStatements = ifOrWaitStatements

class ProcedureListener:
    def __init__(self,name,watchdog,procedure):
        self.name = name
        self.watchdog = watchdog
        self.listenFlag = True
    def listenWatchdog():
        while self.listenFlag:
            if watchdog.continuationAction == "resume":
                procedure.setExecutionSatus("executing")
                procedure.setConfirmationStatus("not available")
            if watchdog.continuationAction == "terminate":
                procedure.setExecutionSatus("confirmation")
                procedure.setConfirmationStatus("not available")
            if watchdog.continuationAction == "raise event":
                 pass
            if watchdog.continuationAction == "abort":
                procedure.setExecutionSatus("completed")
                procedure.setConfirmationStatus("aborted")


class WatchdogSymbol(Symbol):
    def __init__(self,name,events,step=None):
        self.name = name
        self.continuationAction = "not available"
        self.step = step
        self.events = events
        #if it is a step watchdog we have to know the step
    def listenToEventRegister():
        global eventRegister
        while True:
            if eventRegister in self.events:
                ##call the appropriate handler
                pass

class ProcedureSymbol(Symbol):
    def __init__(self,name,mainbody=None, declarationbody=None, preconditionsbody=None, watchdogbody=None, confirmationbody=None):
        super().__init__(name)
        self.mainBody = mainbody
        self.declarationBody = declarationbody
        self.preconditionsBody = preconditionsbody
        self.watchdoBody = watchdogbody
        self.confirmationBody = confirmationbody
        self.bodies = [mainbody, declarationbody, preconditionsbody, watchdogbody, confirmationbody]
        self.executionStatus = "not available"
        self.confirmationStatus = "not available"
        #print(self.bodies)
    def setExecutionSatus(self,data):
        self.executionStatus = data
    def setConfirmationStatus(self,data):
        self.confirmationStatus = data
    def run(self):
        for body in self.bodies:
            try:
                body.parent = self
                #print("yeh")
                body.run()
            except Exception as e:
                #print(e)
                continue

class EventSymbol(Symbol):
    def __init__(self,name,description=None):
        super().__init__(name)
        self.description = description
    def raiseEvent(self):
        global eventRegister
        if eventRegister == None:
            eventRegister = self.name
    def run(self,parent):
        #print("I am here!!!")
        global eventsScope
        eventsScope[parent].append(self)
        ##print(f" SCOPE:")
        #print(eventsScope)

class ExpressionSymbol(Symbol):
    def __init__(self,name,type,data):
        super().__init__(name,type)
        self.data = data
class EventReferenceSymbol(Symbol):
    def __init__(self,name,data):
        super().__init__(name)
        self.data = data
class TimeoutSymbol(Symbol):
    def __init__(self,name,data,raiseEvent=None):
        super().__init__(name)
        self.data = data
        self.raiseEvent = raiseEvent
class Statement:
    def __init__(self,name,type=None):
        self.name = name
        self.type = type
class SetProcedureContextStatement(Statement):
    def __init__(self,name):
        super().__init__(name)
class InitiateInParallelStatement(Statement):
    pass
class InitiateAndConfirmStepStatement(Statement):
    def __init__(self,name,step,continuationtest=None):
        super().__init__(name)
        self.step = step
        self.continuationtest = continuationtest
    def run(self):
        #we have to initiate a new listener
        #and run step in parallel
        t = threading.Thread(target=self.step.run)
        t.start()
        stepListener = InitiateAndConfirmStepListener(self.step)
        stepListener.listen()

class InitiateAndConfirmStepListener:
    def __init__(self,step):
        self.step = step
    def listen(self):
        #print(f"{self} is listening for {self.step}'s execution status")
        while self.step.executionStatus != "completed":
            continue
        return True

class InformUserStatement(Statement):
    pass
class LogStatement(Statement):
    pass
class StepSymbol(Symbol):
    def __init__(self,name,mainbody=None, declarationbody=None, preconditionsbody=None, watchdogbody=None, confirmationbody=None):
        super().__init__(name)
        self.mainBody = mainbody
        self.declarationBody = declarationbody
        self.preconditionsBody = preconditionsbody
        self.watchdoBody = watchdogbody
        self.confirmationBody = confirmationbody
        self.bodies = [mainbody, declarationbody, preconditionsbody, watchdogbody, confirmationbody]
        self.executionStatus = "not available"
        self.confirmationStatus = "not available"
        #print(self.bodies)
    def setExecutionSatus(self,data):
        self.executionStatus = data
    def setConfirmationStatus(self,data):
        self.confirmationStatus = data
    def run(self):
        for body in self.bodies:
            try:
                body.parent = self
                #print("yeh")
                body.run()
            except Exception as e:
                #print(e)
                continue
        self.executionStatus = "completed"


class StepMainBody(Body):
    def __init__(self,name,statements):
        super().__init__(name)
        self.statements = statements

class SetStepContextStatement(Statement):
    def __init__(self,name,obj,statements):
        super().__init__(name)
        self.obj = obj
        self.statements = statements
class AssignmentStatement(Statement):
    def __init__(self,name,variable,expression):
        super().__init__(name)
        self.variable = variable
        self.expression = expression
class IfStatement(Statement):
    def __init__(self,name,expression,thenstatements,elsestatements):
        super().__init__(name)
        self.exression = expression
        self.thenstatements = thenstatements
        self.elsestatements = elsestatements
class CaseStatement(Statement):
    def __init__(self,name,expression,valuesToStatements):
        super().__init__(name)
        self.expression = expression
        self.valuesToStatements = valuesToStatements

class RepeatStatement(Statement):
    def __init__(self,name,statements,untilExpression,timeout=None):
        super().__init__(name)
        self.statements = statements
        self.untilExpression = untilExpression
        self.timeout = timeout

class WhileStatement(Statement):
    def __init__(self,name,expression,statements,timeout=None):
        super().__init__(name)
        self.expression = expression
        self.statements = statements
        self.timeout = timeout
class ForStatement(Statement):
    def __init__(self,name,variableReference,toExpression,statements,byExpression=1):
        super().__init__(name)
        self.variableReference = variableReference
        self.toExpression = toExpression
        self.statements = statements
        self.byExpression = byExpression

class ObjectOperationReqStatement(Statement):
    def __init__(self,name,objectOperation,objectReference=None,argsToExpressions={}):
        super().__init__(name)
        self.objectOperation = objectOperation
        self.objectReference = objectReference
        self.argsToExpressions = argsToExpressions

class ObjectOperationSymbol(Symbol):
    def __init__(self,name,set=False,property=None,nonStandardObjectOperation=None):
        super().__init__(name)
        self.set = set
        self.property = property
        self.nonStandardObjectOperation = nonStandardObjectOperation

class SaveContextStatement(Statement):
    def __init__(self,name):
        super().__init__(name)

class InitiateAndConfirmActivityStatement(Statement):
    def __init__(self,name,activityCall,referActivityStatement=None,continuationTest=None):
        super().__init__(name)
        self.activityCall = activityCall
        self.referActivityStatement = referActivityStatement
        self.continuationTest = continuationTest
    def run(self):
        #print(self.activityCall)
        self.activityCall.run()

class InitiateActivityStatement(Statement):
    def __init__(self,name,activityCall,referActivityStatement=None):
        super().__init__(name)
        self.activityCall = activityCall
        self.referActivityStatement = referActivityStatement
    def run(self):
        """ run self.activityCall in parallel
        """
        t = threading.Thread(target=self.activityCall.run)
        t.start()
class InformUserStatement(Statement):
    def __init__(self,name,expressions):
        super().__init__(name)
        self.expressions = expressions

class ActivityCallSymbol(Symbol):
    def __init__(self,name,activityReference,arguments=None,valueSetReference=None,directives=None):
        super().__init__(name)
        self.activityReference = activityReference
        self.valueSetReference = valueSetReference
        self.directives = directives
    def run(self):
        #print(self.activityReference)
        self.activityReference.run()

class SimpleArgumentSymbol(Symbol):
    def __init__(self,name,expression=None,activityCall=None,reportingDataRef=None,systemElementRef=None,eventRef=None):
        super().__init__(name)
        self.expression = expression
        self.activityCall = activityCall
        self.reportingDataRef = reportingDataRef
        self.systemElementRef = systemElementRef
        self.eventRef = eventRef
class RecordArgumentSymbol(Symbol):
    def __init__(self,name,arguments):
        super().__init__(name)
        self.arguments = arguments
class ArrayArgumentSymbol(Symbol):
    def __init__(self,name,arguments):
        super().__init__(name)
        self.arguments = arguments

class LogStatement(Statement):
    def __init__(self,name,expressions):
        super().__init__(name)
        self.expressions = expressions

class SwitchOnSymbol(Symbol):
    def __init__(self,name,data):
        super().__init__(name)
        self.data = data
    def run(self):
        global activitiesScope
        print("switchon data:")
        obj = resolveActivity("Switch On",self.data)
        obj.method()

class ParallelUntilAllStatement(Statement):
    def __init__(self,name,statements):
        super().__init__(name)
        self.statements = statements
    def run(self):
        #print("Parallel statements:")
        #print(self.statements)
        threads = []
        for statement in self.statements:
            t = threading.Thread(target=statement.run)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

class Parser(Transformer):
    def switchon(self,args):
        data = " "
        data = data.join(args)
        obj = SwitchOnSymbol(None,data)
        return obj
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
    def initiateandconfirmstep(self,args):
        #print("New step found:")
        #print(*args[1])
        step = StepSymbol(args[0],*args[1])
        obj = InitiateAndConfirmStepStatement(None,step)
        return obj
    def paralleluntilall(self,args):
        obj = ParallelUntilAllStatement(None,args)
        return obj
    def procedurestatement(self,args):
        return args
    def initiateactivity(self,args):
        #print(args)
        obj = InitiateActivityStatement(None,*args)
        return obj
    def proceduremainbody(self,args):
        #print(args)
        obj = MainBody(None,args)
        return obj
    def eventname(self,args):
        eventname = " "
        eventname = eventname.join(args)
        return eventname
    def description(self,args):
        description = " "
        description = description.join(args)
        return description
    def eventdeclaration(self,args):
        #print(args)
        obj = EventSymbol(*args)
        return obj
    def proceduredeclarationbody(self,args):
        #print(args)
        obj = DeclarationBody(None,args)
        return obj
    def procedurebody(self,args):
        #print(args)
        obj = ProcedureSymbol(None,*args)
        return obj


def main():
    global executionStatus
    #Parse extendedpluto grammar
    pluto_grammar = Lark.open('extendedpluto.lark',start="procedurebody")
    #Parse script.pluto into a lexer tree
    with open('script.pluto', 'r') as plutoscript:
        pluto = plutoscript.read()
    #print(pluto)
    procedure = pluto_grammar.parse(pluto)
    #print(procedure.pretty())
    #Create a dummy space system model on memory
    aocelectronics1 = SystemElement(
                                    "AOC Electronics1",
                                    "Dummy part",
                                    "part",
                                    "realization",
                                    None,
                                    None)
    aocelectronics2 = SystemElement(
                                    "AOC Electronics2",
                                    "Dummy part",
                                    "part",
                                    "realization",
                                    None,
                                    None)
    startracker1 = SystemElement(
                                    "Star Tracker1",
                                    "Dummy part",
                                    "sensor",
                                    "realization",
                                    None,
                                    ["Star Tracker2", "Star Tracker3"])
    startracker2 = SystemElement(
                                    "Star Tracker2",
                                    "Dummy part",
                                    "sensor",
                                    "realization",
                                    None,
                                    ["Star Tracker1", "Star Tracker3"])
    startracker3 = SystemElement(
                                    "Star Tracker3",
                                    "Dummy part",
                                    "sensor",
                                    "realization",
                                    None,
                                    ["Star Tracker1", "Star Tracker2"])
    reactionwheel3 = SystemElement(
                                    "Reaction Wheel3",
                                    "Dummy part",
                                    "subsystem",
                                    "realization",
                                    None,
                                    None)
    aocreferences = {
                    "AOC Electronics1" : None,
                    "AOC Electronics2" : None,
                    "Star Tracker1" : None,
                    "Star Tracker2" : None,
                    "Reaction Wheel3" : None
                     }
    aoc = SystemElement(
                        "AOC",
                        "Dummmy System Element",
                        "subsystem",
                        "realization",
                        aocreferences,
                        None)
    satelliteReferences = {
                            "AOC" : "AOC Electronics1",
                            "AOC" : "AOC Electronics2",
                            "AOC" : "Star Tracker1",
                            "AOC" : "Star Tracker2",
                            "AOC" : "Reaction Wheel3"
                            }

    satellite = SystemSystemElement(
                                    "Satellite",
                                    "A Satellite System",
                                    "system",
                                    "realization",
                                    satelliteReferences,
                                    None,
                                    "uniqueidentifierplaceholder",
                                    "space segment")
    startracker1temp = Parameter("Star Tracker1 of AOC of Satellite","Temperature","Still Dummy","Operations",None,None,None,None,dataType="C")
    swichOffReactionWheel3 = Activity("Reaction Wheel3 of AOC of Satellite","Switch Off", "Dummy Activity","onboard procedure",None,None,None,None,"mission critical",None,None,None,None,None,None,None,None,None)
    switchOnReactionWheel3 = Activity("Reaction Wheel3 of AOC of Satellite","Switch On", "Dummy Activity","onboard procedure",None,None,None,swichOffReactionWheel3,"mission critical",None,None,None,None,None,None,None,None,None)
    switchOnStarTracker1 = Activity("Star Tracker1","Switch On", "Dummy Activity","onboard procedure",None,None,None,None,"mission critical",None,None,None,None,None,None,None,None,None)
    switchOnStarTracker2 = Activity("Star Tracker2","Switch On", "Dummy Activity","onboard procedure",None,None,None,None,"mission critical",None,None,None,None,None,None,None,None,None)
    #assign methods to activities
    switchOnReactionWheel3.method = types.MethodType(switchon,switchOnReactionWheel3)
    switchOnStarTracker1.method = types.MethodType(switchon,switchOnStarTracker1)
    switchOnStarTracker2.method = types.MethodType(switchon,switchOnStarTracker2)
    #Transform tree into a procedure instance:
    parse = Parser()
    procedure = parse.transform(procedure)
    procedure.run()
    procedure.executionStatus = "completed"
    #print(procedure.executionStatus)

if __name__ == "__main__":
    main()
