from collections import deque
from .models import Edge, Node

def findpath(startnode, endnode):
    if startnode.id == endnode.id:
        return [startnode]

    queue = deque([[startnode]])
    visited = {startnode.id}

    while queue:
        path = queue.popleft()
        node = path[-1]

        edges = Edge.objects.filter(fromnode=node).select_related('tonode')
        for edge in edges:
            nextnode = edge.tonode
            if nextnode.id == endnode.id:
                return path + [nextnode]
            if nextnode.id not in visited:
                visited.add(nextnode.id)
                queue.append(path + [nextnode])

    return None


def nodeswithinrange(startnode, maxrange=2):
    visited = {startnode.id}
    queue = deque([(startnode, 0)])
    result = {startnode}

    while queue:
        node, dist = queue.popleft()
        if dist >= maxrange:
            continue
        edges = Edge.objects.filter(fromnode=node).select_related('tonode')
        for edge in edges:
            nextnode = edge.tonode
            if nextnode.id not in visited:
                visited.add(nextnode.id)
                result.add(nextnode)
                queue.append((nextnode, dist + 1))

    return result


def getreachablenodes(routenodes):
    reachable = set()
    for node in routenodes:
        reachable |= nodeswithinrange(node, 2)
    return reachable


def getremainingnodes(trip):
    from trips.models import TripRoute
    routes = TripRoute.objects.filter(
        trip=trip,
        visited=False
    ).order_by('order').select_related('node')
    return [r.node for r in routes]


def findmatchingtrips(pickupnode, dropoffnode):
    from trips.models import Trip

    matching = []
    activetrips = Trip.objects.filter(status='active').select_related('driver')

    for trip in activetrips:
        if trip.getcurrentpassengercount() >= trip.maxpassengers:
            continue

        remaining = getremainingnodes(trip)
        if not remaining:
            continue

        reachable = getreachablenodes(remaining)
        if pickupnode not in reachable or dropoffnode not in reachable:
            continue

        routeids = [n.id for n in remaining]
        if pickupnode.id not in routeids or dropoffnode.id not in routeids:
            continue

        if routeids.index(pickupnode.id) >= routeids.index(dropoffnode.id):
            continue

        matching.append(trip)

    return matching


def calculatefare(trip, pickupnode, dropoffnode):
    from trips.models import TripRoute
    from carpool.models import CarpoolOffer

    PRICE_PER_HOP = 10
    BASE_FEE = 20

    remaining = TripRoute.objects.filter(
        trip=trip, visited=False
    ).order_by('order').select_related('node')
    originalnodes = [r.node for r in remaining]
    originallength = len(originalnodes)

    if not originalnodes:
        return {'originallength': 0, 'newlength': 0, 'detour': 0, 'fare': BASE_FEE}

    currentnode = originalnodes[0]
    endnode = originalnodes[-1]

    path1 = findpath(currentnode, pickupnode) or []
    path2 = findpath(pickupnode, dropoffnode) or []
    path3 = findpath(dropoffnode, endnode) or []

    if not path1 or not path2 or not path3:
        return {'originallength': originallength, 'newlength': originallength, 'detour': 0, 'fare': BASE_FEE}

    newroute = path1[:]
    if path2:
        newroute += path2[1:]
    if path3:
        newroute += path3[1:]

    newlength = len(newroute)
    detour = max(0, newlength - originallength)

    acceptedoffers = CarpoolOffer.objects.filter(
        trip=trip, status='accepted'
    ).select_related('request__pickupnode', 'request__dropoffnode')

    activepassengers = [
        {'pickup': o.request.pickupnode, 'drop': o.request.dropoffnode}
        for o in acceptedoffers
    ]
    activepassengers.append({'pickup': pickupnode, 'drop': dropoffnode})

    faresum = 0.0
    currentpax = 0

    for i in range(len(newroute) - 1):
        node = newroute[i]
        for p in activepassengers:
            if p['pickup'].id == node.id:
                currentpax += 1
        for p in activepassengers:
            if p['drop'].id == node.id:
                currentpax -= 1
        ni = max(1, currentpax)
        faresum += 1.0 / ni

    fare = round(PRICE_PER_HOP * faresum + BASE_FEE, 2)

    return {
        'originallength': originallength,
        'newlength': newlength,
        'detour': detour,
        'fare': fare,
    }
