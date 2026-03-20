from collections import deque
from .models import Edge


def findpath(startnode, endnode):
    queue = deque([[startnode]])
    visited = set()

    while queue:
        path = queue.popleft()
        node = path[-1]

        if node == endnode:
            return path

        if node not in visited:
            visited.add(node)

            edges = Edge.objects.filter(fromnode=node)
            for edge in edges:
                newpath = list(path)
                newpath.append(edge.tonode)
                queue.append(newpath)

    return None
def nodeswithinrange(startnode):
    from collections import deque
    from .models import Edge

    visited = set()
    queue = deque([(startnode, 0)])

    while queue:
        node, depth = queue.popleft()

        if depth > 2:
            continue

        visited.add(node)

        edges = Edge.objects.filter(fromnode=node)
        for edge in edges:
            queue.append((edge.tonode, depth + 1))

    return visited
def reachablenodes(trip):
    from trips.models import TripRoute

    reachable = set()
    remainingroutes = TripRoute.objects.filter(
        trip=trip,
        visited=False
    )

    for route in remainingroutes:
        nodes = nodeswithinrange(route.node)
        reachable.update(nodes)

    return reachable
def findmatchingtrips(pickupnode, dropnode):
    from trips.models import Trip, TripRoute

    matchingtrips = []

    trips = Trip.objects.filter(status='active')

    for trip in trips:
        remainingroutes = TripRoute.objects.filter(
            trip=trip,
            visited=False
        ).order_by('order')

        routenodes = [r.node for r in remainingroutes]
        if pickupnode in routenodes and dropnode in routenodes:
            if routenodes.index(pickupnode) < routenodes.index(dropnode):
                matchingtrips.append(trip)

    return matchingtrips
def calculatefare(trip, pickupnode, dropnode):
    from trips.models import TripRoute
    from network.utility import findpath

    PRICEPERHOP = 10
    BASEFEE = 20

    remainingroutes = TripRoute.objects.filter(
        trip=trip,
        visited=False
    ).order_by('order')

    originalnodes = [r.node for r in remainingroutes]
    originallength = len(originalnodes)

    newpath1 = findpath(trip.currentnode, pickupnode)
    newpath2 = findpath(pickupnode, dropnode)
    newpath3 = findpath(dropnode, trip.endnode)

    newroute = []

    for path in [newpath1, newpath2, newpath3]:
        if path:
            if newroute:
                newroute += path[1:]
            else:
                newroute += path

    newlength = len(newroute)
    detour = newlength - originallength
    
    active_passengers = []
    existing_requests = trip.carpooloffer_set.filter(status='accepted')

    for req in existing_requests:
        active_passengers.append({
            "pickup": req.request.pickupnode,
            "drop": req.request.dropnode
        })


    active_passengers.append({
        "pickup": pickupnode,
        "drop": dropnode
    })

    faresum = 0
    current_passengers = 0

    for i in range(len(newroute) - 1):
        current_node = newroute[i]

    
        for p in active_passengers:
            if p["pickup"] == current_node:
                current_passengers += 1

    
        for p in active_passengers:
            if p["drop"] == current_node:
                current_passengers -= 1

        if current_passengers <= 0:
            current_passengers = 1

        faresum += 1 / current_passengers

    fare = PRICEPERHOP * faresum + BASEFEE

    return {
        "originallength": originallength,
        "newlength": newlength,
        "detour": detour,
        "fare": round(fare, 2)
    }