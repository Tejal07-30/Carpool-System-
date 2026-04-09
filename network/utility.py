from collections import deque
from .models import Edge
#Trip and TripRoute were imported in each function individually because of some import error. 
def findpath(startnode, endnode):
    from trips.models import TripRoute
    queue = deque([[startnode]])
    visited = set()

    while queue:
        path = queue.popleft()
        node = path[-1]

        if node.id == endnode.id:
            return path

        if node not in visited:
            visited.add(node)

            edges = Edge.objects.filter(fromnode=node)
            for edge in edges:
                nextnode = edge.tonode
                if nextnode not in path:
                    newpath = list(path)
                    newpath.append(edge.tonode)
                    queue.append(newpath)

    return None
def nodeswithinrange(startnode, maxrange=2):
    from trips.models import Trip, TripRoute

    visited = set()
    queue = deque([(startnode, 0)])
    result = set() 
    while queue:
        node, dist = queue.popleft()

        if dist > maxrange:
            continue

        result.add(node)

        edges = Edge.objects.filter(fromnode=node)
        for edge in edges:
            nextnode = edge.tonode
            if nextnode.id not in visited:
                visited.add(nextnode.id)
                queue.append((nextnode, dist + 1))

    return result
def reachablenodes(trip):
    from trips.models import Trip, TripRoute
    reachable = set()
    remainingroutes = TripRoute.objects.filter(
        trip=trip,
        visited=False
    )

    for route in remainingroutes:
        nodes = nodeswithinrange(route.node, 2)
        reachable.update(nodes)

    return reachable
def getremainingnodes(trip):
    from trips.models import TripRoute

    routes = TripRoute.objects.filter(
        trip=trip,
        #visited=False
    ).order_by('order')

    return [r.node for r in routes]
def getreachablenodes(routenodes):
    reachable = set()

    for node in routenodes:
        reachable |= nodeswithinrange(node, 2)

    return reachable

def findmatchingtrips(pickupnode, dropoffnode):
    from trips.models import Trip

    matchingtrips = []

    trips = Trip.objects.filter(status='active')
    #print("Active trips:", trips)

    for trip in trips:
        #print("\nChecking trip:", trip.id)
        remainingnodes = getremainingnodes(trip)
        #print("Remaining nodes:", [n.id for n in remainingnodes])
        if not remainingnodes:
            #print("❌ No remaining nodes")
            continue

        if trip.getcurrentpassengercount() >= trip.maxpassengers:
            #print("❌ Trip full")
            continue
        
        reachablenodes = getreachablenodes(remainingnodes)
        
        if pickupnode not in reachablenodes or dropoffnode not in reachablenodes:
            continue

        routeids = [node.id for node in remainingnodes]

        if pickupnode.id not in routeids or dropoffnode.id not in routeids:
            continue

        if routeids.index(pickupnode.id) >= routeids.index(dropoffnode.id):
            continue

        matchingtrips.append(trip)

    return matchingtrips


def calculatefare(trip, pickupnode, dropnode):
    from trips.models import Trip, TripRoute
    PRICEPERHOP = 10
    BASEFEE = 20

    remainingroutes = TripRoute.objects.filter(
        trip=trip,
        visited=False
    ).order_by('order')

    originalnodes = [r.node for r in remainingroutes]
    originallength = len(originalnodes)

    newpath1 = findpath(trip.getcurrentnode(), pickupnode) or []
    newpath2 = findpath(pickupnode, dropnode) or []
    newpath3 = findpath(dropnode, trip.endnode) or []

    newroute = []

    for path in [newpath1, newpath2, newpath3]:
        if path:
            if newroute:
                newroute += path[1:]
            else:
                newroute += path

    newlength = len(newroute)
    detour = newlength - originallength
    
    activepassengers = []
    existingrequests = trip.offers.filter(status='accepted')

    for req in existingrequests:
        activepassengers.append({
            "pickup": req.request.pickupnode,
            "drop": req.request.dropoffnode
        })


    activepassengers.append({
        "pickup": pickupnode,
        "drop": dropnode
    })

    faresum = 0
    currentpassengers = 0

    for i in range(len(newroute) - 1):
        currentnode = newroute[i]

    
        for p in activepassengers:
            if p["pickup"] == currentnode:
                currentpassengers += 1

    
        for p in activepassengers:
            if p["drop"] == currentnode:
                currentpassengers -= 1

        if currentpassengers <= 0:
            currentpassengers = 1

        faresum += 1 / currentpassengers

    fare = PRICEPERHOP * faresum + BASEFEE

    return {
        "originallength": originallength,
        "newlength": newlength,
        "detour": detour,
        "fare": round(fare, 2)
    }