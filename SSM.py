import types
systemsScope = {}
activitiesScope = []

class Type:
    def __init__(self,name):
        self.name = name
    def __str__(self):
        return self.name
class BooleanType(Type):
    def __init__(self):
        super().__init__("Boolean")
class IntegerType(Type):
    def __init__(self,name,isLong=False,hasUnits=False,engineeringUnits=None,inRange=None):
        super().__init__("Integer")
        self.long = long
        self.isLong = isLong
        self.hasUnits = hasUnits
        self.engineeringUnits = engineeringUnits
        self.inRange = inRange
class ComplexType:
    def __init__(self,name):
        self.name = name
    def __str__(self):
        return self.name

class SystemElement:
    def __init__(self,name,description,type,nature,subproductsToSystemElement, redundantSystemElements):
        global systemsScope
        self.name = name
        self.description = description
        self.type = type
        self.nature = nature
        self.subproductsToSystemElement = subproductsToSystemElement
        self.redundantSystemElements = redundantSystemElements
        systemsScope[name] = subproductsToSystemElement
class VersionData:
    def __init__(
        self,
        number,
        date,
        originator,
        reason,
        status):
        self.number = number
        self.date = date
        self.originator = originator
        self.reason = reason
        self.status = status
class TelecommandSystemElement(SystemElement):
        def __init__(self,name,description,type,nature,subproductsToSystemElement, redundantSystemElements,id):
            super().name = name
            super().description = description
            super().type = type
            super().nature = nature
            super().subproductsToSystemElement = subproductsToSystemElement
            super().redundantSystemElements = redundantSystemElements
            self.id = id

class LimitationsSystemElement(SystemElement):
    def __init__(self,name,description,type,nature,subproductsToSystemElement, redundantSystemElements,maximumCycles,maximumDuration,datesToDuration,cumulativeCycles,cumulativeDuration):
        super().name = name
        super().description = description
        super().type = type
        super().nature = nature
        super().subproductsToSystemElement = subproductsToSystemElement
        super().redundantSystemElements = redundantSystemElements
        self.maximumCycles = maximumCycles
        self.maximumDuration = maximumDuration
        self.datesToDuration = datesToDuration
        self.cumulativeCycles = cumulativeCycles
        self.cumulativeDuration = cumulativeDuration

class SystemSystemElement(SystemElement):
    def __init__(self,name,description,type,nature,subproductsToSystemElement, redundantSystemElements,id,systemType):
        super().__init__(name,description,type,nature,subproductsToSystemElement, redundantSystemElements)
        self.id = id
        self.systemType = systemType

class Activity:
    def __init__(
        self,
        nameOfSystemElement,
        name,
        description,
        type,
        domainApplicability,
        subProductsToSystemElementsToActivities,
        redundantActivity,
        reverseActivity,
        criticality,
        listOfArguments,
        listOfArgumentValueSets,
        expectedDuration,
        minimumDuration,
        maximumDuration,
        earliestStartTime,
        latestStartTime,
        nameToQuantity,
        domainApplicabilityToFailureActivity
        ):
        global activitiesScope
        self.nameOfSystemElement = nameOfSystemElement
        self.name = name
        self.description = description
        self.type = type
        self.domainApplicability = domainApplicability
        self.subProductsToSystemElementsToActivities = subProductsToSystemElementsToActivities
        self.redundantActivity = redundantActivity
        self.reverseActivity = reverseActivity
        self.criticality = criticality
        self.listOfArguments = listOfArguments
        self.listOfArgumentValueSets = listOfArgumentValueSets
        self.expectedDuration = expectedDuration
        self.minimumDuration = minimumDuration
        self.maximumDuration = maximumDuration
        self.earliestStartTime = earliestStartTime
        self.latestStartTime = latestStartTime
        self.nameToQuantity = nameToQuantity
        self.domainApplicabilityToFailureActivity = domainApplicabilityToFailureActivity
        self.method = None
        activitiesScope.append(self)
        print(activitiesScope)

class Step:
    def __init__(
        self,
        name,
        description,
        minimumDuration,
        maximumDuration,
        earliestStartTime,
        latestStartTime,
        nameToQuantity
        ):
        self.state = "not initiated"
        self.name = name
        self.descrition = description
        self.minimumDuration = minimumDuration
        self.maximumDuration = maximumDuration
        self.earliestStartTime = earliestStartTime
        self.latestStartTime = latestStartTime

class ActivityCall(ComplexType):
    def __init__(self,nameOfSystemElement,name,description,type,domainApplicability,subProductsToSystemElementsToActivities,redundantActivity,reverseActivity,criticality,listOfArguments,nameOfSystemElements):
        super.__init__("Activity Call")
        self.nameOfSystemElement = nameOfSystemElement
        self.name = name
        self.description = description
        self.type = type
        self.domainApplicability = domainApplicability
        self.subProductsToSystemElementsToActivities = subProductsToSystemElementsToActivities
        self.redundantActivity = redundantActivity
        self.reverseActivity = reverseActivity
        self.criticality = criticality
        self.listOfArguments = listOfArguments
        self.nameOfSystemElements = nameOfSystemElements

class ArrayArity:
    def __init__(self,name,minimumNumberOfRepetitions,maximumNumberOfRepetitions):
        self.name = name
        self.minimumNumberOfRepetitions = minimumNumberOfRepetitions
        self.maximumNumberOfRepetitions = maximumNumberOfRepetitions

class Telecommand(Activity):
    def __init__(
        self,
        serviceData,
        serviceSubtype,
        defaultApplicationProcess,
        priority,
        map=None
        ):
        self.serviceData = serviceData
        self.serviceSubtype = serviceSubtype
        self.defaultApplicationProcess = defaultApplicationProcess
        self.priority = priority
        self.map = map

class TelecommandArguments(ArrayArity):
    def __init__(
        self,
        name,
        minimumNumberOfRepetitions,
        maximumNumberOfRepetitions,
        pfcOfRepetitionNumber
        ):
        super().__init__(self,name,minimumNumberOfRepetitions,maximumNumberOfRepetitions)
        self.pfcOfRepetitionNumber = pfcOfRepetitionNumber
class ProcedureActivity(Activity):
    def __init__(
        self,
        nameOfSystemElement,
        name,
        description,
        type,
        domainApplicability,
        subProductsToSystemElementsToActivities,
        redundantActivity,
        reverseActivity,
        criticality,
        listOfArguments,
        listOfArgumentValueSets,
        expectedDuration,
        minimumDuration,
        maximumDuration,
        earliestStartTime,
        latestStartTime,
        nameToQuantity,
        domainApplicabilityToFailureActivity,
        initiationMode,
        earliestValidityDate,
        latestValidityDate
        ):
        super().__init__(
            self,
            nameOfSystemElement,
            name,
            description,
            type,
            domainApplicability,
            subProductsToSystemElementsToActivities,
            redundantActivity,
            reverseActivity,
            criticality,
            listOfArguments,
            listOfArgumentValueSets,
            expectedDuration,
            minimumDuration,
            maximumDuration,
            earliestStartTime,
            latestStartTime,
            nameToQuantity,
            domainApplicabilityToFailureActivity
            )
        self.initiationMode = initiationMode
        self.earliestValidityDate = earliestValidityDate
        self.latestValidityDate = latestValidityDate

class GroundProcedureActivity(ProcedureActivity):
    def __init__(
        self,
        nameOfSystemElement,
        name,
        description,
        type,
        domainApplicability,
        subProductsToSystemElementsToActivities,
        redundantActivity,
        reverseActivity,
        criticality,
        listOfArguments,
        listOfArgumentValueSets,
        expectedDuration,
        minimumDuration,
        maximumDuration,
        earliestStartTime,
        latestStartTime,
        nameToQuantity,
        domainApplicabilityToFailureActivity,
        initiationMode,
        earliestValidityDate,
        latestValidityDate,
        script,
        executionMode
        ):
        super().__init__(
            self,
            nameOfSystemElement,
            name,
            description,
            type,
            domainApplicability,
            subProductsToSystemElementsToActivities,
            redundantActivity,
            reverseActivity,
            criticality,
            listOfArguments,
            listOfArgumentValueSets,
            expectedDuration,
            minimumDuration,
            maximumDuration,
            earliestStartTime,
            latestStartTime,
            nameToQuantity,
            domainApplicabilityToFailureActivity,
            initiationMode,
            earliestValidityDate,
            latestValidityDate
            )
        self.script = script
        self.executionMode = executionMode

class OnboardProcedureActivity(ProcedureActivity):
    def __init__(
        self,
        nameOfSystemElement,
        name,
        description,
        type,
        domainApplicability,
        subProductsToSystemElementsToActivities,
        redundantActivity,
        reverseActivity,
        criticality,
        listOfArguments,
        listOfArgumentValueSets,
        expectedDuration,
        minimumDuration,
        maximumDuration,
        earliestStartTime,
        latestStartTime,
        nameToQuantity,
        domainApplicabilityToFailureActivity,
        initiationMode,
        earliestValidityDate,
        latestValidityDate,
        script,
        preloadedOnBoard,
        priority
        ):
        super().__init__(
            self,
            nameOfSystemElement,
            name,
            description,
            type,
            domainApplicability,
            subProductsToSystemElementsToActivities,
            redundantActivity,
            reverseActivity,
            criticality,
            listOfArguments,
            listOfArgumentValueSets,
            expectedDuration,
            minimumDuration,
            maximumDuration,
            earliestStartTime,
            latestStartTime,
            nameToQuantity,
            domainApplicabilityToFailureActivity,
            initiationMode,
            earliestValidityDate,
            latestValidityDate
            )
        self.script = script
        self.preloadedOnBoard = preloadedOnBoard
        self.priority = priority

class Event:
    def __init__(
        self,
        nameOfSystemElement,
        name,
        description,
        type,
        domainApplicability,
        subProductsToSystemElementsToEvents,
        severity,
        reportingDataToTimeOffset,
        domainApplicabilityToActivity
        ):
        self.nameOfSystemElement = nameOfSystemElement
        self.name = name
        self.description = description
        self.type = type
        self.domainApplicability = domainApplicability
        self.subProductsToSystemElementsToEvents = subProductsToSystemElementsToEvents
        self.severity = severity
        self.reportingDataToTimeOffset = reportingDataToTimeOffset
        self.domainApplicabilityToActivity = domainApplicabilityToActivity

class ReportingData:
    def __init__(
                self,
                nameOfSystemElement,
                name,
                description,
                type,
                domainApplicability,
                domainApplicabilityToValidityCondition,
                references,
                redundantReportingData):
        self.nameOfSystemElement = nameOfSystemElement
        self.name = name
        self.description = description
        self.type = type
        self.domainApplicability = domainApplicability
        self.domainApplicabilityToValidityCondition = domainApplicabilityToValidityCondition
        self.references = references
        self.redundantReportingData = redundantReportingData

class Parameter(ReportingData):
    def __init__(
                self,
                nameOfSystemElement,
                name,
                description,
                type,
                domainApplicability,
                domainApplicabilityToValidityCondition,
                references,
                redundantReportingData,
                dataType):
        super().__init__(
                    nameOfSystemElement,
                    name,
                    description,
                    type,
                    domainApplicability,
                    domainApplicabilityToValidityCondition,
                    references,
                    redundantReportingData)
        self.dataType = dataType
        self.value = 0
    def __str__(self):
        return f"<{self.value}:{self.dataType}>"
def switchon(self):
    print(f"{self.nameOfSystemElement} is on")

def resolveSystem(nameOfSystemElement):
    global systemsScope
    listOfElements = nameOfSystemElement.split(" of ")
    for element in systemsScope.values():
        try:
            for l in element:
                if(l.name == listOfElements[0]):
                    return l
        except:
            continue
def resolveActivity(activityName,nameOfSystemElement):
    global activitiesScope
    for activity in activitiesScope:
        if activity.name == activityName and activity.nameOfSystemElement == nameOfSystemElement:
            return activity
def main():
    global systemsScope
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
                    aocelectronics1 : None,
                    aocelectronics2 : None,
                    startracker1 : None,
                    startracker2 : None,
                    reactionwheel3 : None
                     }
    aoc = SystemElement(
                        "AOC",
                        "Dummmy System Element",
                        "subsystem",
                        "realization",
                        aocreferences,
                        None)
    satelliteReferences = {
                            aoc : aocelectronics1,
                            aoc : aocelectronics2,
                            aoc : startracker1,
                            aoc : startracker2,
                            aoc : reactionwheel3
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
    print(startracker1temp)
    print(systemsScope)
    resolve("Star Tracker2 of AOC of Satellite")
    #assign a method to activity
    switchOnReactionWheel3.method = types.MethodType(switchon,switchOnReactionWheel3)
    switchOnReactionWheel3.method()

if __name__ == "__main__":
    main()
