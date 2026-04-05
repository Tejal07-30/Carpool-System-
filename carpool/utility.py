from network.utility import nodeswithinrange
from network.models import Node
from network.utility import findpath
from carpool.models import Transaction

def isrequestvalid(trip, pickupnode, dropnode):
    remainingnodes = trip.getremainingroute()

    validnodes = set()

    from network.models import Node

    for node_id in remainingnodes:
        node = Node.objects.get(id=node_id)
        validnodes.update(getnodeswithinrange(node, 2))

    return pickupnode.id in validnodes and dropnode.id in validnodes
def routelength(route):
    return len(route)
def buildnewroute(trip, pickupnode, dropnode):
   
    remainingrouteids = trip.getremainingroute()
    remainingnodes = [Node.objects.get(id=i) for i in remainingrouteids]

    if not remainingnodes:
        return None

    currentnode = remainingnodes[0]
    finalnode = remainingnodes[-1]

    pathtopickup = findpath(currentnode, pickupnode)
    pathpickuptodrop = findpath(pickupnode, dropnode)
    pathdroptoend = findpath(dropnode, finalnode)

    if not pathtopickup or not pathpickuptodrop or not pathdroptoend:
        return None
    newroute = (
        pathtopickup[:-1] +
        pathpickuptodrop[:-1] +
        pathdroptoend
    )

    return [node.id for node in newroute]

def calculatedetour(trip, newroute):
    originallength = len(trip.getremainingroute())
    newlength = len(newroute)

    return newlength - originallength

def calculatefare(newroute, basefee=10, priceperhop=5, passengers=1):
    fare = 0
    hops = len(newroute)

    for _ in range(hops):
        fare += priceperhop * (1 / passengers)

    return round(fare + basefee, 2)

def computeoffer(trip, pickupnode, dropnode):
    newroute = buildnewroute(trip, pickupnode, dropnode)

    if not newroute:
        return None

    detour = calculatedetour(trip, newroute)
    fare = calculatefare(newroute)

    return {
        "route": newroute,
        "detour": detour,
        "fare": fare
    }


def processtrippayment(trip, passenger, fare):
    passengerwallet = passenger.wallet
    driverwallet = trip.driver.wallet

    if passengerwallet.balance < fare:
        raise Exception("Insufficient balance")
    passengerwallet.balance -= fare
    passengerwallet.save()

    Transaction.objects.create(
        user=passenger,
        amount=fare,
        type='debit',
        description=f"Payment for trip {trip.id}"
    )

    driverwallet.balance += fare
    driverwallet.save()

    Transaction.objects.create(
        user=trip.driver,
        amount=fare,
        type='credit',
        description=f"Earning from trip {trip.id}"
    )